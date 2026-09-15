# Contributing to Omega Zero

Thank you for your interest in contributing to **Omega Zero**.

Omega Zero is an operating profile and deterministic evidence specification for AI-assisted engineering on top of Orca. Contributions that enhance rigor, clarity, and deterministic verification are welcome.

---

## Core Invariants

Before submitting changes, ensure your contribution respects our architectural invariants:

1. **Standard Library Only**: The core reference validator (`tools/validate_evidence.py`) and test suite have **zero third-party dependencies**. Do not add `pip` or external package dependencies.
2. **Empirical Truthfulness**: Never make claims that are not backed by reproducible evidence or CI runs. Do not disguise assumptions as verified facts.
3. **Bounded Authority**: Authority is strictly segregated. The human holds the only merge edge; workers and reviews are bounded.
4. **Deterministic Checks**: All scripts must produce predictable, deterministic JSON output.

---

## Development & Testing Workflow

1. **Fork and Clone**:
   ```bash
   git clone https://github.com/TomaszGonczar/omega-zero.git
   cd omega-zero
   ```

2. **Run the Test Suite**:
   Run the full local verification suite using Python 3.11+:
   ```bash
   # 1. Run unit tests
   python3 -m unittest discover -s tests -p 'test_*.py' -v

   # 2. Validate committed examples
   python3 tools/validate_evidence.py \
     --contract examples/task-contract.json \
     --receipt examples/result-receipt.json

   # 3. Validate first-real-run evidence
   python3 tools/validate_evidence.py \
     --contract evidence/first-real-run/task-contract.json \
     --receipt evidence/first-real-run/result-receipt.json

   # 4. Check negative fixture (must exit 1 with ZERO_COLLECTED)
   python3 tools/validate_evidence.py \
     --contract tests/fixtures/zero-collected/task-contract.json \
     --receipt tests/fixtures/zero-collected/result-receipt.json
   ```

3. **Code Style**:
   - Python code must follow standard PEP 8 conventions.
   - Use clear variable names and explicit type checks (e.g. `type(val) is int` when verifying JSON integers to avoid boolean type coercion).

---

## Submitting Pull Requests

- Keep pull requests focused on a single bounded objective.
- Include regression tests for any validator bug fixes or additions.
- Ensure that CI passes across Python 3.11, 3.12, and 3.13.
