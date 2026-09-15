#!/usr/bin/env python3
"""Validate Omega Zero Task Contracts and Result Receipts.

Architectural Scope & Invariants:
1. Pure Standard Library: Zero third-party dependencies (no pydantic, jsonschema,
   or external packages) ensuring instant (<10ms) execution, zero supply-chain
   attack surface, and universal execution on air-gapped, containerized, or
   minimal CI environments.
2. Proof-of-Structure Gate: Validates syntactic schema conformance, bounded path
   containment, and declared check counts. It does not execute commands, inspect
   version control or Orca state, access the network, read declared evidence
   paths, judge semantic truth, or grant approvals.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import PurePosixPath
from typing import Any, Dict, Iterable, List, Tuple


MAX_OUTPUT_BYTES = 4096
MAX_INPUT_BYTES = 2 * 1024 * 1024  # 2 MiB per input file (DoS protection)
VALID_RECEIPT_OUTCOMES = {"passed", "failed", "skipped", "error", "unknown"}
SCHEMA_VERSION = 1



def _emit(result: Dict[str, Any], exit_code: int) -> int:
    payload = json.dumps(result, sort_keys=True, separators=(",", ":"))
    if len(payload.encode("utf-8")) > MAX_OUTPUT_BYTES:
        payload = json.dumps(
            {"valid": False, "errors": ["OUTPUT_LIMIT_EXCEEDED"]},
            sort_keys=True,
            separators=(",", ":"),
        )
    print(payload)
    return exit_code


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _is_relative_path(value: str) -> bool:
    if not isinstance(value, str) or "\0" in value:
        return False
    if value in {".", ".."}:
        return False
    if value.startswith(("/", "\\")):
        return False
    if "\\" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts and path.as_posix() not in {".", ""}



def _validate_string_list(
    value: Any,
    *,
    allow_empty: bool,
    require_relative: bool,
    unique: bool,
) -> Tuple[bool, List[str]]:
    if not isinstance(value, list):
        return False, []
    if not allow_empty and len(value) == 0:
        return False, []

    normalized: List[str] = []
    seen: set[str] = set()

    for item in value:
        if not _is_non_empty_string(item):
            return False, []
        item = item.strip()
        if require_relative and not _is_relative_path(item):
            return False, []
        normalized.append(item)
        seen.add(item)

    if unique and len(normalized) != len(seen):
        return False, []

    return True, normalized


def _validate_contract(contract: Any, errors: List[str]) -> Dict[str, Any]:
    if not isinstance(contract, dict):
        errors.append("INVALID_CONTRACT")
        return {}

    schema_version = contract.get("schema_version")
    if (
        not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or schema_version != SCHEMA_VERSION
    ):
        errors.append("SCHEMA_VERSION_UNSUPPORTED")

    for field in ["intent", "base_sha"]:
        if not _is_non_empty_string(contract.get(field)):
            errors.append("INVALID_CONTRACT")
            break

    valid_allowed, allowed_paths = _validate_string_list(
        contract.get("allowed_paths"),
        allow_empty=False,
        require_relative=True,
        unique=True,
    )
    if not valid_allowed:
        errors.append("INVALID_CONTRACT")

    valid_evidence, evidence_required = _validate_string_list(
        contract.get("evidence_required"),
        allow_empty=False,
        require_relative=False,
        unique=True,
    )
    if not valid_evidence:
        errors.append("INVALID_CONTRACT")

    minimum = contract.get("minimum_total_collected")
    if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum < 1:
        errors.append("INVALID_CONTRACT")

    if contract.get("human_merge_only") is not True:
        errors.append("INVALID_CONTRACT")

    return {
        "allowed_paths": allowed_paths if valid_allowed else [],
        "minimum_total_collected": minimum,
        "evidence_required": evidence_required if valid_evidence else [],
    }


def _validate_receipt(receipt: Any, errors: List[str]) -> Dict[str, Any]:
    if not isinstance(receipt, dict):
        errors.append("INVALID_RECEIPT")
        return {}

    schema_version = receipt.get("schema_version")
    if (
        not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or schema_version != SCHEMA_VERSION
    ):
        errors.append("SCHEMA_VERSION_UNSUPPORTED")

    if receipt.get("outcome") not in {"succeeded", "failed"}:
        errors.append("INVALID_RECEIPT")

    if not _is_non_empty_string(receipt.get("artifact_or_commit")):
        errors.append("INVALID_RECEIPT")

    files_valid, files = _validate_string_list(
        receipt.get("files"),
        allow_empty=True,
        require_relative=True,
        unique=True,
    )
    if not files_valid:
        errors.append("INVALID_RECEIPT")

    checks = receipt.get("checks_run")
    if not isinstance(checks, list) or len(checks) == 0:
        errors.append("INVALID_RECEIPT")
        checks = []

    collected_total = 0
    for check in checks:
        if not isinstance(check, dict):
            errors.append("INVALID_CHECK")
            continue

        if not _is_non_empty_string(check.get("command")):
            errors.append("INVALID_CHECK")

        exit_code = check.get("exit_code")
        if not (
            exit_code is None
            or (isinstance(exit_code, int) and not isinstance(exit_code, bool))
        ):
            errors.append("INVALID_CHECK")

        collected = check.get("collected")
        if collected == "not_applicable":
            pass
        elif isinstance(collected, int) and not isinstance(collected, bool) and collected >= 0:
            collected_total += collected
        else:
            errors.append("INVALID_CHECK")

        if check.get("outcome") not in VALID_RECEIPT_OUTCOMES:
            errors.append("INVALID_CHECK")

    for field in ("facts", "inferences", "uncertainties"):
        value = receipt.get(field)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            errors.append("INVALID_RECEIPT")

    return {
        "files": files if files_valid else [],
        "checks": checks,
        "collected_total": collected_total,
    }


def _deduplicate_errors(errors: Iterable[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for code in errors:
        if code not in seen:
            seen.add(code)
            ordered.append(code)
    return ordered


def validate_inputs(contract_path: str, receipt_path: str) -> Tuple[int, Dict[str, Any], List[str]]:
    errors: List[str] = []

    for path in (contract_path, receipt_path):
        try:
            if os.path.getsize(path) > MAX_INPUT_BYTES:
                return 1, {"valid": False, "errors": ["INPUT_LIMIT_EXCEEDED"]}, []
        except FileNotFoundError:
            return 1, {"valid": False, "errors": ["MISSING_INPUT"]}, []
        except OSError:
            return 1, {"valid": False, "errors": ["INVALID_JSON"]}, []

    try:
        with open(contract_path, "r", encoding="utf-8") as f:
            contract = json.load(f)
    except FileNotFoundError:
        return 1, {"valid": False, "errors": ["MISSING_INPUT"]}, []
    except Exception:
        return 1, {"valid": False, "errors": ["INVALID_JSON"]}, []

    try:
        with open(receipt_path, "r", encoding="utf-8") as f:
            receipt = json.load(f)
    except FileNotFoundError:
        return 1, {"valid": False, "errors": ["MISSING_INPUT"]}, []
    except Exception:
        return 1, {"valid": False, "errors": ["INVALID_JSON"]}, []


    contract_summary = _validate_contract(contract, errors)
    receipt_summary = _validate_receipt(receipt, errors)

    if "SCHEMA_VERSION_UNSUPPORTED" not in errors:
        if not set(receipt_summary.get("files", [])).issubset(
            set(contract_summary.get("allowed_paths", []))
        ):
            errors.append("FILE_OUT_OF_ALLOWED_PATHS")

        minimum_total = contract_summary.get("minimum_total_collected")
        if isinstance(minimum_total, int) and minimum_total >= 1:
            if receipt_summary.get("collected_total", 0) < minimum_total:
                errors.append("ZERO_COLLECTED")

    errors = _deduplicate_errors(errors)
    result = {
        "valid": len(errors) == 0,
        "errors": errors,
        "error_count": len(errors),
    }
    return (0 if len(errors) == 0 else 1), result, errors


def _parse_args(argv: List[str]) -> Tuple[str | None, str | None]:
    contract_path: str | None = None
    receipt_path: str | None = None
    i = 1
    while i < len(argv):
        if argv[i] == "--contract":
            if i + 1 >= len(argv):
                return None, None
            contract_path = argv[i + 1]
            i += 2
        elif argv[i] == "--receipt":
            if i + 1 >= len(argv):
                return None, None
            receipt_path = argv[i + 1]
            i += 2
        else:
            return None, None
    return contract_path, receipt_path


def main(argv: List[str]) -> int:
    contract_path, receipt_path = _parse_args(argv)
    if not contract_path or not receipt_path:
        return _emit({"valid": False, "errors": ["MISSING_INPUT"]}, 1)

    exit_code, result, _ = validate_inputs(contract_path, receipt_path)
    return _emit(result, exit_code)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
