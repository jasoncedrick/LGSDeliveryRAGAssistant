import json

with open("data/eboss_corpus_chunks_v1.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

token_lengths = [c["token_count"] for c in chunks]
max_len = max(token_lengths)
print(f"Validated Chunks: {len(chunks)}")
print(f"Max Token Length: {max_len} (Must be <= 120)")
assert max_len <= 120, "Violation: Found chunk exceeding 120 tokens!"
print("[SUCCESS] All chunks conform to MiniLM token limits.")
