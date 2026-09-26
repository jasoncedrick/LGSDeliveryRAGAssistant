import json

with open("data/eboss_corpus_chunks_v1.json", "r", encoding="utf-8") as f:
    corpus = json.load(f)
valid_chunk_ids = {c["chunk_id"] for c in corpus}

with open("data/benchmark_scenarios_draft.json", "r", encoding="utf-8") as f:
    scenarios = json.load(f)

missing = []
for s in scenarios:
    for cid in s["ground_truth_chunk_ids"]:
        if cid not in valid_chunk_ids:
            missing.append((s["group_id"], cid))

if missing:
    print(f"[!] Warning: Found {len(missing)} unmapped chunk IDs:")
    for gid, cid in missing:
        print(f"    {gid} -> {cid}")
else:
    print(f"[SUCCESS] All 30 Development Groups verified against {len(valid_chunk_ids)} indexed corpus chunks.")