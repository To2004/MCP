"""Tests for provenance and the freeze manifest (heldout/heldout_provenance.py, EV-02)."""

from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path

import pytest

from mcp_security.behaviour.engine import BehaviourConfig
from reports.experiments.dynamic_dimensions.heldout import heldout_provenance as hp
from reports.experiments.dynamic_dimensions.heldout import heldout_world_spec as ws


@dataclasses.dataclass(frozen=True)
class _Config:
    alpha: float = 0.01
    shares: tuple[float, ...] = (1 / 3, 1 / 3, 1 / 3)


def test_config_digest_is_the_ev02_formula() -> None:
    cfg = _Config()
    literal = hashlib.sha256(
        json.dumps(dataclasses.asdict(cfg), sort_keys=True).encode()
    ).hexdigest()
    assert hp.config_digest(cfg) == literal
    assert hp.config_digest(cfg) == hp.config_digest(_Config())
    assert hp.config_digest(cfg) != hp.config_digest(_Config(alpha=0.025))
    assert hp.config_digest(dataclasses.asdict(cfg)) == literal


def test_engine_configs_have_distinct_stable_digests() -> None:
    v4, v5 = BehaviourConfig(design="v4"), BehaviourConfig(design="v5")
    assert hp.config_digest(v5) == hp.config_digest(BehaviourConfig(design="v5"))
    assert hp.config_digest(v4) != hp.config_digest(v5)
    with pytest.raises(TypeError):
        hp.config_digest(42)


def test_merges_are_refused_unless_only_the_engines_differ() -> None:
    a = {"config_digests": {"v4": "c4"}, "world_digest": "w1", "engines": ["v4"]}
    hp.check_mergeable(a, a | {"engines": ["v4", "v5"], "config_digests": {"v5": "c5"}})
    with pytest.raises(hp.ProvenanceMismatch, match=r"config_digests\[v4\]"):
        hp.check_mergeable(a, a | {"config_digests": {"v4": "other"}})
    with pytest.raises(hp.ProvenanceMismatch, match="seed"):
        hp.check_mergeable(a, a | {"seed": 3})
    with pytest.raises(hp.ProvenanceMismatch, match="world_digest"):
        hp.check_mergeable(a, a | {"world_digest": "w2"})


def test_an_only_run_can_add_an_engine_and_the_merge_keeps_both() -> None:
    # A v4 run, then a v5 --only run that imported one more file: shared files must agree.
    v4 = {
        "git_sha": "g",
        "sha256": {"engine.py": "e1", "world.py": "w1"},
        "imported": ["engine.py", "world.py"],
        "config_digests": {"v4": "c4"},
        "policy_digests": {"v4": "p4"},
        "engines": ["v4"],
        "world_digest": "rows",
    }
    v5 = v4 | {
        "sha256": {"engine.py": "e1", "world.py": "w1", "calibration.py": "k1"},
        "imported": ["calibration.py", "engine.py", "world.py"],
        "config_digests": {"v5": "c5"},
        "policy_digests": {"v5": "p5"},
        "engines": ["v5"],
    }
    merged = hp.merged_provenance(v4, v5)
    assert merged["engines"] == ["v4", "v5"]
    assert merged["config_digests"] == {"v4": "c4", "v5": "c5"}
    assert merged["policy_digests"] == {"v4": "p4", "v5": "p5"}
    assert set(merged["sha256"]) == {"engine.py", "world.py", "calibration.py"}
    assert merged["imported"] == ["calibration.py", "engine.py", "world.py"]
    edited = v5 | {"sha256": {"engine.py": "e2"}}
    with pytest.raises(hp.ProvenanceMismatch, match=r"sha256\[engine.py\]"):
        hp.merged_provenance(v4, edited)
    rerun = v5 | {"config_digests": {"v5": "c5-other"}}
    with pytest.raises(hp.ProvenanceMismatch, match=r"config_digests\[v5\]"):
        hp.check_mergeable(merged, rerun)


def test_code_hashes_and_missing_files(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x = 1\n")
    hashes = hp.code_hashes(["a.py"], root=tmp_path)
    assert hashes == {"a.py": hashlib.sha256(b"x = 1\n").hexdigest()}
    with pytest.raises(FileNotFoundError):
        hp.code_hashes(["missing.py"], root=tmp_path)


def test_imported_files_list_this_harness() -> None:
    files = hp.imported_files()
    assert "reports/experiments/dynamic_dimensions/heldout/heldout_provenance.py" in files
    assert all(not f.startswith("/") for f in files)


def test_the_provenance_block(tmp_path: Path) -> None:
    policy = tmp_path / "policy.json"
    policy.write_text('{"limits": {}}')
    spec = ws.world_spec("W3", ws.TEST, 4, 99)
    v4, v5 = BehaviourConfig(design="v4"), BehaviourConfig(design="v5")
    block = hp.provenance(
        configs={"v5": v5, "v4": v4},
        policies={"v5": policy},
        world_digest="ab" * 32,
        spec=spec,
        files=[Path(hp.__file__)],
    )
    assert block["config_digests"] == {"v4": hp.config_digest(v4), "v5": hp.config_digest(v5)}
    assert block["policy_digests"] == {"v5": hp.file_sha256(policy)}
    assert block["spec"]["family"] == "W3" and block["spec"]["seed"] == 99
    assert block["engines"] == ["v4", "v5"]
    assert {"python", "numpy", "PYTHONHASHSEED", "git_sha", "dirty", "imported"} <= set(block)
    assert len(block["sha256"]) == 1
    with pytest.raises(ValueError, match="without a config"):
        hp.provenance(configs={"v4": v4}, policies={"v5": policy}, files=[])


def test_git_state_outside_a_repository(tmp_path: Path) -> None:
    state = hp.git_state(tmp_path)
    assert state["git_sha"] is None and "git_error" in state


def test_freeze_manifest_digests_files_constants_and_x3(tmp_path: Path) -> None:
    (tmp_path / "engine.py").write_text("A = 1\n")
    (tmp_path / "scenario_01.json").write_text("{}")
    kwargs = {
        "files": ["engine.py"],
        "x1_scenarios": ["scenario_01.json"],
        "x3_log_digests": {"lab_route": "cd" * 32},
        "root": tmp_path,
    }
    constants = {"budget_shares": (1 / 3, 1 / 3, 1 / 3), "surge_min": 5}
    first = hp.freeze_manifest(_Config(), constants, **kwargs)
    assert set(first["sha256"]) == {"engine.py"}
    assert set(first["x1_scenarios"]) == {"scenario_01.json"}
    assert first["constants"]["surge_min"] == 5
    assert (
        hp.freeze_manifest(_Config(), constants, **kwargs)["manifest_digest"]
        == (first["manifest_digest"])
    )
    (tmp_path / "engine.py").write_text("A = 2\n")
    assert (
        hp.freeze_manifest(_Config(), constants, **kwargs)["manifest_digest"]
        != (first["manifest_digest"])
    )


def test_freeze_manifest_digest_leaves_the_runtime_out(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "engine.py").write_text("A = 1\n")
    kwargs = {"files": ["engine.py"], "root": tmp_path}
    first = hp.freeze_manifest(_Config(), {"surge_min": 5}, **kwargs)
    monkeypatch.setattr(
        hp, "runtime", lambda: {"python": "9.9", "numpy": "0.1", "PYTHONHASHSEED": "7"}
    )
    other_machine = hp.freeze_manifest(_Config(), {"surge_min": 5}, **kwargs)
    assert other_machine["runtime"]["python"] == "9.9"  # recorded ...
    assert other_machine["manifest_digest"] == first["manifest_digest"]  # ... not digested


def _fake_repo(root: Path, *, later: bool) -> None:
    named = [*hp.GATEWAY_RUNTIME_FILES, *hp.DEPENDENCY_FILES, *hp.SIMULATOR_FILES]
    named += [*hp.HARNESS_FILES, "src/mcp_security/gateway/oauth.py"]
    if later:
        named += [*hp.LATER_FILES, f"{hp.DD}/catalogs/slack.json"]
    for name in named:
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(name)


def test_freeze_files_needs_every_named_and_later_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        hp.freeze_files(tmp_path)
    _fake_repo(tmp_path, later=False)
    with pytest.raises(FileNotFoundError, match="heldout_run_world.py"):
        hp.freeze_files(tmp_path)
    preview = hp.freeze_files(tmp_path, allow_missing_later=True)
    assert tmp_path / "src/mcp_security/gateway/oauth.py" in preview
    _fake_repo(tmp_path, later=True)
    (tmp_path / "scripts/extra.py").write_text("x = 1\n")
    files = hp.freeze_files(tmp_path, imported=["scripts/extra.py"])
    rel = {str(p.relative_to(tmp_path)) for p in files}
    assert {*hp.LATER_FILES, f"{hp.DD}/catalogs/slack.json", "scripts/extra.py"} <= rel
    with pytest.raises(FileNotFoundError):
        hp.freeze_files(tmp_path, imported=["scripts/missing.py"])


def test_the_freeze_covers_the_modules_that_compute_v5_inputs() -> None:
    files = {str(p.relative_to(hp.REPO)) for p in hp.freeze_files(allow_missing_later=True)}
    for name in (
        "src/mcp_security/behaviour/calibration.py",
        "src/mcp_security/binding/touched_asset.py",
        "src/mcp_security/gateway/oauth.py",
        "src/mcp_security/gateway/wire_log.py",
        "src/mcp_security/gateway/protocol_era.py",
        "src/mcp_security/gateway/config.py",
        "src/mcp_security/gateway/framework.py",
        "uv.lock",
        f"{hp.DD}/heldout/heldout_stats.py",
    ):
        assert name in files, name
