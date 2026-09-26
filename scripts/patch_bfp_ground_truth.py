import json
import re

BENCHMARK_PATH = "data/benchmark_scenarios_draft.json"
CORPUS_PATH = "data/eboss_corpus_chunks_v1.json"

# Key statutory phrases from the BFP Citizen's Charter
BFP_KEYWORD_MAP = {
    "SCENARIO-BFP-001": ["FIRE SAFETY EVALUATION CLEARANCE", "FSEC", "Architectural documents"],
    "SCENARIO-BFP-002": ["FCCT", "0.1%", "50,000.00", "verified estimated value"],
    "SCENARIO-BFP-003": ["FSIF", "15%", "500.00", "regulatory fees charge by LGU"],
    "SCENARIO-BFP-004": ["Simple Transaction", "Complex Transaction", "Highly Technical"],
    "SCENARIO-BFP-005": ["FSCR", "FSCCR", "FSMR", "automatic fire suppression"],
    "SCENARIO-BFP-006": ["MAHIGPIT NA IPINAGBABAWAL", "ACCREDIT", "Recommend any Brand"]
}

def patch_bfp_citations():
    print("[*] Loading corpus and benchmark dataset...")
    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        corpus = json.load(f)
    
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        scenarios = json.load(f)

    bfp_chunks = [c for c in corpus if c["governance_pillar"] == "Bureau of Fire Protection"]
    assert len(bfp_chunks) > 0, "No BFP chunks found in corpus!"

    patched_count = 0

    for s in scenarios:
        gid = s["group_id"]
        if gid in BFP_KEYWORD_MAP:
            keywords = BFP_KEYWORD_MAP[gid]
            matched_ids = []
            
            for chunk in bfp_chunks:
                text = chunk["text_content"].lower()
                # Score chunk based on keyword hit count
                hits = sum(1 for kw in keywords if kw.lower() in text)
                if hits >= 1:
                    matched_ids.append((chunk["chunk_id"], hits))

            # Sort by highest keyword matches
            matched_ids.sort(key=lambda x: x[1], reverse=True)
            
            if matched_ids:
                # Assign top matched chunk ID(s)
                best_ids = [matched_ids[0][0]]
                if len(matched_ids) > 1 and matched_ids[1][1] == matched_ids[0][1]:
                    best_ids.append(matched_ids[1][0])
                
                s["ground_truth_chunk_ids"] = best_ids
                patched_count += 1
                print(f"[+] Re-anchored {gid} -> {best_ids}")
            else:
                # Fallback to the first procedural table chunk
                s["ground_truth_chunk_ids"] = [bfp_chunks[0]["chunk_id"]]
                patched_count += 1
                print(f"[!] Warning: Fallback {gid} -> {[bfp_chunks[0]['chunk_id']]}")

    with open(BENCHMARK_PATH, "w", encoding="utf-8") as f:
        json.dump(scenarios, f, indent=2, ensure_ascii=False)

    print(f"\n[SUCCESS] Patched {patched_count} BFP scenario groups in {BENCHMARK_PATH}.")

if __name__ == "__main__":
    patch_bfp_citations()