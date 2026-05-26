"""
Consolidate the 3 new demo filesystems and their simulation logs into the main repo.

- Copies demo/medical_clinic_fs, law_firm_fs, media_studio_fs -> main repo demo/
- Merges 15 per-run logs per app into one combined output in logs/proxy/sessions/
"""

import csv
import json
import shutil
from pathlib import Path

WORKTREE = Path(__file__).resolve().parent.parent.parent.parent / ".worktrees/demo-filesystems"
MAIN_REPO = Path(__file__).resolve().parent.parent.parent.parent

APPS = [
    ("medical_clinic_fs", "medical_clinic_fs_sim", "medical_clinic_sim"),
    ("law_firm_fs", "law_firm_fs_sim", "law_firm_sim"),
    ("media_studio_fs", "media_studio_fs_sim", "media_studio_sim"),
]


def copy_demo_fs(app_fs: str) -> None:
    src = WORKTREE / "demo" / app_fs
    dst = MAIN_REPO / "demo" / app_fs
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"  copied demo/{app_fs} -> main repo")


def combine_sim(sim_dir_src: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    all_flows: list[dict] = []
    all_rows: list[dict] = []
    report_parts: list[str] = []
    trace_parts: list[str] = []
    csv_header: list[str] = []

    run_dirs = sorted(sim_dir_src.glob("run_*"))
    for run_dir in run_dirs:
        run_id = run_dir.name

        # flows.jsonl
        flows_path = run_dir / "flows.jsonl"
        if flows_path.exists():
            for line in flows_path.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if line:
                    flow = json.loads(line)
                    flow["run_id"] = run_id
                    all_flows.append(flow)

        # calls.csv
        calls_path = run_dir / "calls.csv"
        if calls_path.exists():
            with calls_path.open(encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                if not csv_header and reader.fieldnames:
                    csv_header = list(reader.fieldnames) + ["run_id"]
                for row in reader:
                    row["run_id"] = run_id
                    all_rows.append(row)

        # report.txt
        report_path = run_dir / "report.txt"
        if report_path.exists():
            report_parts.append(f"\n{'='*80}\nRUN: {run_id}\n{'='*80}\n")
            report_parts.append(report_path.read_text(encoding="utf-8", errors="replace"))

        # http_trace.txt
        trace_path = run_dir / "http_trace.txt"
        if trace_path.exists():
            trace_parts.append(f"\n{'='*80}\nRUN: {run_id}\n{'='*80}\n")
            trace_parts.append(trace_path.read_text(encoding="utf-8", errors="replace"))

    # write combined flows.jsonl
    flows_out = out_dir / "flows.jsonl"
    with flows_out.open("w", encoding="utf-8") as f:
        for flow in all_flows:
            f.write(json.dumps(flow) + "\n")
    print(f"    flows.jsonl  — {len(all_flows)} flows")

    # write combined calls.csv
    calls_out = out_dir / "calls.csv"
    with calls_out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_header)
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"    calls.csv    — {len(all_rows)} rows")

    # write combined calls_report.txt
    report_out = out_dir / "calls_report.txt"
    report_out.write_text("\n".join(report_parts), encoding="utf-8")
    print(f"    calls_report.txt — {len(run_dirs)} runs")

    # write combined http_trace.txt
    trace_out = out_dir / "http_trace.txt"
    trace_out.write_text("\n".join(trace_parts), encoding="utf-8")
    print(f"    http_trace.txt — {len(run_dirs)} runs")

    # copy captured.jsonl as-is (already has all flows)
    captured_src = sim_dir_src / "captured.jsonl"
    if captured_src.exists():
        shutil.copy2(captured_src, out_dir / "captured.jsonl")
        print(f"    captured.jsonl — copied")


def main() -> None:
    for app_fs, sim_src_name, sim_out_name in APPS:
        print(f"\n{'-'*60}")
        print(f"APP: {app_fs}")

        copy_demo_fs(app_fs)

        sim_src = WORKTREE / "demo" / sim_src_name
        sim_out = MAIN_REPO / "logs" / "proxy" / "sessions" / sim_out_name
        print(f"  combining {sim_src_name} -> logs/proxy/sessions/{sim_out_name}/")
        combine_sim(sim_src, sim_out)

    print(f"\n{'='*60}")
    print("Done. Summary:")

    sessions_root = MAIN_REPO / "logs" / "proxy" / "sessions"
    for _, _, sim_out_name in APPS:
        d = sessions_root / sim_out_name
        files = list(d.iterdir())
        print(f"  {sim_out_name}/  — {len(files)} files")
    demo_root = MAIN_REPO / "demo"
    for app_fs, _, _ in APPS:
        count = sum(1 for _ in (demo_root / app_fs).rglob("*") if _.is_file())
        print(f"  demo/{app_fs}/  — {count} files")


if __name__ == "__main__":
    main()
