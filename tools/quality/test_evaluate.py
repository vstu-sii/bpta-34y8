"""Scorer harness checks; synthetic predictions are never model evidence."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.quality import evaluate


class ScorerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.validation = evaluate.validate()

    def setUp(self):
        self.predictions = []
        for row in self.rows:
            pred = {"id": row["id"], "task": row["task"]}
            if row["task"] == "evaluate":
                pred["status"] = row["expected"]["status"]
            elif row["task"] == "abstain":
                pred["cards"] = []
            else:
                pred["cards"] = [copy.deepcopy(row["expected"]["card"])]
                pred["reviews"] = [
                    {
                        "grounded": True,
                        "useful": True,
                        "duplicate": False,
                        "critical_error": False,
                        "covers_question": True,
                        "evidence": "Synthetic scorer harness, not human/model evaluation",
                    }
                ]
            self.predictions.append(pred)

    def run_score(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "harness.jsonl"
            path.write_text("\n".join(json.dumps(p) for p in self.predictions), "utf-8")
            return evaluate.score(self.rows, path)

    def test_harness_perfect_results(self):
        result = self.run_score()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["metrics"]["Q3_accuracy"]["numerator"], 20)

    def test_missing_id_rejected(self):
        self.predictions.pop()
        with self.assertRaisesRegex(ValueError, "Missing or unknown"):
            self.run_score()

    def test_duplicate_id_rejected(self):
        self.predictions.append(self.predictions[0])
        with self.assertRaisesRegex(ValueError, "Duplicate prediction"):
            self.run_score()

    def test_false_correct_blocks_even_above_accuracy_threshold(self):
        self.predictions[-1]["status"] = "correct"
        result = self.run_score()
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["false_correct"], 1)
        self.assertEqual(result["metrics"]["Q3_accuracy"]["value"], 0.95)

    def test_timeout_kept_in_denominator(self):
        self.predictions[-1] = {"id": "GD-040", "task": "evaluate", "error": "timeout"}
        result = self.run_score()
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["metrics"]["Q3_accuracy"]["denominator"], 20)
        self.assertEqual(result["confusion_matrix"]["incorrect"]["error"], 1)

    def test_forged_quote_rejected_despite_positive_review(self):
        self.predictions[0]["cards"][0]["source_fragment"] = "Made up evidence"
        self.assertEqual(self.run_score()["status"], "FAIL")

    def test_wrong_document_context_rejected(self):
        self.predictions[0]["cards"][0]["source_locator"] = "another-document"
        self.assertEqual(self.run_score()["status"], "FAIL")

    def test_critical_error_blocks(self):
        self.predictions[0]["reviews"][0]["critical_error"] = True
        self.assertEqual(self.run_score()["status"], "FAIL")

    def test_human_review_required(self):
        self.predictions[0]["reviews"] = []
        with self.assertRaisesRegex(ValueError, "needs human review"):
            self.run_score()

    def test_empty_generation_is_not_full_coverage(self):
        for pred in self.predictions[:2]:
            pred.update(cards=[], reviews=[])
        result = self.run_score()
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["metrics"]["Q5_coverage"]["numerator"], 14)

    def test_hallucination_on_unanswerable_question_blocks(self):
        self.predictions[16]["cards"] = [self.predictions[0]["cards"][0]]
        self.assertEqual(self.run_score()["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
