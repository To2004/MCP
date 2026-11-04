"""AI-1, AI-2, AI-12, AI-13 (exact dict and unique match), EXP-1: the touched asset.

The register is the simulated Helios Grid GitHub route's
(``reports/experiments/gateway/github_remote``); the smaller registers are invented.
"""

from __future__ import annotations

import dataclasses
import json
import time
from pathlib import Path

import pytest

from mcp_security.behaviour import engine
from mcp_security.behaviour.engine import Message
from mcp_security.binding import touched_asset as ta
from mcp_security.binding.scoring import MatrixScorer, parse_tool_targets
from mcp_security.binding.touched_asset import (
    AMBIGUOUS,
    EXACT,
    NAMED,
    NO_TARGET,
    PUBLIC,
    UNIQUE,
    UNREGISTERED,
    AssetRegister,
    Container,
    ContainerValue,
    Touched,
    TouchedAssetLookup,
    named_containers,
)
from mcp_security.gateway.pseudonym import Pseudonymizer
from mcp_security.static_scoring.server_policies import PolicyAssetRow, parse_asset_register

REPO = Path(__file__).resolve().parents[2]
ROUTE = REPO / "reports" / "experiments" / "gateway" / "github_remote"
SCAN = ROUTE / "github_remote.cells.json"
REGISTER = ROUTE / "github_helios_remote.md"
CLASSIFICATION_END = "## Input policy"  # the file's second register is the input policy's
KEY = b"test-only-key"
PSEUDONYMS = Pseudonymizer(KEY)
OWNER, FOREIGN = "helios", "outside-org"
SCADA, PUBLIC_SITE = "helios-scada-gateway", "helios-public-site"
#: The route's standing containers, as a scan's ``asset_containers`` would declare them.
REPOSITORIES = (
    SCADA,
    PUBLIC_SITE,
    "helios-grid-infra-config",
    "helios-market-bidding-engine",
    "helios-ot-runbooks",
)
#: The deployment's registered repositories; their owner, helios, becomes a known owner.
REGISTERED = {f"{OWNER}/website": PUBLIC}
TARGETS = {
    "get_file_contents": ["owner", "repo"],
    "issue_read": ["owner", "repo"],
    "issue_write": ["owner", "repo"],
    "list_commits": ["owner", "repo"],
    # the destination is the repository GitHub creates, organization/repo
    "fork_repository": [
        ["owner", "repo"],
        {"inputs": ["organization", "repo"], "owner": "organization"},
    ],
}
LARGE_REGISTER = 100_000
#: Mean time one exact hit may take in the large register: about 50 times the synthetic
#: development timing (about 20 us), so only a lookup that is no longer O(1) fails.
EXACT_HIT_BUDGET_S = 1e-3
EXACT_HITS_TIMED = 1_000


@pytest.fixture(scope="module")
def scan() -> dict:
    return json.loads(SCAN.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def rows() -> list[PolicyAssetRow]:
    return parse_asset_register(REGISTER.read_text(encoding="utf-8").split(CLASSIFICATION_END)[0])


@pytest.fixture(scope="module")
def register(scan: dict, rows: list[PolicyAssetRow]) -> AssetRegister:
    """The register as the policy rows give it today: containers inferred, owner helios."""
    return AssetRegister.from_rows(rows, scan["asset_sensitivity"], repositories=REGISTERED)


@pytest.fixture(scope="module")
def lookup(register: AssetRegister) -> TouchedAssetLookup:
    return TouchedAssetLookup(register, TARGETS, PSEUDONYMS)


@pytest.fixture(scope="module")
def declared(scan: dict, rows: list[PolicyAssetRow]) -> TouchedAssetLookup:
    """The same route once the scan declares its containers (``asset_containers``)."""
    register = AssetRegister.from_scan(
        {**scan, "asset_containers": list(REPOSITORIES)}, REGISTERED, rows=rows
    )
    return TouchedAssetLookup(register, TARGETS, PSEUDONYMS)


@pytest.fixture(scope="module")
def ownerless(scan: dict, rows: list[PolicyAssetRow]) -> TouchedAssetLookup:
    """The route without registered repositories or owners: names count under any owner."""
    register = AssetRegister.from_rows(rows, scan["asset_sensitivity"])
    return TouchedAssetLookup(register, TARGETS, PSEUDONYMS)


def handle(prefix: str, value: str, key: bytes | None = KEY) -> str:
    return prefix + Pseudonymizer(key).of(value)[: ta.HANDLE_CHARS]


# ── AI-1, AI-2: named, unregistered, none ───────────────────────────────────────────────


def test_a_registered_repository_is_named_with_its_sensitivity_and_exposure(
    lookup: TouchedAssetLookup,
) -> None:
    touched = lookup.touched("get_file_contents", {"owner": OWNER, "repo": PUBLIC_SITE})
    assert (touched.asset, touched.sensitivity, touched.exposure) == (PUBLIC_SITE, 1, PUBLIC)
    assert touched.basis == NAMED and touched.primary.match == EXACT and touched.floor_eligible


def test_the_lookup_runs_over_every_register_id_not_the_tools_candidates(
    scan: dict, lookup: TouchedAssetLookup
) -> None:
    """AI-4 item 11: issue_read has no cell against the public site, yet it names it."""
    assert PUBLIC_SITE not in MatrixScorer(scan["cells"], scan["bands"]).candidates("issue_read")
    touched = lookup.touched("issue_read", {"owner": OWNER, "repo": PUBLIC_SITE, "method": "get"})
    assert touched.asset == PUBLIC_SITE


def test_an_unregistered_repository_is_a_keyed_pseudonym_without_sensitivity(
    lookup: TouchedAssetLookup,
) -> None:
    touched = lookup.touched("get_file_contents", {"owner": OWNER, "repo": "Website"})
    assert touched.asset == handle(ta.CONTAINER_PREFIX, f"{OWNER}/website")
    assert touched.basis == UNREGISTERED and touched.sensitivity is None
    assert not touched.floor_eligible
    # the registered-repositories list gives an unregistered container its exposure (EXP-1)
    assert touched.exposure == PUBLIC


def test_the_pseudonym_depends_on_the_key_and_on_the_owner(register: AssetRegister) -> None:
    args = {"owner": OWNER, "repo": "website"}
    keyed = TouchedAssetLookup(register, TARGETS, PSEUDONYMS)
    other_key = TouchedAssetLookup(register, TARGETS, Pseudonymizer(b"another-key"))
    unkeyed = TouchedAssetLookup(register, TARGETS, Pseudonymizer(None))
    assert keyed.touched("get_file_contents", args) == keyed.touched("issue_read", args)
    assert (
        keyed.touched("get_file_contents", args).asset
        != other_key.touched("get_file_contents", args).asset
    )
    assert unkeyed.touched("get_file_contents", args).asset == handle(
        ta.CONTAINER_PREFIX, f"{OWNER}/website", key=None
    )
    elsewhere = keyed.touched("get_file_contents", {"owner": FOREIGN, "repo": "website"})
    assert elsewhere.asset != keyed.touched("get_file_contents", args).asset


def test_the_pseudonyms_are_required_and_say_whether_they_are_keyed(
    register: AssetRegister,
) -> None:
    with pytest.raises(TypeError):
        TouchedAssetLookup(register, TARGETS)  # type: ignore[call-arg]
    assert TouchedAssetLookup(register, TARGETS, PSEUDONYMS).keyed
    assert not TouchedAssetLookup(register, TARGETS, Pseudonymizer(None)).keyed


@pytest.mark.parametrize(
    ("tool", "args"),
    [
        ("search_code", {"query": f"repo:{OWNER}/{SCADA}"}),  # no target input
        ("get_file_contents", {"repo": SCADA}),  # one of the container's inputs missing
        ("get_file_contents", {"owner": OWNER, "repo": "  "}),  # empty value
        ("get_file_contents", "not-an-object"),
    ],
)
def test_no_target_value_gives_no_touched_asset(
    lookup: TouchedAssetLookup, tool: str, args: object
) -> None:
    touched = lookup.touched(tool, args)
    assert touched == Touched() and touched.basis == NO_TARGET
    assert touched.message_fields() == {
        "asset": None,
        "sensitivity": None,
        "exposure": None,
        "owner": None,
        "more_assets": (),
    }


def test_without_tool_targets_no_call_has_a_touched_asset(register: AssetRegister) -> None:
    lookup = TouchedAssetLookup(register, None, PSEUDONYMS)
    assert lookup.touched("get_file_contents", {"owner": OWNER, "repo": SCADA}) == Touched()


# ── AI-3: decoys ────────────────────────────────────────────────────────────────────────


def test_a_decoy_path_or_body_cannot_name_another_asset(lookup: TouchedAssetLookup) -> None:
    website = handle(ta.CONTAINER_PREFIX, f"{OWNER}/website")
    read = lookup.touched(
        "get_file_contents", {"owner": OWNER, "repo": "website", "path": f"docs/{SCADA}.md"}
    )
    write = lookup.touched(
        "issue_write",
        {
            "owner": OWNER,
            "repo": "website",
            "method": "create",
            "title": SCADA,
            "body": f"copied from {SCADA}",
        },
    )
    assert read.asset == write.asset == website
    assert read.sensitivity is None and write.sensitivity is None


# ── EXP-1: owners ───────────────────────────────────────────────────────────────────────


def test_an_owner_never_names_a_register_asset() -> None:
    """The exact pass tries tails only, and the name pass drops an id the owner covers
    unless the container's own name covers it too."""
    register = AssetRegister({"team": 5, "website": 2, "b": 4})
    lookup = TouchedAssetLookup(register, {"read": ["owner", "repo"]}, PSEUDONYMS)
    assert lookup.touched("read", {"owner": "team", "repo": "docs"}).basis == UNREGISTERED
    assert lookup.touched("read", {"owner": "team", "repo": "website"}).asset == "website"
    assert lookup.match("b/ab", owner="b") == (None, ())  # 'b' is a head, not a tail segment
    # an owner-prefixed register id is still found: the owner only adds to the repo's words
    prefixed = TouchedAssetLookup(
        AssetRegister({"acme-billing-api": 4}), {"read": ["o", "r"]}, PSEUDONYMS
    )
    assert prefixed.touched("read", {"o": "acme", "r": "billing-api"}).primary.match == UNIQUE
    # one repository name resolves the same way whichever owner it lives under
    payments = TouchedAssetLookup(
        AssetRegister({"payments": 5}), {"read": ["owner", "repo"]}, PSEUDONYMS
    )
    for org in ("acme", "payments"):
        touched = payments.touched("read", {"owner": org, "repo": "payments-v2"})
        assert (touched.asset, touched.sensitivity, touched.primary.match) == (
            "payments",
            5,
            UNIQUE,
        ), org
    # a container that is only an owner (a destination organisation) names nothing
    org_only = TouchedAssetLookup(
        register, {"fork": [{"inputs": ["org"], "owner": "org"}]}, PSEUDONYMS
    )
    assert org_only.touched("fork", {"org": "team"}).basis == UNREGISTERED


def test_a_registered_name_under_another_owner_is_someone_elses_container(
    lookup: TouchedAssetLookup,
) -> None:
    """A mirror or fork of a registered repository under another owner is not the asset:
    it has no sensitivity, so its first read cannot spend the alert-floor budget."""
    home = lookup.touched("get_file_contents", {"owner": "Helios", "repo": SCADA})
    assert (home.asset, home.sensitivity, home.primary.match) == (SCADA, 5, EXACT)
    mirror = lookup.touched("get_file_contents", {"owner": "evil-corp", "repo": SCADA})
    assert mirror.asset == handle(ta.CONTAINER_PREFIX, f"evil-corp/{SCADA}")
    assert (mirror.basis, mirror.sensitivity, mirror.primary.candidates) == (
        UNREGISTERED,
        None,
        (),
    )
    assert not mirror.floor_eligible and mirror.owner == handle(ta.OWNER_PREFIX, "evil-corp")


def test_the_owners_come_from_the_register_and_the_registered_repositories() -> None:
    register = AssetRegister(
        {"payments": 5}, repositories={"Partner/Shared": ta.INTERNAL}, owners=frozenset({"ACME"})
    )
    assert register.owners == {"acme", "partner"}
    lookup = TouchedAssetLookup(register, {"read": ["owner", "repo"]}, PSEUDONYMS)
    for owner, basis in (("acme", NAMED), ("partner", NAMED), ("rival", UNREGISTERED)):
        assert lookup.touched("read", {"owner": owner, "repo": "payments"}).basis == basis, owner
    # a single-input container has no owner to check, so a register name still names it
    single = TouchedAssetLookup(register, {"read": ["repository"]}, PSEUDONYMS)
    assert single.touched("read", {"repository": "rival/payments"}).asset == "payments"


def test_without_known_owners_a_register_name_names_its_asset_under_any_owner(
    ownerless: TouchedAssetLookup,
) -> None:
    """Pinned limitation: with no owners configured the lookup cannot tell a mirror from
    the asset, so a deployment sets ``owners`` or registers its repositories."""
    assert not ownerless.register.owners
    mirror = ownerless.touched("get_file_contents", {"owner": "evil-corp", "repo": SCADA})
    assert (mirror.asset, mirror.sensitivity, mirror.primary.match) == (SCADA, 5, EXACT)


# ── AI-13: exact dict, unique match, ambiguity, inferred containers ─────────────────────


AMBIGUOUS_REGISTER = {"ops-runbooks": 5, "ops-runbooks-archive": 4, "billing-api": 3}


def test_ambiguity_gives_no_sensitivity_and_so_no_floor() -> None:
    lookup = TouchedAssetLookup(
        AssetRegister(AMBIGUOUS_REGISTER), {"read": ["owner", "repo"]}, PSEUDONYMS
    )
    touched = lookup.touched("read", {"owner": "acme", "repo": "ops-runbooks-archive-copy"})
    assert touched.basis == AMBIGUOUS
    assert touched.primary.candidates == ("ops-runbooks", "ops-runbooks-archive")
    assert touched.sensitivity is None and not touched.floor_eligible
    assert touched.asset == handle(ta.CONTAINER_PREFIX, "acme/ops-runbooks-archive-copy")


def test_an_exact_id_wins_over_several_name_matches() -> None:
    lookup = TouchedAssetLookup(
        AssetRegister(AMBIGUOUS_REGISTER), {"read": ["owner", "repo"]}, PSEUDONYMS
    )
    touched = lookup.touched("read", {"owner": "acme", "repo": "ops-runbooks-archive"})
    assert (touched.asset, touched.sensitivity, touched.primary.match) == (
        "ops-runbooks-archive",
        4,
        EXACT,
    )


def test_a_unique_name_match_against_declared_containers_may_fire_a_floor(
    declared: TouchedAssetLookup,
) -> None:
    touched = declared.touched("get_file_contents", {"owner": OWNER, "repo": f"{SCADA}-fork"})
    assert (touched.asset, touched.sensitivity, touched.primary.match) == (SCADA, 5, UNIQUE)
    assert touched.floor_eligible


def test_a_name_match_against_inferred_containers_names_no_asset(
    lookup: TouchedAssetLookup, declared: TouchedAssetLookup
) -> None:
    """The policy rows mix repositories with data classes, so a name that only resembles a
    row (``branch-head-tools`` and the ``branch-heads`` class) gets a pseudonym, and the
    row it resembled is kept for audit. Only an exact id names an inferred container."""
    assert lookup.register.containers_inferred and not declared.register.containers_inferred
    for repo, resembled in ((f"{SCADA}-fork", SCADA), ("branch-head-tools", "branch-heads")):
        touched = lookup.touched("get_file_contents", {"owner": OWNER, "repo": repo})
        assert touched.asset == handle(ta.CONTAINER_PREFIX, f"{OWNER}/{repo}"), repo
        assert (touched.basis, touched.sensitivity) == (UNREGISTERED, None), repo
        assert touched.primary.candidates == (resembled,) and not touched.floor_eligible
    # declared containers hold no data class, so the tool repository resembles nothing
    tools = declared.touched("get_file_contents", {"owner": OWNER, "repo": "branch-head-tools"})
    assert (tools.basis, tools.primary.candidates) == (UNREGISTERED, ())


def test_two_ids_with_one_canonical_form_are_ambiguous() -> None:
    lookup = TouchedAssetLookup(
        AssetRegister({"Payroll": 5, "payroll": 4}), {"read": ["path"]}, PSEUDONYMS
    )
    touched = lookup.touched("read", {"path": "PAYROLL"})
    assert touched.basis == AMBIGUOUS and touched.sensitivity is None


def test_a_large_register_finds_exact_ids_in_constant_time_and_keeps_ambiguity() -> None:
    """AI-13 at 10^5 ids: the exact dict. The name pass has no time bound until the
    deferred token index exists, so only exact hits are timed here."""
    ids = {f"svc-{i:06d}-data": 1 + i % 5 for i in range(LARGE_REGISTER)}
    lookup = TouchedAssetLookup(
        AssetRegister({**ids, "Svc-004242-Data": 5}), {"read": ["owner", "repo"]}, PSEUDONYMS
    )
    for i in (0, 4_241, LARGE_REGISTER - 1):
        touched = lookup.touched("read", {"owner": "acme", "repo": f"svc-{i:06d}-data"})
        assert (touched.asset, touched.primary.match) == (f"svc-{i:06d}-data", EXACT)
    clash = lookup.touched("read", {"owner": "acme", "repo": "SVC-004242-data"})
    assert clash.basis == AMBIGUOUS and clash.sensitivity is None
    assert clash.primary.candidates == ("Svc-004242-Data", "svc-004242-data")
    step = LARGE_REGISTER // EXACT_HITS_TIMED
    start = time.perf_counter()
    for i in range(0, LARGE_REGISTER, step):
        lookup.touched("read", {"owner": "acme", "repo": f"svc-{i:06d}-data"})
    assert (time.perf_counter() - start) / EXACT_HITS_TIMED < EXACT_HIT_BUDGET_S


def test_the_register_rows_that_describe_a_call_target_are_not_containers(
    scan: dict, rows: list[PolicyAssetRow], register: AssetRegister
) -> None:
    assert "repository-contents" not in register.containers  # "What a file read ... reaches"
    assert {SCADA, PUBLIC_SITE} <= register.containers
    # from the scan alone every id is a container, so give the rows when the scan lacks
    # asset_containers: an exact hit on a call-target row is otherwise named
    bare = AssetRegister.from_scan(scan)
    assert bare.containers == set(scan["asset_sensitivity"]) and bare.containers_inferred
    by_rows = AssetRegister.from_scan(scan, rows=rows)
    assert by_rows.containers == register.containers and by_rows.containers_inferred
    assert by_rows.exposure[PUBLIC_SITE] == PUBLIC  # the row's public flag (EXP-1)
    args = {"owner": OWNER, "repo": "repository-contents"}
    from_bare = TouchedAssetLookup(bare, TARGETS, PSEUDONYMS).touched("get_file_contents", args)
    assert from_bare.primary.match == EXACT
    from_rows = TouchedAssetLookup(by_rows, TARGETS, PSEUDONYMS).touched("get_file_contents", args)
    assert from_rows.basis == UNREGISTERED


def test_a_path_reaches_a_registered_folder_by_name_never_by_a_leading_segment() -> None:
    """Hierarchy containers are out of scope for the exact pass: a leading segment can be
    an owner inside a qualified value, so it is never tried as an exact id."""
    folder = TouchedAssetLookup(AssetRegister({"payroll": 5}), {"read": ["path"]}, PSEUDONYMS)
    touched = folder.touched("read", {"path": "/hr/payroll/2024.csv"})
    assert (touched.asset, touched.primary.match) == ("payroll", UNIQUE)
    qualified = TouchedAssetLookup(
        AssetRegister({"payments": 5, "website": 2}), {"read": ["repository"]}, PSEUDONYMS
    )
    assert qualified.match("payments/website") == (EXACT, ("website",))  # the tail
    assert qualified.match("payments/blog") == (UNIQUE, ("payments",))  # by name, not exact


# ── AI-12: several containers per call ──────────────────────────────────────────────────


def test_a_fork_out_of_the_organisation_names_two_containers_under_two_owners(
    lookup: TouchedAssetLookup,
) -> None:
    touched = lookup.touched(
        "fork_repository", {"owner": OWNER, "repo": SCADA, "organization": FOREIGN}
    )
    assert (touched.asset, touched.sensitivity) == (SCADA, 5)
    destination = handle(ta.CONTAINER_PREFIX, f"{FOREIGN}/{SCADA}")
    assert touched.more_assets == (destination,)  # Breadth counts 2
    assert touched.owner == handle(ta.OWNER_PREFIX, OWNER)
    assert touched.containers[1].owner == handle(ta.OWNER_PREFIX, FOREIGN)
    assert touched.containers[1].basis == UNREGISTERED


def test_without_known_owners_a_fork_destination_folds_into_its_source(
    ownerless: TouchedAssetLookup,
) -> None:
    """Pinned limitation: both containers are named as the register asset, so the
    destination adds nothing to Breadth; known owners fix it (the test above)."""
    touched = ownerless.touched(
        "fork_repository", {"owner": OWNER, "repo": SCADA, "organization": FOREIGN}
    )
    assert [c.asset for c in touched.containers] == [SCADA, SCADA]
    assert touched.more_assets == ()


def test_a_fork_into_its_own_organisation_names_one_container(
    lookup: TouchedAssetLookup,
) -> None:
    touched = lookup.touched(
        "fork_repository", {"owner": OWNER, "repo": SCADA, "organization": OWNER}
    )
    assert len(touched.containers) == 1 and touched.more_assets == ()


def test_a_list_valued_target_names_one_container_per_item_most_sensitive_first(
    lookup: TouchedAssetLookup,
) -> None:
    touched = lookup.touched(
        "list_commits", {"owner": OWNER, "repo": [PUBLIC_SITE, SCADA, PUBLIC_SITE]}
    )
    assert touched.asset == SCADA  # the most sensitive is the primary
    assert touched.more_assets == (PUBLIC_SITE,)  # a repeated container counts once
    assert len({touched.asset, *touched.more_assets}) == 2


def test_more_assets_counts_each_other_asset_once_and_never_the_primarys(
    declared: TouchedAssetLookup,
) -> None:
    """Two spellings of one asset are two container values but one asset."""
    touched = declared.touched(
        "list_commits",
        {"owner": OWNER, "repo": [SCADA, "scada-gateway", PUBLIC_SITE, "public-site"]},
    )
    assert [(c.asset, c.match) for c in touched.containers] == [
        (SCADA, EXACT),
        (SCADA, UNIQUE),
        (PUBLIC_SITE, EXACT),
        (PUBLIC_SITE, UNIQUE),
    ]
    assert touched.more_assets == (PUBLIC_SITE,)
    pair = declared.touched("list_commits", {"owner": OWNER, "repo": ["scada-gateway", SCADA]})
    assert len(pair.containers) == 2 and pair.more_assets == ()


def test_on_a_sensitivity_tie_the_first_named_container_is_the_primary(
    lookup: TouchedAssetLookup,
) -> None:
    unregistered = lookup.touched("list_commits", {"owner": OWNER, "repo": ["beta", "alpha"]})
    assert unregistered.asset == handle(ta.CONTAINER_PREFIX, f"{OWNER}/beta")
    runbooks, infra = "helios-ot-runbooks", "helios-grid-infra-config"  # both sensitivity 4
    for repos in ([runbooks, infra], [infra, runbooks]):
        touched = lookup.touched("list_commits", {"owner": OWNER, "repo": repos})
        assert (touched.asset, touched.more_assets) == (repos[0], (repos[1],))


def test_the_containers_per_call_are_bounded(lookup: TouchedAssetLookup) -> None:
    cap = ta.MAX_CONTAINERS_PER_CALL
    repos = [f"team-repo-{i}" for i in range(cap * 3)]
    one_list = lookup.touched("list_commits", {"owner": OWNER, "repo": repos})
    assert len(one_list.containers) == cap
    # two list inputs: each column is within its cap, so only the per-call cap stops them
    owners = [OWNER, "second-org", "third-org"]
    two_lists = lookup.touched("list_commits", {"owner": owners, "repo": repos[:cap]})
    assert len(two_lists.containers) == cap
    assert {c.owner for c in two_lists.containers} == {handle(ta.OWNER_PREFIX, OWNER)}


def test_only_the_first_items_of_a_list_value_are_read(lookup: TouchedAssetLookup) -> None:
    """A cost bound (DEP-7): an item past the first MAX_CONTAINERS_PER_CALL names nothing."""
    repos = ["same-repo"] * ta.MAX_CONTAINERS_PER_CALL + ["late-repo"]
    touched = lookup.touched("list_commits", {"owner": OWNER, "repo": repos})
    assert [c.asset for c in touched.containers] == [
        handle(ta.CONTAINER_PREFIX, f"{OWNER}/same-repo")
    ]


def test_named_containers_canonicalises_and_reads_owners() -> None:
    spec = parse_tool_targets({"t": [{"inputs": ["org", "name"], "owner": "org"}]})["t"]
    found = named_containers(spec, {"org": " Helios ", "name": ["Web", 42, True, None, ""]})
    assert found == [
        ContainerValue("helios/web", "helios", "web"),
        ContainerValue("helios/42", "helios", "42"),
    ]
    last = parse_tool_targets({"t": [{"inputs": ["name", "org"], "owner": "org"}]})["t"]
    assert named_containers(last, {"org": "helios", "name": "web"}) == [
        ContainerValue("web/helios", "helios", "web")
    ]
    single = parse_tool_targets({"t": ["channel"]})["t"]
    assert named_containers(single, {"channel": "#General"}) == [
        ContainerValue("general", None, "general")
    ]


# ── EXP-1: exposure and the register's construction ────────────────────────────────────


def test_register_exposure_comes_before_the_repository_list() -> None:
    register = AssetRegister(
        {"site": 1},
        exposure={"site": ta.PRIVATE},
        repositories={"acme/site": PUBLIC, "Acme/Blog": ta.INTERNAL},
    )
    lookup = TouchedAssetLookup(register, {"read": ["owner", "repo"]}, PSEUDONYMS)
    assert lookup.touched("read", {"owner": "acme", "repo": "site"}).exposure == ta.PRIVATE
    assert lookup.touched("read", {"owner": "acme", "repo": "blog"}).exposure == ta.INTERNAL
    assert lookup.touched("read", {"owner": "acme", "repo": "other"}).exposure is None


def test_a_single_input_container_has_no_owner() -> None:
    lookup = TouchedAssetLookup(AssetRegister({"general": 2}), {"post": ["channel"]}, PSEUDONYMS)
    touched = lookup.touched("post", {"channel": "#general"})
    assert (touched.asset, touched.owner) == ("general", None)


def test_from_scan_reads_the_optional_exposure_and_container_fields() -> None:
    scan = {
        "asset_sensitivity": {"a": 5, "b": 1, "rows": 3},
        "asset_exposure": {"b": PUBLIC},
        "asset_containers": ["a", "b"],
    }
    register = AssetRegister.from_scan(scan, owners=["Acme"])
    assert register.containers == {"a", "b"} and register.exposure["b"] == PUBLIC
    assert not register.containers_inferred and register.owners == {"acme"}
    fallback = AssetRegister.from_scan({"asset_sensitivity": {"a": 2}})
    assert fallback.containers == {"a"} and fallback.containers_inferred
    assert not AssetRegister({"a": 2}).containers_inferred  # a caller's register is declared


@pytest.mark.parametrize(
    "kwargs",
    [
        {"sensitivity": {"a": 6}},
        {"sensitivity": {"a": 0}},
        {"sensitivity": {"a": 2.5}},
        {"sensitivity": {"a": True}},
        {"sensitivity": {"a": 2}, "exposure": {"a": "secret"}},
        {"sensitivity": {"a": 2}, "repositories": {"x/y": "open"}},
        {"sensitivity": {"a": 2}, "containers": frozenset({"b"})},
        {"sensitivity": {"a": 2}, "owners": "acme"},
        {"sensitivity": {"a": 2}, "owners": frozenset({" / "})},
        {"sensitivity": {"a": 2}, "owners": frozenset({3})},
    ],
)
def test_a_malformed_register_fails_at_construction(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        AssetRegister(**kwargs)


def test_the_register_is_read_only(register: AssetRegister) -> None:
    with pytest.raises(TypeError):
        register.sensitivity[SCADA] = 1  # type: ignore[index]


# ── what reaches the engine ─────────────────────────────────────────────────────────────


def test_message_fields_build_an_engine_message(lookup: TouchedAssetLookup) -> None:
    touched = lookup.touched(
        "fork_repository", {"owner": OWNER, "repo": SCADA, "organization": FOREIGN}
    )
    message = Message(
        0.0, "agent", "tools/call", tool="fork_repository", **touched.message_fields()
    )
    assert (message.asset, message.sensitivity, message.owner, message.more_assets) == (
        SCADA,
        5,
        touched.owner,
        touched.more_assets,
    )


def test_the_value_constants_equal_the_engines() -> None:
    assert (ta.PUBLIC, ta.INTERNAL, ta.PRIVATE) == (engine.PUBLIC, engine.INTERNAL, engine.PRIVATE)
    assert (ta.READ, ta.WRITE) == (engine.READ, engine.WRITE)


def test_no_raw_unregistered_name_reaches_the_result(lookup: TouchedAssetLookup) -> None:
    """AI-4 item 9's precondition: what the engine stores carries no unregistered name."""
    touched = lookup.touched(
        "fork_repository",
        {"owner": "acme-skunkworks", "repo": "secret-merger-plan", "organization": "rival-corp"},
    )
    assert len(touched.containers) == 2
    dumped = json.dumps(dataclasses.asdict(touched))
    for raw in ("acme", "skunkworks", "secret-merger-plan", "rival-corp"):
        assert raw not in dumped


def test_named_ids_stay_readable_and_containers_are_frozen() -> None:
    container = Container("x", NAMED, 3)
    with pytest.raises(dataclasses.FrozenInstanceError):
        container.asset = "y"  # type: ignore[misc]
    assert Touched.from_containers([]) == Touched()
