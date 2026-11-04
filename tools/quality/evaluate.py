"""Offline dataset validation and scoring of recorded system predictions."""

import argparse
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError, ValidationError

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "docs/quality/golden-dataset"
LABELS = ("correct", "partially_correct", "incorrect")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_jsonl(path):
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        require(bool(line.strip()), f"{path}:{number}: blank row")
        row = json.loads(line)
        require(isinstance(row, dict), f"{path}:{number}: expected object")
        rows.append(row)
    require(bool(rows), f"{path}: empty file")
    return rows


def contract_validator(name):
    contract = yaml.safe_load((ROOT / "docs/api/openapi.yaml").read_text("utf-8"))
    schema = {
        "$ref": f"#/components/schemas/{name}",
        "components": contract["components"],
    }
    return Draft202012Validator(schema, format_checker=FormatChecker())


def validate():
    rows = read_jsonl(DATA / "cases.jsonl")
    manifest = json.loads((DATA / "manifest.json").read_text("utf-8"))
    digest = hashlib.sha256((DATA / "cases.jsonl").read_bytes()).hexdigest()
    require(
        digest == manifest["sha256"], "Dataset checksum changed; version/review needed"
    )
    require(30 <= len(rows) <= 50 and len(rows) == manifest["cases"], "Case count")
    schema = json.loads((DATA / "schema.json").read_text("utf-8"))
    Draft202012Validator.check_schema(schema)
    checker = Draft202012Validator(schema)
    card_checker = contract_validator("Card")
    request_checker = contract_validator("EvaluateAnswerRequest")
    seen = set()
    inputs = set()
    for row in rows:
        checker.validate(row)
        case_id = row["id"]
        require(case_id not in seen, f"Duplicate ID {case_id}")
        seen.add(case_id)
        encoded = json.dumps(row["input"], sort_keys=True, ensure_ascii=False)
        require(encoded not in inputs, f"Duplicate input {case_id}")
        inputs.add(encoded)
        expected, inp = row["expected"], row["input"]
        require(expected["action"] == row["task"], f"Task/action mismatch {case_id}")
        require(row["version"] == manifest["version"], f"Version mismatch {case_id}")
        if row["task"] == "generate":
            card = expected["card"]
            card_checker.validate(card)
            require(
                card["source_fragment"] in inp["source"]["text"], f"Quote {case_id}"
            )
            for key in ("chunk_id", "source_locator", "source_page"):
                require(
                    card[key] == inp["source"][key], f"Source mapping {case_id}: {key}"
                )
            if card["card_type"] == "formula":
                require(card["formula"] in inp["source"]["text"], f"Formula {case_id}")
        elif row["task"] == "evaluate":
            request = {
                key: inp[key]
                for key in (
                    "question",
                    "reference_answer",
                    "source_fragment",
                    "student_answer",
                )
            }
            request.update(
                card_id="00000000-0000-4000-8000-000000000001",
                required_points=expected["required_points"],
            )
            request_checker.validate(request)
            require(
                inp["source_fragment"] in inp["source"]["text"], f"Context {case_id}"
            )
            label = "accepted" if expected["status"] == "correct" else "rejected"
            require(expected["binary_label"] == label, f"Binary label {case_id}")
    tasks = Counter(row["task"] for row in rows)
    labels = Counter(
        row["expected"].get("status") for row in rows if row["task"] == "evaluate"
    )
    require(tasks == {"generate": 16, "abstain": 4, "evaluate": 20}, "Task coverage")
    require(
        labels == {"correct": 10, "partially_correct": 5, "incorrect": 5},
        "Label balance",
    )
    require(
        {row["uc_id"] for row in rows} == {f"QS-UC-0{i}" for i in range(1, 6)},
        "UC coverage",
    )
    return rows, {
        "status": "PASS",
        "cases": len(rows),
        "sha256": digest,
        "tasks": dict(tasks),
        "answer_labels": dict(labels),
        "categories": dict(Counter(row["category"] for row in rows)),
        "scope": "Dataset/schema/contract fixtures only; no model or product tests",
    }


def ratio(numerator, denominator):
    return {
        "numerator": numerator,
        "denominator": denominator,
        "value": numerator / denominator if denominator else None,
    }


def score(rows, path):
    predictions = read_jsonl(path)
    indexed = {}
    for pred in predictions:
        require(pred["id"] not in indexed, f"Duplicate prediction {pred['id']}")
        indexed[pred["id"]] = pred
    require(
        set(indexed) == {row["id"] for row in rows}, "Missing or unknown prediction IDs"
    )
    matrix = {
        actual: {predicted: 0 for predicted in (*LABELS, "error")} for actual in LABELS
    }
    generated = grounded = useful = duplicates = covered = critical = 0
    abstained = exact = false_correct = binary_matches = errors = 0
    checker = contract_validator("Card")
    evidence = []
    for row in rows:
        pred = indexed[row["id"]]
        require(pred.get("task") == row["task"], f"Prediction task {row['id']}")
        error = pred.get("error")
        if error:
            require(isinstance(error, str), "error must be a string")
            errors += 1
            if row["task"] == "evaluate":
                matrix[row["expected"]["status"]]["error"] += 1
            evidence.append({"id": row["id"], "error": error})
            continue
        if row["task"] == "evaluate":
            status = pred.get("status")
            require(status in LABELS, f"Invalid status {row['id']}")
            actual = row["expected"]["status"]
            matrix[actual][status] += 1
            exact += status == actual
            false_correct += status == "correct" and actual != "correct"
            binary_matches += (status == "correct") == (actual == "correct")
        else:
            cards = pred.get("cards")
            require(isinstance(cards, list), f"cards must be an array {row['id']}")
            if row["task"] == "abstain":
                abstained += len(cards) == 0
                continue
            reviews = pred.get("reviews")
            require(
                isinstance(reviews, list) and len(reviews) == len(cards),
                f"Each generated card needs human review {row['id']}",
            )
            case_covered = False
            for card, review in zip(cards, reviews, strict=True):
                checker.validate(card)
                for key in (
                    "grounded",
                    "useful",
                    "duplicate",
                    "critical_error",
                    "covers_question",
                ):
                    require(
                        type(review.get(key)) is bool,
                        f"Boolean review {key} {row['id']}",
                    )
                require(
                    isinstance(review.get("evidence"), str)
                    and review["evidence"].strip(),
                    f"Review evidence missing {row['id']}",
                )
                source = row["input"]["source"]
                exact_quote = card["source_fragment"] in source["text"]
                source_matches = all(
                    card[key] == source[key]
                    for key in ("source_locator", "source_page", "chunk_id")
                )
                formula_ok = (
                    card["card_type"] != "formula" or card["formula"] in source["text"]
                )
                supported = (
                    review["grounded"] and exact_quote and source_matches and formula_ok
                )
                grounded += supported
                useful += supported and review["useful"]
                duplicates += review["duplicate"]
                critical += review["critical_error"]
                case_covered |= supported and review["covers_question"]
                generated += 1
                if not (exact_quote and source_matches and formula_ok):
                    evidence.append(
                        {"id": row["id"], "invalid_context_or_formula": True}
                    )
            covered += case_covered
    metrics = {
        "Q1_grounded": ratio(grounded, generated),
        "Q2_useful": ratio(useful, generated),
        "Q3_accuracy": ratio(exact, 20),
        "Q4_duplicates": ratio(duplicates, generated),
        "Q5_coverage": ratio(covered, 16),
        "abstain_success": ratio(abstained, 4),
        "binary_accuracy": ratio(binary_matches, 20),
    }
    passed = (
        generated > 0
        and grounded / generated >= 0.9
        and useful / generated >= 0.8
        and exact / 20 >= 0.85
        and duplicates / generated <= 0.1
        and covered / 16 >= 0.9
        and abstained == 4
        and false_correct == 0
        and critical == 0
        and errors == 0
        and not evidence
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "thresholds": "proposed; team review pending",
        "metrics": metrics,
        "confusion_matrix": matrix,
        "false_correct": false_correct,
        "critical_errors": critical,
        "system_errors": errors,
        "issues": evidence,
        "scope": "Recorded predictions and supplied human reviews; no model execution",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "score"))
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        rows, report = validate()
        if args.command == "score":
            require(args.predictions is not None, "score requires --predictions")
            report = score(rows, args.predictions)
            report["dataset_sha256"] = hashlib.sha256(
                (DATA / "cases.jsonl").read_bytes()
            ).hexdigest()
            report["predictions_sha256"] = hashlib.sha256(
                args.predictions.read_bytes()
            ).hexdigest()
        report["checked_at"] = datetime.now(UTC).isoformat()
    except (
        ValueError,
        KeyError,
        TypeError,
        OSError,
        yaml.YAMLError,
        SchemaError,
        ValidationError,
    ) as error:
        report = {"status": "ERROR", "error": f"{type(error).__name__}: {error}"}
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
