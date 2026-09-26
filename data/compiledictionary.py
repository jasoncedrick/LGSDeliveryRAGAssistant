import os
import json
import glob
import re
import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

def compile_master_dictionary(
    input_source: str = "Master_Candidate_Terms.xlsx",
    output_path: str = "data/municipal_dictionary_v1.json"
):
    """
    Compiles all 6 eBOSS domain worksheets into a key-indexed JSON hashmap
    with O(1) runtime lookup and monosemous field integrity.
    """
    input_path = Path(input_source)
    if not input_path.is_absolute() and not input_path.exists():
        input_path = PROJECT_DIR / "data" / input_path

    output_file = Path(output_path)
    if not output_file.is_absolute():
        output_file = PROJECT_DIR / output_file
    output_file.parent.mkdir(parents=True, exist_ok=True)

    dictionary_hashmap = {}
    total_raw_rows = 0

    # Case 1: Ingesting a single Master Excel Workbook with 6 Worksheets
    if input_path.exists() and input_path.suffix.lower() in (".xlsx", ".xls"):
        print(f"Loading Master Excel Workbook: {input_path}")
        xls = pd.ExcelFile(input_path)
        print(f"Found {len(xls.sheet_names)} worksheets: {xls.sheet_names}")
        
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            total_raw_rows += len(df)
            process_dataframe(df, dictionary_hashmap, sheet)

    # Case 2: Fallback to independent CSV files
    else:
        csv_files = glob.glob("Candidate_Terms_*.csv") or glob.glob("*.csv")
        print(f"Master workbook '{input_source}' not found. Falling back to CSVs: {csv_files}")
        
        for f in csv_files:
            df = pd.read_csv(f)
            total_raw_rows += len(df)
            process_dataframe(df, dictionary_hashmap, f)

    # Sort keys alphabetically for reproducible Git diffs
    sorted_hashmap = {k: dictionary_hashmap[k] for k in sorted(dictionary_hashmap)}

    with open(output_file, "w", encoding="utf-8") as out:
        json.dump(sorted_hashmap, out, indent=2, ensure_ascii=False)

    polysemous_count = sum(1 for v in sorted_hashmap.values() if v["polysemy_flag"])
    monosemous_count = len(sorted_hashmap) - polysemous_count

    print("\n=== COMPILATION AUDIT SUMMARY ===")
    print(f"Raw records processed : {total_raw_rows}")
    print(f"Unique keys compiled   : {len(sorted_hashmap)}")
    print(f"Monosemous terms       : {monosemous_count} (sanitized with rule='')")
    print(f"Polysemous fallbacks   : {polysemous_count} (active clarifying prompts)")
    print(f"File successfully saved: {output_file}\n")

def process_dataframe(df: pd.DataFrame, target_hashmap: dict, source_label: str):
    # Use the aliases in headers such as "Local Term (local_term)".
    def normalize_header(header):
        header = str(header).strip().lower()
        alias = re.search(r"\(([^)]+)\)", header)
        if alias:
            header = alias.group(1)
        return re.sub(r"[^a-z0-9]+", "_", header).strip("_")

    df.columns = [normalize_header(column) for column in df.columns]
    
    required_cols = [
        "term_id", "local_term", "language", 
        "verified_english_definition", "governance_context_tag", 
        "polysemy_flag", "disambiguation_rule"
    ]
    
    for _, row in df.iterrows():
        term = str(row.get("local_term", "")).strip().lower()
        if not term or term == "nan":
            continue

        # Ingestion Integrity for Monosemous Terms
        raw_polysemy = str(row.get("polysemy_flag", "")).strip().lower()
        is_polysemous = raw_polysemy in ["true", "1", "yes", "t"]
        
        # Enforce Rule: If monosemous, rule MUST be empty string
        if is_polysemous:
            disambiguation_rule = str(row.get("disambiguation_rule", "")).strip()
            if len(disambiguation_rule) >= 2 and disambiguation_rule[0] == disambiguation_rule[-1] == '"':
                disambiguation_rule = disambiguation_rule[1:-1].strip()
        else:
            disambiguation_rule = ""

        target_hashmap[term] = {
            "term_id": str(row.get("term_id", "")).strip(),
            "language": str(row.get("language", "")).strip(),
            "verified_english_definition": str(row.get("verified_english_definition", "")).strip(),
            "governance_context_tag": str(row.get("governance_context_tag", "")).strip(),
            "polysemy_flag": is_polysemous,
            "disambiguation_rule": disambiguation_rule,
            "curation_source": "manual"
        }

if __name__ == "__main__":
    # Point this to your actual Excel filename or leave default
    compile_master_dictionary(input_source="Master_Candidate_Terms.xlsx")