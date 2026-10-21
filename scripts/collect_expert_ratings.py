"""Validate exported audit JSON and consolidate blinded records without unmasking."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKET_ROOT = ROOT / "experiments/t08-t09-expert-audit-v1/public"
FLAGS = {
    "Incorrect fee", "Wrong requirement or office", "Unsupported statement",
    "Missing information", "Off-topic answer", "Source conflict or ambiguity",
    "No factual claims", "Incomplete or empty output",
    "Claim absent from retrieved passages", "Other",
}


def check_dimension(value):
    if not isinstance(value, dict):
        raise ValueError("Missing dimension")
    score, missing, reason = (value.get(k) for k in ("score", "unscorable", "reason"))
    if type(missing) is not bool or not isinstance(reason, str):
        raise ValueError("Invalid missing-score fields")
    if missing:
        if score is not None or not reason.strip():
            raise ValueError("Unscorable requires a null score and a reason")
    elif type(score) is not int or score not in (1, 2, 3, 4) or reason:
        raise ValueError("Score must be an integer 1-4, with no unscorable reason")


def validate_export(export, packet):
    for key in ("schema_version", "packet_id", "rater_id", "rubric_version", "packet_version"):
        if export.get(key) != packet[key]:
            raise ValueError(f"Packet identity mismatch: {key}")
    if export.get("export_kind") != "final":
        raise ValueError("Use a final JSON export, not a draft backup")
    ratings = export.get("ratings")
    expected = {r["answer_id"] for p in packet["pairs"] for r in p["responses"]}
    if not isinstance(ratings, dict) or set(ratings) != expected:
        raise ValueError("Missing, unknown, or duplicate response identifiers")
    rows = []
    for position, pair in enumerate(packet["pairs"], 1):
        for side, response in zip(("left", "right"), pair["responses"]):
            answer_id = response["answer_id"]
            r = ratings[answer_id]
            for d in ("relevance", "faithfulness"):
                check_dimension(r[d])
            if not isinstance(r.get("note"), str) or not isinstance(r.get("flags"), list):
                raise ValueError("Invalid note or flags")
            if any(f not in FLAGS for f in r["flags"]) or len(r["flags"]) != len(set(r["flags"])):
                raise ValueError("Unknown or duplicate flag")
            if not isinstance(r.get("updated_at"), str):
                raise ValueError("Missing timestamp")
            datetime.fromisoformat(r["updated_at"].replace("Z", "+00:00"))
            row = {key: packet[key] for key in
                   ("rater_id", "packet_id", "packet_version", "rubric_version")}
            row.update(query_id=pair["query_id"], answer_id=answer_id,
                       displayed_side=side, presentation_position=position)
            for d in ("relevance", "faithfulness"):
                row[d + "_score"] = r[d]["score"]
                row[d + "_unscorable"] = r[d]["unscorable"]
                row[d + "_reason"] = r[d]["reason"]
            row.update(evidence_note=r["note"], error_flags="; ".join(r["flags"]),
                       updated_at=r["updated_at"])
            rows.append(row)
    return rows


def safe_cell(value):
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("exports", nargs="+", type=Path)
    p.add_argument("--packet-root", type=Path, default=DEFAULT_PACKET_ROOT)
    p.add_argument("--out", required=True, type=Path,
                   help="New output directory; existing directories are never overwritten")
    args = p.parse_args()
    rows, raters, sources = [], set(), {}
    for path in args.exports:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        rater = data.get("rater_id")
        if rater not in ("R01", "R02", "R03") or rater in raters:
            raise ValueError("Unknown or duplicate rater; select one final export per rater")
        packet = json.loads((args.packet_root / rater / "packet.json").read_text(encoding="utf-8"))
        canonical = dict(packet)
        claimed = canonical.pop("packet_id")
        actual = hashlib.sha256(json.dumps(canonical, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        if actual != claimed:
            raise ValueError("Packet content hash mismatch")
        rows.extend(validate_export(data, packet))
        raters.add(rater)
        sources[str(path.resolve())] = hashlib.sha256(path.read_bytes()).hexdigest()
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "blinded_ratings.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (args.out / "blinded_ratings.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows({k: safe_cell(v) for k, v in row.items()} for row in rows)
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "raters": sorted(raters), "scheduled_reviews": 360, "received_reviews": len(rows),
        "all_three_received": len(raters) == 3,
        "observed_scores": {d: sum(r[d + "_score"] is not None for r in rows)
                            for d in ("relevance", "faithfulness")},
        "unscorable_dimensions": {d: sum(r[d + "_unscorable"] for r in rows)
                                  for d in ("relevance", "faithfulness")},
        "input_sha256": sources,
        "note": "No identities unmasked and no scores imputed. Independent originals remain unchanged.",
    }
    (args.out / "receipt.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
