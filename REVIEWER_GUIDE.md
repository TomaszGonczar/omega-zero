# Reviewer Guide — Omega Zero

## Review State

* **Current revision:** `main` (`c14ac5b`)
* **Test suite:** 19 tests passed (Python stdlib-only `unittest`, ~1s runtime, zero external dependencies)
* **CLI validator:** `tools/validate_evidence.py` (<10ms execution, 2 MiB DoS bounds)
* **License:** MIT · Single-author repository

---

## What This Repository Demonstrates

* **Deterministic multi-agent task governance:** Task Contracts and Result Receipts specifying immutable base commit, bounded `allowed_paths`, input size ceilings (2 MiB DoS limit), and machine-verified check counts.
* **Zero-dependency reference validator:** Written strictly with the Python standard library (zero pip packages, zero pydantic/jsonschema overhead, <10ms execution time).
* **Fail-closed negative fixtures:** Rigorous rejection of malformed, DoS-sized, path-traversal, null-byte, and boolean-subclass bypass attempts (`tests/fixtures/zero-collected/`).
* **Incident-driven hardening:** Case study documenting how the independent reviewer caught the Python `bool` subclassing `int` (`True == 1`) schema bypass and rejected the candidate before human merge.

---

## What This Repository Does NOT Demonstrate

* **No execution sandbox:** Task contracts and Git worktrees isolate state and define lexical boundaries; they do not replace OS-level process isolation (Docker/Bubblewrap/Seatbelt) for untrusted third-party execution.
* **No complex orchestrator runtime:** This is an open governance profile and reference validator, not a full multi-tenant agent execution platform.
* **No multi-contributor team development:** Single-author repository with self-administered reviews and CI automation.

---

## Fast Review Path (10 Minutes)

1. **Reference Validator:** [`tools/validate_evidence.py`](tools/validate_evidence.py) — The pure standard-library verification engine (~300 lines).
2. **Case Study:** [`docs/CASE_STUDY.md`](docs/CASE_STUDY.md) — Exact chronicle of the `bool` schema bypass caught by the independent reviewer.
3. **Test Suite:** [`tests/test_validate_evidence.py`](tests/test_validate_evidence.py) — 19 test cases covering edge cases, DoS limits, and negative fixtures.
4. **Canonical Formats:** [`examples/task-contract.json`](examples/task-contract.json) & [`examples/result-receipt.json`](examples/result-receipt.json) — The schema structure.
5. **Architectural Authority Matrix:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — Authority separation and 3-layer threat containment model.

---

## Reproduce the Review State

```bash
git checkout main

# 1. Run unit test suite (19 tests, stdlib-only, zero dependencies)
python3 -m unittest discover -s tests -p 'test_*.py' -v

# 2. Validate committed example contract and receipt
python3 tools/validate_evidence.py --contract examples/task-contract.json --receipt examples/result-receipt.json

# 3. Validate first real-run evidence
python3 tools/validate_evidence.py --contract evidence/first-real-run/task-contract.json --receipt evidence/first-real-run/result-receipt.json

# 4. Verify negative fixture (must exit 1 with ZERO_COLLECTED)
python3 tools/validate_evidence.py --contract tests/fixtures/zero-collected/task-contract.json --receipt tests/fixtures/zero-collected/result-receipt.json
```

Expected output:
* `Ran 19 tests in ~1s -> OK`
* `examples`: `{"error_count":0,"errors":[],"valid":true}` (exit code `0`)
* `first-real-run`: `{"error_count":0,"errors":[],"valid":true}` (exit code `0`)
* `zero-collected`: `{"error_count":1,"errors":["ZERO_COLLECTED"],"valid":false}` (exit code `1`)

---

## One Control Worth Falsifying

**Invariant:** `schema_version` must be strictly integer `1`, never boolean `True` (despite Python's `isinstance(True, int) == True`).
* Verification: [`tools/validate_evidence.py`](tools/validate_evidence.py) guards against this explicitly:
  ```python
  if not isinstance(schema_version, int) or isinstance(schema_version, bool) or schema_version != SCHEMA_VERSION:
      return False, ["SCHEMA_VERSION_UNSUPPORTED"]
  ```
* You can test this control by setting `"schema_version": true` and running the validator:
  ```bash
  python3 -c "
  import json, subprocess, sys, tempfile
  with open('examples/task-contract.json') as f: c = json.load(f)
  c['schema_version'] = True
  with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as tmp:
      json.dump(c, tmp); tmp_path = tmp.name
  res = subprocess.run([sys.executable, 'tools/validate_evidence.py', '--contract', tmp_path, '--receipt', 'examples/result-receipt.json'], capture_output=True, text=True)
  print('Exit code:', res.returncode)
  print('Output:', res.stdout.strip())
  "
  ```
  Expected output:
  * `Exit code: 1`
  * `Output: {"error_count":1,"errors":["SCHEMA_VERSION_UNSUPPORTED"],"valid":false}`

---

## Authorship & AI Assistance

Single-author repository. Tomasz Gonczar owns all requirements, architectural decisions, invariants, acceptance criteria, repository state, and merge decisions. Coding agents (Claude Code / Codex / Antigravity CLI) were used as execution pair-programmers. PR reviews, CI pipelines, and gates are self-administered.

---

## Known Limits

1. **Syntactic & structural verification:** The reference validator checks schema conformance, path bounds, and check counts; it does not execute commands or judge semantic veracity.
2. **POSIX path scope:** Bounded path validation expects POSIX paths; Windows-style backslashes are rejected by contract design.
3. **Orchestrator neutral:** Protocol works with any multi-agent runner (Orca, Claude Code, Cursor, Aider) via POSIX CLI contract handoff.
