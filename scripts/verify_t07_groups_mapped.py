"""Verification script to confirm all 70 held-out test groups are 100% mapped."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
crosswalk_path = ROOT / 'experiments/t07-final-evaluation-v1/source_span_crosswalk.json'

if not crosswalk_path.exists():
    raise FileNotFoundError(f"Missing crosswalk file: {crosswalk_path}")

d = json.loads(crosswalk_path.read_text(encoding='utf-8'))
groups = d['groups']

targets_11 = [
    'SCENARIO-BB-018',
    'SCENARIO-CTO-008',
    'SCENARIO-CTO-016',
    'SCENARIO-CPDO-020',
    'SCENARIO-BFP-007',
    'SCENARIO-BFP-008',
    'SCENARIO-BFP-011',
    'SCENARIO-BFP-013',
    'SCENARIO-BFP-014',
    'SCENARIO-BFP-015',
    'SCENARIO-BFP-017',
]

print("=" * 65)
print("AUDITING THE 11 PREVIOUSLY UNMAPPED HELD-OUT GROUPS:")
print("=" * 65)
all_11_ok = True
for gid in targets_11:
    g = groups.get(gid)
    if not g:
        print(f"[-] {gid}: MISSING FROM GROUPS!")
        all_11_ok = False
        continue
    status = "COMPLETE" if g.get("complete") else "INCOMPLETE"
    mapped_ids = g.get("mapped_ids", [])
    print(f"[+] {gid:<18} -> {status:<10} | Mapped IDs ({len(mapped_ids)}): {mapped_ids}")
    if not g.get("complete"):
        all_11_ok = False

print("-" * 65)
total_complete = sum(1 for g in groups.values() if g.get("complete"))
total_groups = len(groups)
print(f"TOTAL COMPLETE GROUPS: {total_complete} / {total_groups}")
print("=" * 65)

assert all_11_ok, "ERROR: Some of the 11 target groups are still incomplete!"
assert total_complete == 70, f"ERROR: Expected 70 complete groups, found {total_complete}!"

print("CONFIRMED: All 70 held-out scenario groups (210 queries) are 100% mapped!")
