"""Build an offline, blinded audit from immutable T07 archives. No inference."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "experiments/t07-final-evaluation-v1"
OUT = ROOT / "experiments/t08-t09-expert-audit-v1"
SEED = "LGS-T08-20261020-v1"
LANGUAGES = {"english", "taglish", "bislish"}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")


def rank(namespace, value):
    return hashlib.sha256(f"{SEED}|{namespace}|{value}".encode()).hexdigest()


def records(config):
    return [json.loads(line) for line in
            (FINAL / config / "interactions.jsonl").read_text(encoding="utf-8").splitlines()]


def verify_frozen():
    checks = dict(read(FINAL / "candidate_registration.json")["file_hashes"])
    checks.update(read(FINAL / "execution_manifest.json")["execution_code_hashes"])
    for name, expected in checks.items():
        path = Path(name)
        if not path.is_absolute():
            path = ROOT / name
        if digest(path) != expected:
            raise ValueError(f"Frozen file changed: {name}")
    return len(checks)


def select_groups(rows):
    """Selection uses only category and group ID, never outcomes or label coverage."""
    categories = {}
    for row in rows:
        categories.setdefault(row["pillar"], set()).add(row["question_group_id"])
    if len(categories) != 5 or any(len(ids) != 14 for ids in categories.values()):
        raise ValueError("Expected five categories with fourteen held-out groups each.")
    return {category: sorted(ids, key=lambda gid: rank("selection", gid))[:4]
            for category, ids in sorted(categories.items())}


def register():
    verify_frozen()
    target = OUT / "private/selection_registration.json"
    if target.exists():
        raise FileExistsError("Selection already registered; reuse it, do not select again.")
    a = records("A")
    selection = select_groups(a)
    write(target, {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "selection_algorithm": "Ascending SHA256(seed|selection|group_id); first four per category.",
        "selection_inputs": "Only pillar and question_group_id from the 70-group frame.",
        "selected_groups": selection,
        "timing": "POST_T07_EVALUATION_PRE_HUMAN_RATINGS",
        "methodology_deviation": (
            "No earlier registered audit subset was found in repository preparation/final "
            "evaluation records. Selection occurred after automated results were known. "
            "This does not fulfill a claim of preselection before T07; disclose the timing "
            "and obtain adviser acknowledgement before formal collection. No outcome-based "
            "selection, exclusions or resampling are allowed."),
        "archive_hashes": {c: digest(FINAL / c / "interactions.jsonl") for c in ("A", "B")},
        "manuscript_sha256": digest(Path("D:/thesis/20260923.pdf")),
        "tracker": {"path": "C:/Users/User/Downloads/thesis_progress_tracker.xlsx",
                    "sha256": digest(Path("C:/Users/User/Downloads/thesis_progress_tracker.xlsx")),
                    "tab": "Thesis Tracker", "rows": [18, 19, 20]},
        "requirements": {"groups": 20, "queries": 60, "answers_per_rater": 120,
                         "raters": 3, "reviews": 360, "dimensions": 2, "scale": [1, 2, 3, 4]},
    })
    print("Registered fixed category-balanced selection:", target)


def build():
    verify_frozen()
    registration = read(OUT / "private/selection_registration.json")
    if (OUT / "public").exists():
        raise FileExistsError("Public packet already exists; preserve it and use a new version.")
    for c, expected in registration["archive_hashes"].items():
        if digest(FINAL / c / "interactions.jsonl") != expected:
            raise ValueError(f"Archive changed: {c}")
    selected = set(sum(registration["selected_groups"].values(), []))
    archives = {c: {x["question_id"]: x for x in records(c)} for c in ("A", "B")}
    queries = sorted(q for q, x in archives["A"].items() if x["question_group_id"] in selected)
    assert len(queries) == 60
    for gid in selected:
        assert {archives["A"][q]["language"] for q in queries
                if archives["A"][q]["question_group_id"] == gid} == LANGUAGES
    # Use the exact historical annotation corpus used by T07, not the older
    # same-named compatibility file retained from origin/main during the merge.
    legacy_path = Path("D:/thesis/LGSDeliveryRAGAssistant-main/data/eboss_corpus_chunks_v1.json")
    assert digest(legacy_path) == "1649d2dba95b8e03a57226364f7294d51d8f009af11c8509a74ecbd8cabba152"
    legacy = {x["chunk_id"]: x for x in read(legacy_path)}
    source_pages = read(ROOT / "experiments/chapter3-table-repaired-development-v1/source_pages.json")
    source_hashes = {p["file_source"]: p["pdf_sha256"] for p in source_pages}
    files = sorted(source_hashes)
    source_ids = {name: f"charter-{i+1:02d}.pdf" for i, name in enumerate(files)}
    public = OUT / "public"
    for name in files:
        src = ROOT / "data/raw_charters" / name
        if digest(src) != source_hashes[name]:
            raise ValueError(f"Source PDF differs from corpus provenance: {name}")
        dest = public / "sources" / source_ids[name]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)

    def source_link(x):
        page = int(x["pdf_relative_page"])
        return {"document": x["file_source"], "pdf_page": page,
                "printed_page": x.get("source_page"),
                "href": "../sources/" + source_ids[x["file_source"]] + f"#page={page}"}

    items, mapping, private_records = {}, [], []
    for qid in queries:
        a, b = archives["A"][qid], archives["B"][qid]
        assert a["question"] == b["question"]
        assert a["original_ground_truth_chunk_ids"] == b["original_ground_truth_chunk_ids"]
        query_id = "Q-" + rank("query-id", qid)[:12]
        common, seen = [], set()
        for gold in a["original_ground_truth_chunk_ids"]:
            source = legacy[gold]
            key = (source["file_source"], source["pdf_relative_page"])
            if key not in seen:
                common.append(source_link(source))
                seen.add(key)
        answers = {}
        for c, x in (("A", a), ("B", b)):
            answer_id = "R-" + rank("answer-id", qid + "|" + c)[:16]
            answers[c] = {"answer_id": answer_id, "text": x["answer"] or "",
                          "passages": [dict(source_link(p), label=p["citation"], text=p["text"])
                                       for p in x["citations"]]}
            mapping.append({"answer_id": answer_id, "query_id": query_id,
                            "question_id": qid, "group_id": a["question_group_id"],
                            "configuration": c, "status": x["status"]})
            private_records.append(x)
        items[qid] = {"query_id": query_id, "question": a["question"],
                      "language": a["language"], "category": a["pillar"],
                      "common_sources": common, "answers": answers}
    write(OUT / "private/answer_key.json", mapping)
    write(OUT / "private/original_selected_records.json", private_records)

    # 30 A-left and 30 B-left in each packet; each pair changes side across raters.
    side_order = sorted(queries, key=lambda q: rank("side", q))
    side_index = {q: i for i, q in enumerate(side_order)}
    template_path = ROOT / "audit_ui/packet.html"
    template = template_path.read_text(encoding="utf-8")
    packets = {}
    for n in range(3):
        rater = f"R{n+1:02d}"
        order = sorted(queries, key=lambda q: rank("order-" + rater, q))
        pairs = []
        for q in order:
            item = items[q]
            configs = ["A", "B"] if (side_index[q] + n) % 2 == 0 else ["B", "A"]
            pairs.append({k: v for k, v in item.items() if k != "answers"} |
                         {"responses": [item["answers"][c] for c in configs]})
        payload = {"schema_version": 1, "rubric_version": "chapter3-table2-v1",
                   "rater_id": rater, "packet_version": "t08-t09-v1", "pairs": pairs}
        payload["packet_id"] = hashlib.sha256(
            json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        folder = public / rater
        write(folder / "packet.json", payload)
        # Escaping < prevents model-generated HTML/script injection inside embedded JSON.
        embedded = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
        (folder / "index.html").write_text(template.replace("__PACKET_JSON__", embedded),
                                          encoding="utf-8")
        packets[rater] = payload["packet_id"]
        (folder / "START_HERE.txt").write_text(
            f"YOUR INDEPENDENT AUDIT PACKET: {rater}\n\n"
            "Extract the entire ZIP before opening index.html in Edge or Chrome.\n"
            "Keep the sources folder beside your rater folder. No server is required.\n"
            "Read Instructions in the interface before rating. Complete practice with\n"
            "the facilitator first. Do not discuss formal scores with other raters.\n"
            "Use Download backup at breaks. Browser autosave is a convenience, not a backup.\n"
            "On another computer, import your backup into this same rater packet.\n"
            "When finished, Export final ratings. Return the JSON and CSV to the researcher.\n"
            "Do not send the packet to other raters; each has a different presentation order.\n",
            encoding="utf-8")
        zip_path = OUT / "distribution" / f"{rater}-audit-packet.zip"
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for path in sorted(folder.iterdir()):
                z.write(path, path.relative_to(public))
            for path in sorted((public / "sources").iterdir()):
                z.write(path, path.relative_to(public))

    write(OUT / "private/build_manifest.json", {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "selection_registration_sha256": digest(OUT / "private/selection_registration.json"),
        "packets": packets, "template_sha256": digest(template_path),
        "builder_sha256": digest(Path(__file__)), "source_pdf_hashes": source_hashes,
        "archive_hashes": registration["archive_hashes"],
        "legacy_annotation_corpus": {"path": str(legacy_path), "sha256": digest(legacy_path)},
        "group_counts": dict(Counter(archives["A"][q]["pillar"] for q in queries)),
        "source_policy": (
            "Common page links follow original held-out annotations, including unresolved "
            "chunk transfers. PDFs are verified against frozen source provenance. They are "
            "starting locations, not a certification that reference answers are correct or "
            "complete. Full charters are available; raters may record other relevant pages. "
            "Historical reference answers and normalized queries remain in private archives "
            "to avoid answer anchoring and pipeline identity hints. Actual retrieved passages "
            "and generated answers are preserved verbatim in public packets."),
        "blinding_limit": (
            "Configuration labels, seeds, mapping, normalization and automated scores are "
            "absent from distribution ZIPs. Content/style can still suggest a system. "
            "Custodian with private key is not blind; formal facilitator must not access it."),
        "files": {str(p.relative_to(OUT)): digest(p) for p in sorted(public.rglob("*")) if p.is_file()},
    })
    verify_frozen()
    print("Built three offline packets (60 pairs / 120 answers each):", OUT)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--register-only", action="store_true")
    args = parser.parse_args()
    register() if args.register_only else build()
