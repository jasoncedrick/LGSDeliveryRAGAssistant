import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/t08-t09-expert-audit-v1"


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


build = module("prepare_expert_audit")
collect = module("collect_expert_ratings")


class ExpertAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packets = [build.read(OUT / "public" / r / "packet.json") for r in ("R01", "R02", "R03")]
        cls.key = {x["answer_id"]: x for x in build.read(OUT / "private/answer_key.json")}
        cls.originals = {(x["question_id"], x["configuration"]): x
                         for x in build.read(OUT / "private/original_selected_records.json")}

    def test_frozen_inputs_and_output_hashes(self):
        self.assertGreater(build.verify_frozen(), 20)
        manifest = build.read(OUT / "private/build_manifest.json")
        for name, sha in manifest["files"].items():
            self.assertEqual(build.digest(OUT / name), sha)

    def test_selection_ignores_scores_and_outcomes(self):
        rows = build.records("A")
        baseline = build.select_groups(rows)
        for row in rows:
            row.update(answer="REPLACED", ranking_metrics={"hit_at_k": 999},
                       status="CHANGED", reference_answer="CHANGED",
                       relevance_mapping_status="CHANGED")
        self.assertEqual(build.select_groups(list(reversed(rows))), baseline)

    def test_sample_balance_and_stable_answers(self):
        answer_sets = []
        orders = []
        for p in self.packets:
            self.assertEqual(len(p["pairs"]), 60)
            counts = {}
            for pair in p["pairs"]:
                counts[pair["category"]] = counts.get(pair["category"], 0) + 1
            self.assertEqual(sorted(counts.values()), [12] * 5)
            self.assertEqual({lang: sum(x["language"] == lang for x in p["pairs"])
                              for lang in build.LANGUAGES},
                             {lang: 20 for lang in build.LANGUAGES})
            answers = {r["answer_id"] for x in p["pairs"] for r in x["responses"]}
            self.assertEqual(len(answers), 120)
            answer_sets.append(answers)
            orders.append([x["query_id"] for x in p["pairs"]])
            self.assertEqual(sum(self.key[x["responses"][0]["answer_id"]]["configuration"] == "A"
                                 for x in p["pairs"]), 30)
        self.assertEqual(answer_sets[0], answer_sets[1])
        self.assertEqual(answer_sets[1], answer_sets[2])
        self.assertNotEqual(orders[0], orders[1])
        for query in orders[0]:
            lefts = {next(x for x in p["pairs"] if x["query_id"] == query)["responses"][0]["answer_id"]
                     for p in self.packets}
            self.assertEqual(len(lefts), 2)

    def test_answers_passages_and_source_links(self):
        for p in self.packets:
            for pair in p["pairs"]:
                for response in pair["responses"]:
                    key = self.key[response["answer_id"]]
                    original = self.originals[(key["question_id"], key["configuration"])]
                    self.assertEqual(response["text"], original["answer"] or "")
                    self.assertEqual([s["text"] for s in response["passages"]],
                                     [s["text"] for s in original["citations"]])
                    self.assertEqual(pair["question"], original["question"])
                    for s in pair["common_sources"] + response["passages"]:
                        target = OUT / "public" / p["rater_id"] / s["href"].split("#")[0]
                        self.assertTrue(target.is_file())

    def test_public_schema_contains_no_researcher_metadata(self):
        prohibited = {"configuration", "normalized_query", "ranking_metrics", "reference_answer",
                      "seed", "answer_key", "original_ground_truth_chunk_ids", "question_id"}
        def visit(value):
            if isinstance(value, dict):
                self.assertFalse(prohibited.intersection(value))
                for v in value.values():
                    visit(v)
            elif isinstance(value, list):
                for v in value:
                    visit(v)
        for p in self.packets:
            visit(p)
        for zpath in (OUT / "distribution").glob("*.zip"):
            with zipfile.ZipFile(zpath) as z:
                self.assertEqual(z.testzip(), None)
                self.assertEqual(len(z.namelist()), 8)
                self.assertFalse(any("private" in name or "key" in name for name in z.namelist()))

    def export(self):
        p = self.packets[0]
        out = {k: p[k] for k in ("schema_version", "packet_id", "rater_id", "rubric_version", "packet_version")}
        out["export_kind"] = "final"
        out["ratings"] = {r["answer_id"]: {
            "relevance": {"score": 2, "unscorable": False, "reason": ""},
            "faithfulness": {"score": None, "unscorable": True, "reason": "Synthetic test only"},
            "note": "Synthetic test only", "flags": [], "updated_at": "2026-10-20T00:00:00Z",
        } for pair in p["pairs"] for r in pair["responses"]}
        return out

    def test_validation_preserves_missing_dimensions(self):
        rows = collect.validate_export(self.export(), self.packets[0])
        self.assertEqual(len(rows), 120)
        self.assertTrue(all(r["faithfulness_score"] is None for r in rows))

    def test_rejects_invalid_scores_missing_reasons_wrong_packet(self):
        original = self.export()
        first = next(iter(original["ratings"]))
        for score in (0, 5, True, "4", 3.5):
            changed = copy.deepcopy(original)
            changed["ratings"][first]["relevance"]["score"] = score
            with self.assertRaises(ValueError):
                collect.validate_export(changed, self.packets[0])
        changed = copy.deepcopy(original)
        changed["ratings"][first]["faithfulness"]["reason"] = ""
        with self.assertRaises(ValueError):
            collect.validate_export(changed, self.packets[0])
        with self.assertRaises(ValueError):
            collect.validate_export(original, self.packets[1])

    def test_csv_formula_safety(self):
        self.assertEqual(collect.safe_cell(" =HYPERLINK(1)"), "' =HYPERLINK(1)")
        self.assertEqual(collect.safe_cell(4), 4)


if __name__ == "__main__":
    unittest.main()
