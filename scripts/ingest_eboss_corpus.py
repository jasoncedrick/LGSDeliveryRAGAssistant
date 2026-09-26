import os
import re
import json
import fitz  # PyMuPDF
from typing import List, Dict, Any
from transformers import AutoTokenizer

# Architectural parameters aligned with Chapter 3 (Section 3.2.2)
TOKENIZER_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CHUNK_SIZE = 120       # Strict token boundary to avoid 128-token truncation
CHUNK_OVERLAP = 20     # Overlap window for procedural continuity
OUTPUT_FILE = "data/eboss_corpus_chunks_v1.json"

# Catalog mapping directly to your five uploaded files
INGESTION_CATALOG = [
    {
        "pillar": "Business Bureau",
        "pillar_code": "BB",
        "file_name": "Business Bureau CGD_Citizen Charter 2026_VOL.I & II.pdf",
        "document_title": "Davao City Citizens Charter 2026 - Business Bureau (External Services)"
    },
    {
        "pillar": "City Treasurer's Office",
        "pillar_code": "CTO",
        "file_name": "City Treasurer's CGD_Citizen Charter 2026_VOL.I & II-2.pdf",
        "document_title": "Davao City Citizens Charter 2026 - City Treasurer's Office (External Services)"
    },
    {
        "pillar": "Office of the City Building Official",
        "pillar_code": "OCBO",
        "file_name": "OCBD Pages from CGD_Citizen Charter 2026_VOL.I & II-2.pdf",
        "document_title": "Davao City Citizens Charter 2026 - Office of the City Building Official"
    },
    {
        "pillar": "City Planning and Development Office",
        "pillar_code": "CPDO",
        "file_name": "City Planning CGD_Citizen Charter 2026_VOL.I & II-3.pdf",
        "document_title": "Davao City Citizens Charter 2026 - CPDO Zoning Enforcement Division"
    },
    {
        "pillar": "Bureau of Fire Protection",
        "pillar_code": "BFP",
        "file_name": "BFP-CITIZENS-CHARTER-2022.pdf",
        "document_title": "BFP Citizen's Charter - Fire Safety Enforcement Services"
    }
]

def sanitize_and_format_text(page: fitz.Page) -> str:
    """
    Extracts text using layout-aware blocks to preserve table rows
    and regularizes whitespace without destroying statutory structures.
    """
    # Extract structural text blocks (preserves row/column boundaries better than raw text)
    blocks = page.get_text("blocks")
    lines = []
    
    for b in blocks:
        block_text = b[4]
        # Strip non-ASCII/corrupt symbols while preserving currency signs and numerals
        cleaned_block = re.sub(r"[^\x20-\x7E\n₱]", " ", block_text)
        cleaned_block = re.sub(r"[ \t]+", " ", cleaned_block).strip()
        if cleaned_block:
            lines.append(cleaned_block)
            
    full_text = "\n".join(lines)
    # Collapse 3+ consecutive line breaks into standard double paragraph breaks
    full_text = re.sub(r"\n{3,}", "\n\n", full_text)
    return full_text.strip()

def detect_printed_page_number(text: str, pdf_page_idx: int) -> int:
    """
    Attempts to parse the original printed Citizen's Charter page number
    from the text header/footer. Falls back to pdf_page_idx + 1.
    """
    # Looks for isolated 2 to 3 digit numbers at the beginning or end of pages
    matches = re.findall(r"(?:^|\n\s*)(\d{2,3})(?:\s*\n|$)", text)
    if matches:
        try:
            val = int(matches[-1])
            if 30 <= val <= 800:
                return val
        except ValueError:
            pass
    return pdf_page_idx + 1

def tokenize_and_split(text: str, tokenizer: Any, chunk_size: int = 120, chunk_overlap: int = 20) -> List[Dict[str, Any]]:
    """
    Segments text using Hugging Face token-level sliding windows.
    Guarantees no chunk exceeds chunk_size tokens.
    """
    tokens = tokenizer.encode(text, add_special_tokens=False)
    if not tokens:
        return []

    step = chunk_size - chunk_overlap
    token_chunks = []

    for i in range(0, len(tokens), step):
        slice_ids = tokens[i : i + chunk_size]
        decoded = tokenizer.decode(slice_ids, skip_special_tokens=True).strip()
        if decoded:
            token_chunks.append({
                "text": decoded,
                "token_count": len(slice_ids)
            })
        if i + chunk_size >= len(tokens):
            break

    return token_chunks

def execute_ingestion(data_dir: str = "."):
    print(f"[*] Loading Tokenizer: {TOKENIZER_NAME}...")
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME)

    master_chunks = []
    total_files_processed = 0

    for entry in INGESTION_CATALOG:
        file_path = os.path.join(data_dir, entry["file_name"])
        pillar = entry["pillar"]
        pillar_code = entry["pillar_code"]
        doc_title = entry["document_title"]

        if not os.path.exists(file_path):
            print(f"[!] ERROR: Target file not found at: {file_path}")
            continue

        doc = fitz.open(file_path)
        total_pages = len(doc)
        print(f"\n[*] Scanning '{entry['file_name']}' ({total_pages} total pages) for Pillar: {pillar}...")
        
        pillar_chunk_count = 0

        # Scan every page in the pre-sliced PDF
        for p_idx in range(total_pages):
            page = doc.load_page(p_idx)
            raw_text = sanitize_and_format_text(page)

            # Safeguard against completely blank pages
            if len(raw_text) < 25:
                continue

            printed_page = detect_printed_page_number(raw_text, p_idx)
            chunks = tokenize_and_split(raw_text, tokenizer, CHUNK_SIZE, CHUNK_OVERLAP)

            for c_idx, c_data in enumerate(chunks):
                pillar_chunk_count += 1
                chunk_id = f"CHUNK-{pillar_code}-P{printed_page:03d}-C{c_idx+1:02d}"

                master_chunks.append({
                    "chunk_id": chunk_id,
                    "governance_pillar": pillar,
                    "document_title": doc_title,
                    "file_source": entry["file_name"],
                    "source_page": printed_page,
                    "pdf_relative_page": p_idx + 1,
                    "token_count": c_data["token_count"],
                    "text_content": c_data["text"],
                    "version_date": "2026"
                })

        doc.close()
        total_files_processed += 1
        print(f"    -> Extracted {pillar_chunk_count} valid chunks for {pillar}.")

    if not master_chunks:
        raise RuntimeError("Zero chunks extracted. Check file directory paths and PDF permissions.")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(master_chunks, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 65)
    print(f"Ingestion Finished: Processed {total_files_processed}/{len(INGESTION_CATALOG)} files.")
    print(f"Total Serialized Chunks: {len(master_chunks)}")
    print(f"Corpus Database Exported to: {OUTPUT_FILE}")
    print("=" * 65)

if __name__ == "__main__":
    # If the PDF files are in a specific subfolder, change "." to that path (e.g., "data/raw_charters")
    execute_ingestion(".")