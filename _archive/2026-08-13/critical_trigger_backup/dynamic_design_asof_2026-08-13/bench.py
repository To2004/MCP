"""Run the bundle gateway over our labelled live-call corpus, per policy arm."""
import csv, json, sys, collections
sys.path.insert(0, "/tmp/claude-343913582/-home-ovadyat/0f6b2a0f-9e83-439c-9310-a205e0f2bdbe/scratchpad/gateway/bundle")
from mcp_security.gateway.artifact import StaticArtifact, ArtifactError
from mcp_security.gateway.scorer import DynamicScorer
from mcp_security.gateway.config import GatewayConfig
from mcp_security.gateway.decision import Action

ARMS = {
    "v7_iso":  "/home/ovadyat/MCP/reports/experiments/v7/five_level_v2_policy_v7_iso",
    "nacombo": "/home/ovadyat/MCP/reports/experiments/v5/five_level_v2_policy_v5r_nacombo",
}
CORPUS = "/home/ovadyat/MCP/reports/experiments/v5/five_level_v2_policy_v5r_nacombo/live_calls.csv"
rows = list(csv.DictReader(open(CORPUS)))

for arm, d in ARMS.items():
    print(f"\n{'='*72}\nARM: {arm}\n{'='*72}")
    arts, scorers = {}, {}
    for org in sorted({r["org"] for r in rows}):
        try:
            art = StaticArtifact.load(f"{d}/{org}.json")           # native load, no adapter
        except (ArtifactError, FileNotFoundError) as e:
            print(f"  {org}: LOAD FAILED -> {e}"); continue
        arts[org] = art
        scorers[org] = DynamicScorer(art, GatewayConfig())
        print(f"  loaded {org}: score_max={art.score_max} kind={art.server_kind} "
              f"tools={len(art.tools)} assets={len(art.asset_ids)} v={art.version}")

    cm = collections.Counter(); res_ok = res_bad = res_none = 0; acts = collections.Counter()
    per_label = collections.defaultdict(collections.Counter)
    for r in sorted(rows, key=lambda x: int(x["index"])):
        sc = scorers.get(r["org"])
        if sc is None: continue
        try: args = json.loads(r["args"]) if r["args"] else {}
        except json.JSONDecodeError: args = {}
        dec = sc.score(r["persona"], r["tool"], args)
        acts[dec.action.value] += 1
        per_label[r["category"]][dec.action.value] += 1
        truth = "benign" if r["category"] == "BENIGN" else "bad"
        pred = "allow" if dec.action == Action.ALLOW else "flag"
        cm[(truth, pred)] += 1
        # resolver accuracy vs the corpus's ground-truth asset column
        if dec.asset is None: res_none += 1
        elif dec.asset == r["asset"]: res_ok += 1
        else: res_bad += 1

    n = sum(cm.values())
    if not n: continue
    tp, fn = cm[("bad", "flag")], cm[("bad", "allow")]
    fp, tn = cm[("benign", "flag")], cm[("benign", "allow")]
    print(f"\n  actions: {dict(acts)}")
    for lab in ("BENIGN", "MISUSE", "MALICIOUS"):
        print(f"    {lab:10} -> {dict(per_label[lab])}")
    print(f"\n  confusion (flag = DEGRADE or DROP):")
    print(f"    true positives  {tp:3}   false negatives {fn:3}")
    print(f"    false positives {fp:3}   true negatives  {tn:3}")
    prec = tp/(tp+fp) if tp+fp else 0; rec = tp/(tp+fn) if tp+fn else 0
    print(f"    precision {prec:.2f}  recall {rec:.2f}  "
          f"FP rate {fp/(fp+tn) if fp+tn else 0:.2f}  ({n} calls)")
    print(f"\n  asset resolution vs corpus ground truth: "
          f"correct {res_ok}  wrong {res_bad}  unresolved {res_none}")
