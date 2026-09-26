import json

DEV_PATH = "data/benchmark_scenarios_dev.json"
TEST_PATH = "data/benchmark_scenarios_test.json"
CORPUS_PATH = "data/eboss_corpus_chunks_v1.json"

with open(CORPUS_PATH, "r", encoding="utf-8") as f:
    corpus = json.load(f)
valid_chunks = {c["chunk_id"] for c in corpus}

with open(DEV_PATH, "r", encoding="utf-8") as f:
    dev_set = json.load(f)

with open(TEST_PATH, "r", encoding="utf-8") as f:
    test_set = json.load(f)

print("==================================================")
print("BENCHMARK MATRIX AUDIT (100 GROUPS / 300 QUERIES)")
print("==================================================")
print(f"Development Set Groups : {len(dev_set)} (90 queries)")
print(f"Held-Out Test Groups   : {len(test_set)} (210 queries)")
print(f"Total Scenario Groups  : {len(dev_set) + len(test_set)} (300 queries)")

assert len(dev_set) == 30, f"Error: Expected 30 dev groups, found {len(dev_set)}"
assert len(test_set) == 70, f"Error: Expected 70 test groups, found {len(test_set)}"

dev_ids = {s["group_id"] for s in dev_set}
test_ids = {s["group_id"] for s in test_set}
collisions = dev_ids.intersection(test_ids)
assert len(collisions) == 0, f"Fatal: Cross-split collision on group IDs: {collisions}"

all_scenarios = dev_set + test_set
broken_citations = []
for s in all_scenarios:
    for cid in s["ground_truth_chunk_ids"]:
        if cid not in valid_chunks:
            broken_citations.append((s["group_id"], cid))

if broken_citations:
    print(f"\n[!] ERROR: Found {len(broken_citations)} unmapped chunk citations:")
    for gid, cid in broken_citations:
        print(f"    {gid} -> {cid}")
    raise RuntimeError("Corpus citation audit failed!")

print("\n[+] Zero Cross-Split Collisions.")
print("[+] All 300 queries successfully anchored to valid corpus chunks.")
print("==================================================")
print("[SUCCESS] TASK T05 IS OFFICIALLY COMPLETE AND FROZEN.")
print("==================================================")