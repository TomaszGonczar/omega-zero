import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
VALID_CONTRACT = ROOT / "examples/task-contract.json"
VALID_RECEIPT = ROOT / "examples/result-receipt.json"
ZERO_CONTRACT = ROOT / "tests/fixtures/zero-collected/task-contract.json"
ZERO_RECEIPT = ROOT / "tests/fixtures/zero-collected/result-receipt.json"
SCRIPT = ROOT / "tools/validate_evidence.py"


def run_validator(*args):
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed


def run_with_payload(contract, receipt):
    return run_validator("--contract", str(contract), "--receipt", str(receipt))


def parse_output(proc):
    return json.loads(proc.stdout)


def read_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)


class ValidateEvidenceTests(unittest.TestCase):
    def test_missing_input(self):
        proc = run_validator()
        payload = parse_output(proc)

        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(payload["errors"], ["MISSING_INPUT"])
        self.assertNotIn("Traceback", proc.stdout + proc.stderr)

    def test_missing_contract(self):
        proc = run_validator("--contract", "missing-contract.json", "--receipt", str(VALID_RECEIPT))
        payload = parse_output(proc)

        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(payload["errors"], ["MISSING_INPUT"])

    def test_missing_receipt(self):
        proc = run_validator("--contract", str(VALID_CONTRACT), "--receipt", "missing-receipt.json")
        payload = parse_output(proc)

        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(payload["errors"], ["MISSING_INPUT"])

    def test_malformed_json(self):
        with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as contract_file:
            contract_file.write("{\n")
            contract_path = Path(contract_file.name)

        proc = run_with_payload(contract_path, VALID_RECEIPT)
        payload = parse_output(proc)

        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("INVALID_JSON", payload["errors"])
        self.assertNotIn("Traceback", proc.stdout + proc.stderr)

    def test_malformed_receipt_json(self):
        with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as receipt_file:
            receipt_file.write("[\n")
            receipt_path = Path(receipt_file.name)

        proc = run_with_payload(VALID_CONTRACT, receipt_path)
        payload = parse_output(proc)

        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("INVALID_JSON", payload["errors"])
        self.assertNotIn("Traceback", proc.stdout + proc.stderr)

    def test_unsupported_schema(self):
        contract = read_json(VALID_CONTRACT)
        receipt = read_json(VALID_RECEIPT)
        contract["schema_version"] = 2

        with tempfile.TemporaryDirectory() as td:
            contract_path = Path(td) / "task-contract.json"
            receipt_path = Path(td) / "result-receipt.json"
            write_json(contract_path, contract)
            write_json(receipt_path, receipt)

            proc = run_with_payload(contract_path, receipt_path)
            payload = parse_output(proc)

        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("SCHEMA_VERSION_UNSUPPORTED", payload["errors"])

    def test_boolean_schema_version_in_contract(self):
        contract = read_json(VALID_CONTRACT)
        contract["schema_version"] = True

        with tempfile.TemporaryDirectory() as td:
            contract_path = Path(td) / "task-contract.json"
            receipt_path = Path(td) / "result-receipt.json"
            write_json(contract_path, contract)
            write_json(receipt_path, read_json(VALID_RECEIPT))

            proc = run_with_payload(contract_path, receipt_path)
            payload = parse_output(proc)

        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(payload["valid"])
        self.assertIn("SCHEMA_VERSION_UNSUPPORTED", payload["errors"])

    def test_boolean_schema_version_in_receipt(self):
        receipt = read_json(VALID_RECEIPT)
        receipt["schema_version"] = True

        with tempfile.TemporaryDirectory() as td:
            contract_path = Path(td) / "task-contract.json"
            receipt_path = Path(td) / "result-receipt.json"
            write_json(contract_path, read_json(VALID_CONTRACT))
            write_json(receipt_path, receipt)

            proc = run_with_payload(contract_path, receipt_path)
            payload = parse_output(proc)

        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(payload["valid"])
        self.assertIn("SCHEMA_VERSION_UNSUPPORTED", payload["errors"])

    def test_unexpected_changed_path(self):
        contract = read_json(VALID_CONTRACT)
        receipt = read_json(VALID_RECEIPT)
        contract["allowed_paths"] = ["README.md"]
        receipt["files"] = ["tests/test_validate_evidence.py"]

        with tempfile.TemporaryDirectory() as td:
            contract_path = Path(td) / "task-contract.json"
            receipt_path = Path(td) / "result-receipt.json"
            write_json(contract_path, contract)
            write_json(receipt_path, receipt)

            proc = run_with_payload(contract_path, receipt_path)
            payload = parse_output(proc)

        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("FILE_OUT_OF_ALLOWED_PATHS", payload["errors"])

    def test_duplicate_path(self):
        contract = read_json(VALID_CONTRACT)
        contract["allowed_paths"] = ["README.md", "README.md"]

        with tempfile.TemporaryDirectory() as td:
            contract_path = Path(td) / "task-contract.json"
            receipt_path = Path(td) / "result-receipt.json"
            write_json(contract_path, contract)
            write_json(receipt_path, read_json(VALID_RECEIPT))

            proc = run_with_payload(contract_path, receipt_path)
            payload = parse_output(proc)

        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("INVALID_CONTRACT", payload["errors"])

    def test_duplicate_files_in_receipt(self):
        receipt = read_json(VALID_RECEIPT)
        receipt["files"] = ["README.md", "README.md"]

        with tempfile.TemporaryDirectory() as td:
            contract_path = Path(td) / "task-contract.json"
            receipt_path = Path(td) / "result-receipt.json"
            write_json(contract_path, read_json(VALID_CONTRACT))
            write_json(receipt_path, receipt)

            proc = run_with_payload(contract_path, receipt_path)
            payload = parse_output(proc)

        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("INVALID_RECEIPT", payload["errors"])

    def test_empty_files_is_allowed(self):
        receipt = read_json(VALID_RECEIPT)
        receipt["files"] = []

        with tempfile.TemporaryDirectory() as td:
            contract_path = Path(td) / "task-contract.json"
            receipt_path = Path(td) / "result-receipt.json"
            write_json(contract_path, read_json(VALID_CONTRACT))
            write_json(receipt_path, receipt)

            proc = run_with_payload(contract_path, receipt_path)
            payload = parse_output(proc)

        self.assertEqual(proc.returncode, 0)
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["errors"], [])

    def test_zero_collected(self):
        proc = run_with_payload(ZERO_CONTRACT, ZERO_RECEIPT)
        payload = parse_output(proc)

        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("ZERO_COLLECTED", payload["errors"])
        self.assertNotIn("valid\": true", proc.stdout)

    def test_descriptive_evidence_required(self):
        contract = read_json(VALID_CONTRACT)
        receipt = read_json(VALID_RECEIPT)
        contract["evidence_required"] = [
            "candidate revision",
            "check evidence",
            "tests run",
        ]

        with tempfile.TemporaryDirectory() as td:
            contract_path = Path(td) / "task-contract.json"
            receipt_path = Path(td) / "result-receipt.json"
            write_json(contract_path, contract)
            write_json(receipt_path, receipt)

            proc = run_with_payload(contract_path, receipt_path)
            payload = parse_output(proc)

        self.assertEqual(proc.returncode, 0)
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["errors"], [])

    def test_valid_input(self):
        proc = run_with_payload(VALID_CONTRACT, VALID_RECEIPT)
        payload = parse_output(proc)

        self.assertEqual(proc.returncode, 0)
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["errors"], [])

    def test_deterministic_output(self):
        first = run_with_payload(VALID_CONTRACT, VALID_RECEIPT)
        second = run_with_payload(VALID_CONTRACT, VALID_RECEIPT)

        self.assertEqual(first.returncode, 0)
        self.assertEqual(second.returncode, 0)
        self.assertEqual(first.stdout, second.stdout)

    def test_output_bound(self):
        contract = read_json(VALID_CONTRACT)
        receipt = read_json(VALID_RECEIPT)
        contract["allowed_paths"] = ["README.md"]
        contract["allowed_paths"].extend(
            [f"deep/path/{index}.txt" for index in range(10000)]
        )
        contract["minimum_total_collected"] = 2
        receipt["checks_run"][0]["collected"] = 1
        receipt["checks_run"][1]["collected"] = 0

        with tempfile.TemporaryDirectory() as td:
            contract_path = Path(td) / "task-contract.json"
            receipt_path = Path(td) / "result-receipt.json"
            write_json(contract_path, contract)
            write_json(receipt_path, receipt)

            proc = run_with_payload(contract_path, receipt_path)
            self.assertNotEqual(proc.returncode, 0)
            self.assertLessEqual(len(proc.stdout.encode("utf-8")), 4096)


if __name__ == "__main__":
    unittest.main()
