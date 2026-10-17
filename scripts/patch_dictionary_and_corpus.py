"""
patch_dictionary_and_corpus.py
Applies the recommended fixes from LGS_Test_Report_2026-10-08:
1. Adds 17 missing dictionary entries (verb-form renewal triggers,
   checklist document terms, temporal expressions).
2. Fixes the 4 duplicate chunk IDs in eboss_corpus_chunks_v1.json by
   deriving collision-free IDs from pdf_relative_page + a new sub-index.
3. Reports what was changed — does NOT silently overwrite without logging.

Run from: D:\dvscode\lgsdragassistant-jasonceddy\LGSDeliveryRAGAssistant
"""

import json
import sys
import copy
from pathlib import Path
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent  # scripts/ -> LGSDeliveryRAGAssistant/
DICT_PATH = ROOT / "data" / "municipal_dictionary_v1.json"
CORPUS_PATH = ROOT / "data" / "eboss_corpus_chunks_v1.json"
LOG_PATH = ROOT / "data" / "patch_log.json"

sys.stdout.reconfigure(encoding="utf-8")

# ── 1. Dictionary additions ────────────────────────────────────────────────────
NEW_ENTRIES = {
    # Verb-form renewal triggers
    "mag renew": {
        "term_id": "DICT-BB-151",
        "language": "Bislish",
        "verified_english_definition": "Business permit renewal application",
        "governance_context_tag": "Business Bureau",
        "polysemy_flag": False,
        "disambiguation_rule": "",
        "curation_source": "manual",
    },
    "mag-renew": {
        "term_id": "DICT-BB-152",
        "language": "Bislish",
        "verified_english_definition": "Business permit renewal application",
        "governance_context_tag": "Business Bureau",
        "polysemy_flag": False,
        "disambiguation_rule": "",
        "curation_source": "manual",
    },
    "i-renew": {
        "term_id": "DICT-BB-153",
        "language": "Bislish",
        "verified_english_definition": "Business permit renewal application",
        "governance_context_tag": "Business Bureau",
        "polysemy_flag": False,
        "disambiguation_rule": "",
        "curation_source": "manual",
    },
    "i-renew ang permit": {
        "term_id": "DICT-BB-154",
        "language": "Bislish",
        "verified_english_definition": "Business permit renewal application",
        "governance_context_tag": "Business Bureau",
        "polysemy_flag": False,
        "disambiguation_rule": "",
        "curation_source": "manual",
    },
    # Checklist document terms
    "lista sa empleyado": {
        "term_id": "DICT-BB-155",
        "language": "Bisaya",
        "verified_english_definition": "List of employees stating name and position (1 copy), required for business permit renewal",
        "governance_context_tag": "Business Bureau",
        "polysemy_flag": False,
        "disambiguation_rule": "",
        "curation_source": "manual",
    },
    "listahan ng empleyado": {
        "term_id": "DICT-BB-156",
        "language": "Tagalog",
        "verified_english_definition": "List of employees with names and positions for permit renewal",
        "governance_context_tag": "Business Bureau",
        "polysemy_flag": False,
        "disambiguation_rule": "",
        "curation_source": "manual",
    },
    "SPA": {
        "term_id": "DICT-CROSS-157",
        "language": "Bislish",
        "verified_english_definition": "Special Power of Attorney notarized by a Notary Public, authorizing a representative to act on behalf of a business owner",
        "governance_context_tag": "Cross_Cutting",
        "polysemy_flag": False,
        "disambiguation_rule": "",
        "curation_source": "manual",
    },
    "espesyal na kapangyarihan": {
        "term_id": "DICT-CROSS-158",
        "language": "Tagalog",
        "verified_english_definition": "Special Power of Attorney (SPA)",
        "governance_context_tag": "Cross_Cutting",
        "polysemy_flag": False,
        "disambiguation_rule": "",
        "curation_source": "manual",
    },
    "partnership resolution": {
        "term_id": "DICT-BB-159",
        "language": "Bislish",
        "verified_english_definition": "Notarized Partnership Resolution granting specific authority and capacity to a representative for business permit transactions",
        "governance_context_tag": "Business Bureau",
        "polysemy_flag": False,
        "disambiguation_rule": "",
        "curation_source": "manual",
    },
    "board resolution": {
        "term_id": "DICT-BB-160",
        "language": "Bislish",
        "verified_english_definition": "Notarized Board Resolution or Secretary's Certificate granting authority to a business representative for permit applications",
        "governance_context_tag": "Business Bureau",
        "polysemy_flag": False,
        "disambiguation_rule": "",
        "curation_source": "manual",
    },
    "secretary's certificate": {
        "term_id": "DICT-BB-161",
        "language": "Bislish",
        "verified_english_definition": "Notarized Secretary's Certificate granting representative authority for business permit applications",
        "governance_context_tag": "Business Bureau",
        "polysemy_flag": False,
        "disambiguation_rule": "",
        "curation_source": "manual",
    },
    "linya sa bisnes": {
        "term_id": "DICT-BB-162",
        "language": "Bisaya",
        "verified_english_definition": "Specific business line or type of business activity declared to the Business Bureau",
        "governance_context_tag": "Business Bureau",
        "polysemy_flag": False,
        "disambiguation_rule": "",
        "curation_source": "manual",
    },
    "linya sa negosyo": {
        "term_id": "DICT-BB-163",
        "language": "Bisaya",
        "verified_english_definition": "Specific business line or type of business activity",
        "governance_context_tag": "Business Bureau",
        "polysemy_flag": False,
        "disambiguation_rule": "",
        "curation_source": "manual",
    },
    # Temporal expressions
    "ugma": {
        "term_id": "DICT-CROSS-164",
        "language": "Bisaya",
        "verified_english_definition": "Tomorrow — temporal expression indicating the following day (used in deadline and appointment queries)",
        "governance_context_tag": "Cross_Cutting",
        "polysemy_flag": False,
        "disambiguation_rule": "",
        "curation_source": "manual",
    },
    "karong adlawa": {
        "term_id": "DICT-CROSS-165",
        "language": "Bisaya",
        "verified_english_definition": "Today — temporal expression",
        "governance_context_tag": "Cross_Cutting",
        "polysemy_flag": False,
        "disambiguation_rule": "",
        "curation_source": "manual",
    },
    "sa sunod na adlaw": {
        "term_id": "DICT-CROSS-166",
        "language": "Bisaya",
        "verified_english_definition": "The next day or tomorrow",
        "governance_context_tag": "Cross_Cutting",
        "polysemy_flag": False,
        "disambiguation_rule": "",
        "curation_source": "manual",
    },
    "sa hapon": {
        "term_id": "DICT-CROSS-167",
        "language": "Bisaya",
        "verified_english_definition": "This afternoon — temporal expression",
        "governance_context_tag": "Cross_Cutting",
        "polysemy_flag": False,
        "disambiguation_rule": "",
        "curation_source": "manual",
    },
}

# ── Load dictionary ────────────────────────────────────────────────────────────
with open(DICT_PATH, encoding="utf-8") as f:
    dictionary = json.load(f)

before_count = len(dictionary)
added_keys = []
skipped_keys = []

for term, entry in NEW_ENTRIES.items():
    if term in dictionary:
        skipped_keys.append(term)
    else:
        dictionary[term] = entry
        added_keys.append(term)

after_count = len(dictionary)

print(f"Dictionary: {before_count} → {after_count} entries")
print(f"  Added ({len(added_keys)}): {added_keys}")
print(f"  Skipped/already present ({len(skipped_keys)}): {skipped_keys}")

with open(DICT_PATH, "w", encoding="utf-8") as f:
    json.dump(dictionary, f, ensure_ascii=False, indent=2)
print(f"  Saved: {DICT_PATH}")

# ── 2. Corpus duplicate ID fix ─────────────────────────────────────────────────
with open(CORPUS_PATH, encoding="utf-8") as f:
    chunks = json.load(f)

# Find duplicates
from collections import Counter, defaultdict
id_counts = Counter(c["chunk_id"] for c in chunks)
dupes = {k for k, v in id_counts.items() if v > 1}
print(f"\nCorpus: {len(chunks)} chunks, {len(id_counts)} unique IDs")
print(f"  Duplicate IDs before fix: {sorted(dupes)}")

# For each duplicate ID, reassign all occurrences after the first
# Strategy: for duplicate IDs, re-derive as CHUNK-{OFFICE}-PDF{pdf_relative_page:04d}-C{occurrence_index:02d}
# We preserve the first occurrence's ID and only fix subsequent collisions.
seen_ids = {}  # id -> first-seen chunk index
id_occurrence = defaultdict(int)
fix_log = []

new_chunks = []
# Track all assigned IDs globally to guarantee uniqueness
assigned_ids = set(c["chunk_id"] for c in chunks if id_counts[c["chunk_id"]] == 1)

for chunk in chunks:
    cid = chunk["chunk_id"]
    if cid in dupes:
        occ = id_occurrence[cid]
        id_occurrence[cid] += 1
        if occ == 0:
            # Keep the first occurrence's ID unchanged (it's the canonical one)
            assigned_ids.add(cid)
            new_chunks.append(chunk)
        else:
            # Derive a collision-free ID using original C-suffix + occurrence counter
            # to ensure uniqueness even when pdf_relative_page repeats.
            # Format: CHUNK-{OFFICE}-PDF{pdf_rel_page:04d}-{orig_seq}X{occ:02d}
            parts = cid.split("-")  # ['CHUNK', 'CTO', 'P186', 'C01']
            office = parts[1]
            orig_seq = parts[-1]    # e.g. 'C01'
            pdf_page = chunk.get("pdf_relative_page", 0)
            candidate = f"CHUNK-{office}-PDF{pdf_page:04d}-{orig_seq}X{occ:02d}"
            # Guarantee uniqueness by incrementing suffix if somehow still taken
            suffix = occ
            while candidate in assigned_ids:
                suffix += 1
                candidate = f"CHUNK-{office}-PDF{pdf_page:04d}-{orig_seq}X{suffix:02d}"
            assigned_ids.add(candidate)
            new_chunk = copy.copy(chunk)
            new_chunk["chunk_id"] = candidate
            new_chunk["_id_patched"] = True
            new_chunk["_original_id"] = cid
            fix_log.append({"old": cid, "new": candidate, "source_page": chunk.get("source_page"), "pdf_relative_page": pdf_page})
            new_chunks.append(new_chunk)
    else:
        new_chunks.append(chunk)

# Verify no more duplicates
new_id_counts = Counter(c["chunk_id"] for c in new_chunks)
remaining_dupes = {k for k, v in new_id_counts.items() if v > 1}
print(f"\n  Fixed: {len(fix_log)} chunk(s) reassigned")
for fix in fix_log:
    print(f"    {fix['old']} -> {fix['new']} (source_page={fix['source_page']}, pdf_page={fix['pdf_relative_page']})")
print(f"  Duplicate IDs after fix: {sorted(remaining_dupes)}")
print(f"  Total chunks after fix: {len(new_chunks)}")

with open(CORPUS_PATH, "w", encoding="utf-8") as f:
    json.dump(new_chunks, f, ensure_ascii=False, indent=2)
print(f"  Saved: {CORPUS_PATH}")

# ── 3. Save patch log ─────────────────────────────────────────────────────────
log = {
    "patch_date": datetime.now().isoformat(),
    "source_report": "LGS_Test_Report_2026-10-08.pdf",
    "dictionary_patch": {
        "entries_before": before_count,
        "entries_after": after_count,
        "added": added_keys,
        "skipped_existing": skipped_keys,
    },
    "corpus_patch": {
        "total_chunks": len(new_chunks),
        "unique_ids_before": len(id_counts),
        "unique_ids_after": len(new_id_counts),
        "duplicate_ids_fixed": fix_log,
        "remaining_duplicates": sorted(remaining_dupes),
    },
    "notes": (
        "Dictionary entries added per test-report gap analysis: verb-form renewal triggers "
        "(mag renew, mag-renew, i-renew, i-renew ang permit), checklist document terms "
        "(lista sa empleyado, listahan ng empleyado, SPA, espesyal na kapangyarihan, "
        "partnership resolution, board resolution, secretary's certificate, linya sa bisnes, "
        "linya sa negosyo), and temporal expressions (ugma, karong adlawa, sa sunod na adlaw, sa hapon). "
        "Corpus CTO-P186 duplicate IDs fixed by reassigning colliding occurrences to "
        "collision-free CHUNK-{OFFICE}-PDF{pdf_page:04d}-C{occ:02d} format. "
        "IMPORTANT: FAISS and BM25 indices must be rebuilt after this patch. "
        "Benchmark references to the reassigned IDs must also be remapped."
    ),
}

with open(LOG_PATH, "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=2)
print(f"\nPatch log saved: {LOG_PATH}")
print("\n=== IMPORTANT: Rebuild required ===")
print("  1. Re-run: python scripts/build_retrieval_indices.py")
print("  2. Check benchmark_scenarios_*.json for references to old CTO-P186 chunk IDs")
print("  3. Re-run: python scripts/verify_ingest.py")
print("  4. Re-run: python scripts/verify_complete_benchmark.py")
