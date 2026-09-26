import json

with open("data/eboss_corpus_chunks_v1.json", "r", encoding="utf-8") as f:
    corpus = json.load(f)

bfp_chunks = [c for c in corpus if c["governance_pillar"] == "Bureau of Fire Protection"]
print(f"Total BFP chunks found: {len(bfp_chunks)}")
for c in bfp_chunks:
    snippet = c["text_content"].replace("\n", " ")[:60]
    print(f"  {c['chunk_id']} -> \"{snippet}...\"")