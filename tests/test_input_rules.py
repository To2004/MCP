"""Run-time tool-input rules: each rule kind, absence, lists, and the call max."""

from datetime import datetime, timezone

from mcp_security.input_rules import evaluate_call, evaluate_input, rule_problems, values_at

NOW = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
ASSETS = {"helios-scada-gateway": 5, "helios-public-site": 1}


def _row(path, rule, when_absent=None):
    return {"path": path, "rule": rule, "when_absent": when_absent}


PER_PAGE = _row("per_page", {"kind": "ranges", "measure": "value", "default": 3, "ranges": [
    {"min": None, "max": 30, "level": 2}, {"min": 30, "max": 100, "level": 3},
    {"min": 100, "max": None, "level": 4}]})
REPO = _row("repo", {"kind": "register", "default": 5})
PATH = _row("path", {"kind": "keywords", "default": 3, "groups": [
    {"contains": ["secret", ".env", "id_rsa"], "level": 5},
    {"contains": ["readme", "docs/"], "level": 2}]})


def test_ranges_on_the_number():
    assert evaluate_input(PER_PAGE, {"per_page": 10}).level == 2
    assert evaluate_input(PER_PAGE, {"per_page": 30}).level == 3  # min inclusive
    assert evaluate_input(PER_PAGE, {"per_page": "250"}).level == 4  # numeric text


def test_register_uses_the_scanned_asset_level():
    assert evaluate_input(REPO, {"repo": "helios-scada-gateway"}, assets=ASSETS).level == 5
    assert evaluate_input(REPO, {"repo": "helios-public-site"}, assets=ASSETS).level == 1
    unknown = evaluate_input(REPO, {"repo": "new-prototype"}, assets=ASSETS)
    assert (unknown.level, unknown.unresolved) == (5, True)


def test_keywords_take_the_highest_matching_group():
    assert evaluate_input(PATH, {"path": "config/.ENV"}).level == 5
    assert evaluate_input(PATH, {"path": "README.md"}).level == 2
    assert evaluate_input(PATH, {"path": "src/main.c"}).level == 3


def test_values_and_booleans():
    row = _row("private", {"kind": "values", "default": 3, "values": [
        {"value": True, "level": 3}, {"value": False, "level": 5}]})
    assert evaluate_input(row, {"private": False}).level == 5
    assert evaluate_input(row, {"private": "true"}).level == 3


def test_domain_internal_external_and_unknown():
    row = _row("attendees[].email", {"kind": "domain", "internal": 3, "external": 5})
    args = {"attendees": [{"email": "a@aurora.com"}, {"email": "b@aurora.com"}]}
    assert evaluate_input(row, args, org_domains=("aurora.com",)).level == 3
    args["attendees"].append({"email": "x@gmail.com"})  # one outsider lifts the list
    assert evaluate_input(row, args, org_domains=("aurora.com",)).level == 5
    no_config = evaluate_input(row, args)  # no org domains known: never assume internal
    assert (no_config.level, no_config.unresolved) == (5, True)


def test_time_measures():
    hour = _row("start", {"kind": "ranges", "measure": "hour_of_day", "default": 3, "ranges": [
        {"min": 0, "max": 6, "level": 5}, {"min": 6, "max": 8, "level": 4},
        {"min": 8, "max": 18, "level": 3}, {"min": 18, "max": 24, "level": 4}]})
    assert evaluate_input(hour, {"start": "2026-10-01T03:00:00Z"}).level == 5
    assert evaluate_input(hour, {"start": "2026-10-01T10:30:00+02:00"}).level == 3
    span = _row("timeMin", {"kind": "ranges", "measure": "span_hours", "with": "timeMax",
                            "default": 3, "ranges": [{"min": None, "max": 336, "level": 3},
                                                     {"min": 336, "max": None, "level": 5}]})
    week = {"timeMin": "2026-10-01T00:00:00", "timeMax": "2026-10-08T00:00:00"}
    year = {"timeMin": "2026-01-01T00:00:00Z", "timeMax": "2026-12-31T00:00:00Z"}
    assert evaluate_input(span, week).level == 3
    assert evaluate_input(span, year).level == 5


def test_unreadable_value_falls_to_default_and_is_flagged():
    got = evaluate_input(PER_PAGE, {"per_page": "lots"})
    assert (got.level, got.unresolved) == (3, True)


def test_absence_adds_nothing_unless_the_rule_says_so():
    assert evaluate_input(PER_PAGE, {}).level is None
    unscoped = _row("filter_in_channel", {"kind": "register", "default": 5}, when_absent=5)
    assert evaluate_input(unscoped, {"search_query": "data"}).level == 5


def test_call_level_is_the_max_and_names_the_input():
    args = {"repo": "helios-scada-gateway", "path": "src/main.c", "per_page": 10}
    call = evaluate_call([REPO, PATH, PER_PAGE], args, assets=ASSETS)
    assert (call.level, call.set_by) == (5, ("repo",))
    calm = evaluate_call([REPO, PATH], {"repo": "helios-public-site", "path": "README.md"},
                         assets=ASSETS)
    assert calm.level == 2


def test_rows_without_a_rule_never_raise_the_level():
    dropped = {"path": "page", "important": False}
    assert evaluate_call([dropped, PER_PAGE], {"page": 999, "per_page": 10}).level == 2


def test_values_at_walks_lists_and_accepts_value_or_list():
    args = {"events": [{"start": "a"}, {"start": "b"}], "account": "work"}
    assert values_at(args, "events[].start") == ["a", "b"]
    assert values_at(args, "account[]") == ["work"]
    assert values_at(args, "missing.path") == []


def test_rule_problems_catches_broken_rules():
    paths = {"timeMin", "timeMax"}
    assert rule_problems(PER_PAGE, paths) == []
    bad_order = _row("x", {"kind": "ranges", "measure": "value", "default": 3,
                           "ranges": [{"min": 10, "max": 5, "level": 3}]})
    assert any("not below" in p for p in rule_problems(bad_order, paths))
    assert rule_problems(_row("x", {"kind": "regex"}), paths)
    bad_level = _row("x", {"kind": "values", "default": 7, "values": [{"value": "a", "level": 3}]})
    assert rule_problems(bad_level, paths)
    no_sibling = _row("timeMin", {"kind": "ranges", "measure": "span_hours", "with": "end",
                                  "default": 3, "ranges": [{"min": 0, "max": 1, "level": 3}]})
    assert any("sibling" in p for p in rule_problems(no_sibling, paths))


def test_aliases_resolve_opaque_ids_to_assets():
    chan = _row("channel_id", {"kind": "register", "default": 4})
    assets = {"vireo-unblinding": 5, "vireo-eng-platform": 2}
    aliases = {"C0BLNSWSDGU": "vireo-unblinding"}
    got = evaluate_input(chan, {"channel_id": "C0BLNSWSDGU"}, assets=assets, aliases=aliases)
    assert (got.level, got.matched) == (5, "asset vireo-unblinding")
    assert evaluate_input(chan, {"channel_id": "C0OTHER"}, assets=assets, aliases=aliases).level == 4


def test_register_overrides_raise_an_asset_for_this_tool():
    # the policy forbids writes to the crew roster, whose scanned level is only 3
    row = _row("calendarId", {"kind": "register", "default": 4,
                              "overrides": [{"asset": "aurora-crew-roster", "level": 5}]})
    assets = {"aurora-crew-roster": 3, "aurora-team": 3}
    aliases = {"79001a@group.calendar.google.com": "aurora-crew-roster"}
    got = evaluate_input(row, {"calendarId": "79001a@group.calendar.google.com"},
                         assets=assets, aliases=aliases)
    assert (got.level, got.matched) == (5, "asset aurora-crew-roster (policy override)")
    assert evaluate_input(row, {"calendarId": "aurora-team"}, assets=assets).level == 3


def test_values_rules_see_through_id_aliases():
    row = _row("calendarId", {"kind": "values", "default": 4,
                              "values": [{"value": "aurora-exec", "level": 5}]})
    got = evaluate_input(row, {"calendarId": "7cfd@group.calendar.google.com"},
                         aliases={"7cfd@group.calendar.google.com": "aurora-exec"})
    assert got.level == 5


def test_an_open_top_is_required_for_growing_measures():
    closed = _row("limit", {"kind": "ranges", "measure": "value", "default": 3, "ranges": [
        {"min": None, "max": 50, "level": 3}, {"min": 50, "max": 100, "level": 4}]})
    assert any("open" in p for p in rule_problems(closed, set()))
    hours = _row("start", {"kind": "ranges", "measure": "hour_of_day", "default": 3, "ranges": [
        {"min": 0, "max": 8, "level": 4}, {"min": 8, "max": 24, "level": 3}]})
    assert rule_problems(hours, set()) == []  # a bounded measure needs no open top


# --------------------------------------------------------------------------- v13: all five levels

PEAK_HOURS = _row("start", {"kind": "ranges", "measure": "hour_of_day", "default": 3, "ranges": [
    {"min": 10, "max": 16, "level": 1}, {"min": 8, "max": 10, "level": 2},
    {"min": 16, "max": 18, "level": 2}, {"min": 7, "max": 8, "level": 3},
    {"min": 18, "max": 20, "level": 3}, {"min": 6, "max": 7, "level": 4},
    {"min": 20, "max": 22, "level": 4}, {"min": 0, "max": 6, "level": 5},
    {"min": 22, "max": 24, "level": 5}]})


def test_all_levels_requires_an_entry_for_each_level():
    assert rule_problems(PEAK_HOURS, set(), all_levels=True) == []
    assert rule_problems(PER_PAGE, set()) == []  # off by default: v12 files still load
    missing = rule_problems(PER_PAGE, set(), all_levels=True)
    assert missing and "[1, 5]" in missing[0]


def test_the_default_does_not_count_as_a_level():
    four = _row("q", {"kind": "keywords", "default": 3, "groups": [
        {"contains": ["readme"], "level": 1}, {"contains": ["tmp"], "level": 2},
        {"contains": ["salary"], "level": 4}, {"contains": ["secret"], "level": 5}]})
    assert any("[3]" in p for p in rule_problems(four, set(), all_levels=True))


def test_register_levels_come_from_assets_and_name_words():
    # Helios has assets at 1, 4 and 5; the name words fill 2 and 3
    repo = _row("repo", {"kind": "register", "default": 3, "groups": [
        {"contains": ["docs", "demo"], "level": 2}, {"contains": ["tools"], "level": 3}]})
    assets = {"helios-public-site": 1, "helios-ot-runbooks": 4, "helios-scada-gateway": 5}
    assert rule_problems(repo, set(), all_levels=True, assets=assets) == []
    assert rule_problems(repo, set(), all_levels=True, assets={"helios-public-site": 1})
    assert evaluate_input(repo, {"repo": "helios-scada-gateway"}, assets=assets).level == 5
    named = evaluate_input(repo, {"repo": "team-docs"}, assets=assets)
    assert (named.level, named.matched, named.unresolved) == (2, "name contains docs", False)
    other = evaluate_input(repo, {"repo": "prototype"}, assets=assets)
    assert (other.level, other.unresolved) == (3, True)


def test_peak_working_hours_are_the_safest():
    assert evaluate_input(PEAK_HOURS, {"start": "2026-10-01T11:00:00Z"}).level == 1
    assert evaluate_input(PEAK_HOURS, {"start": "2026-10-01T17:30:00Z"}).level == 2
    assert evaluate_input(PEAK_HOURS, {"start": "2026-10-01T23:00:00Z"}).level == 5


def test_email_ladder_reads_the_policy_lists():
    row = _row("attendees[].email", {"kind": "email"})
    assert rule_problems(row, set(), all_levels=True) == []  # five levels by design
    lists = {"org_domains": ("aurora.com",), "partner_domains": ("caterer.com",),
             "flagged_domains": ("faa.gov",)}

    def level(address):
        return evaluate_input(row, {"attendees": [{"email": address}]}, **lists).level

    assert [level(a) for a in ("a@aurora.com", "b@caterer.com", "not-an-address",
                               "c@acme.com", "e@gmail.com", "d@faa.gov")] == [1, 2, 3, 4, 5, 5]
    no_lists = evaluate_input(row, {"attendees": [{"email": "c@acme.com"}]})
    assert (no_lists.level, no_lists.unresolved) == (4, True)  # never assumed internal
    assert evaluate_input(row, {"attendees": [{"email": "e@gmail.com"}]}).level == 5


def test_name_words_must_agree_with_the_assets_they_are_part_of():
    assets = {"helios-public-site": 1, "helios-ot-runbooks": 4, "helios-scada-gateway": 5}
    wrong = _row("repo", {"kind": "register", "default": 3, "groups": [
        {"contains": ["scada"], "level": 2}, {"contains": ["tools"], "level": 3}]})
    found = rule_problems(wrong, set(), all_levels=True, assets=assets)
    assert len(found) == 1 and "scada" in found[0] and "helios-scada-gateway" in found[0]
    close = _row("repo", {"kind": "register", "default": 3, "groups": [
        {"contains": ["docs"], "level": 2}, {"contains": ["runbooks"], "level": 3}]})
    assert rule_problems(close, set(), all_levels=True, assets=assets) == []  # 3 vs 4 is close
    assert rule_problems(wrong, set(), assets=assets) == []  # v12 shape check only


def test_email_reads_addresses_inside_attendee_records():
    row = _row("attendees", {"kind": "email"})
    args = {"attendees": [{"email": "a@aurora.com"}, {"email": "x@gmail.com"}]}
    assert evaluate_input(row, args, org_domains=("aurora.com",)).level == 5


def test_clashing_name_words_are_dropped_as_a_repair():
    from mcp_security.input_rules import drop_clashing_name_words

    assets = {"vireo-unblinding": 5, "vireo-announcements": 1, "vireo-eng-platform": 3}
    rule = {"kind": "register", "default": 3, "groups": [
        {"contains": ["unblinding", "general"], "level": 2},  # unblinding clashes with 5
        {"contains": ["announcements"], "level": 1},  # agrees with its asset
        {"contains": ["eng"], "level": 5}]}  # clashes with 3, group left empty
    cleaned = drop_clashing_name_words(rule, assets)
    assert cleaned["groups"] == [{"contains": ["general"], "level": 2},
                                 {"contains": ["announcements"], "level": 1}]
    assert drop_clashing_name_words(PER_PAGE["rule"], assets) is PER_PAGE["rule"]


def test_v13_default_is_ordinary():
    high = _row("start", {**PEAK_HOURS["rule"], "default": 4})
    assert any("ordinary" in p for p in rule_problems(high, set(), all_levels=True))
    assert rule_problems(high, set()) == []  # v12 rules with default 4 still load


def test_query_words_are_not_checked_against_asset_names():
    from mcp_security.input_rules import drop_clashing_name_words

    # config in a file path is not the grid-infra-config repository
    path = {"kind": "keywords", "default": 3, "groups": [{"contains": ["config"], "level": 2}]}
    assert drop_clashing_name_words(path, {"helios-grid-infra-config": 4}) == path


def test_only_reachable_entries_fill_a_level():
    from mcp_security.input_rules import levels_covered

    fake = {"kind": "ranges", "measure": "span_hours", "with": "b", "default": 3, "ranges": [
        {"min": None, "max": 24, "level": 1}, {"min": 24, "max": 168, "level": 2},
        {"min": 168, "max": 720, "level": 3}, {"min": 720, "max": None, "level": 4},
        {"min": None, "max": None, "level": 5}]}  # never reached: everything matched above
    assert levels_covered(fake) == {1, 2, 3, 4}
    assert levels_covered(PEAK_HOURS["rule"]) == {1, 2, 3, 4, 5}  # split ranges still count
    twice = {"kind": "values", "default": 3, "values": [
        {"value": "a", "level": 1}, {"value": "A", "level": 5}]}  # the second a is never used
    assert levels_covered(twice) == {1}


def test_fragments_match_at_word_starts_only():
    from mcp_security.input_rules import fragment_in
    assert fragment_in("site", "site-a status") and fragment_in("unblind", "unblinding")
    assert not fragment_in("site", "website") and fragment_in(".env", "deploy/.env")
    assert fragment_in(".pem", "private_key.pem")


def test_a_credential_shaped_path_scores_5_whatever_the_rule():
    from mcp_security.input_rules import credential_path
    row = {"path": "path", "rule": {"kind": "register", "groups": [], "default": 3}}
    assert evaluate_input(row, {"path": "app/.env"}).level == 5
    assert evaluate_input(row, {"path": "docs/readme.md"}).level == 3
    assert credential_path("token-service") is None  # a bare name is not a path


def test_one_end_of_a_window_reads_up_to_now():
    from datetime import datetime, timezone
    rule = {"kind": "ranges", "measure": "span_hours", "with": "before", "default": 3, "ranges": [
        {"min": None, "max": 24, "level": 1}, {"min": 24, "max": 168, "level": 2},
        {"min": 168, "max": 720, "level": 3}, {"min": 720, "max": 8760, "level": 4},
        {"min": 8760, "max": None, "level": 5}]}
    now = datetime(2026, 10, 15, tzinfo=timezone.utc)
    got = evaluate_input({"path": "after", "rule": rule}, {"after": "2015-01-01T00:00:00Z"}, now=now)
    assert got.level == 5


def test_a_left_out_input_is_rated_at_its_schema_default():
    rule = {"kind": "ranges", "measure": "value", "default": 3, "ranges": [
        {"min": None, "max": 10, "level": 1}, {"min": 10, "max": 50, "level": 2},
        {"min": 50, "max": None, "level": 5}]}
    row = {"path": "limit", "rule": rule, "schema_default": 20}
    assert evaluate_input(row, {}).level == 2
    assert evaluate_input({**row, "when_absent": 4}, {}).level == 4


def test_a_left_out_input_rated_at_the_server_default_is_at_most_ordinary():
    rule = {"kind": "ranges", "measure": "value", "default": 3, "ranges": [
        {"min": None, "max": 10, "level": 1}, {"min": 10, "max": 50, "level": 2},
        {"min": 50, "max": 100, "level": 3}, {"min": 100, "max": 500, "level": 4},
        {"min": 500, "max": None, "level": 5}]}
    row = {"path": "limit", "rule": rule, "schema_default": 100}
    assert evaluate_input(row, {}).level == 3
    assert evaluate_input(row, {"limit": 100}).level == 4
    assert evaluate_input({**row, "when_absent": 4}, {}).level == 4
