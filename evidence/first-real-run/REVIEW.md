# Independent review record — reference evidence validator

This file consolidates the independent review evidence of the `B1` run of the Omega Zero loop. It is
derived from two review passes performed by reviewers who were not the author of the change, each
bound to one exact revision. It is a durable record of what reviewers observed; it is not an approval
and not a merge authorization.

Like every artifact in this directory, this file is a sanitized public derivative: private absolute
paths, personal identifiers, and local control-plane identifiers from the run's own records were
removed. The findings, revisions, and observed outcomes are reported as recorded; the wording is not
the verbatim original, and the private originals remain outside this package.

## Verdicts

| Pass | Reviewed revision | Verdict | Blocking findings |
|---|---|---|---|
| Review 1 | pre-fix candidate `a1a226d52fa9517a34ec936e229df46790d8650b` | `CHANGES_REQUIRED` | one, ranked P2 |
| Review 2 | corrected candidate `9d79b90df4af533403e01757f6a5ca99e739d0fa` | `ACCEPTABLE` | none |

Frozen base for both passes: `9f89350b7385fb17c4a8991acfca3accb8d3070c`. Both reviewers worked in a
separate worktree from the Builder and treated the candidate as read-only. Review 2 voids on any
change to its candidate revision; the corrected candidate was integrated unchanged, so the verdict it
records stands for exactly that revision.

The pre-fix revision `a1a226d` is a point-in-time revision of the run, not an ancestor of the
integrated result. It is cited because the correction is only meaningful relative to the revision that
carried the defect.

That revision is not in `main`'s ancestry and is not part of any main-only publication of this
repository: a public reader cannot check it out from the published tree. The published tree and the
snippet below therefore demonstrate the corrected behavior, not the defect. The pre-fix column of the
comparison table records outcomes observed here against the pre-fix revision in the run's private
local record; those outcomes are not reproducible from a main-only publication and are offered as
recorded observations, not as public evidence.

## Review 1 finding

**P2 — schema-version type confusion.** The schema-version check compared the parsed JSON value
directly against the integer `1`. Python treats `True == 1` as true, so a contract or a receipt
carrying `schema_version: true` — a JSON boolean, where the contract requires an integer — passed
validation and exited 0. Either file could carry the bypass independently.

Reproduction, as reported by the reviewer and then repeated independently by the coordinating
principal on pristine copies in a temporary directory:

```bash
# both inputs forced to a boolean schema version
python3 - <<'PY'
import json, subprocess, sys, tempfile
from pathlib import Path

contract = json.load(open("examples/task-contract.json"))
receipt = json.load(open("examples/result-receipt.json"))
contract["schema_version"] = True
receipt["schema_version"] = True

with tempfile.TemporaryDirectory() as td:
    c = Path(td) / "c.json"
    r = Path(td) / "r.json"
    c.write_text(json.dumps(contract))
    r.write_text(json.dumps(receipt))
    proc = subprocess.run(
        [sys.executable, "tools/validate_evidence.py", "--contract", str(c), "--receipt", str(r)],
        capture_output=True,
        text=True,
    )
    print("exit", proc.returncode)
    print(proc.stdout.strip())
PY
```

Observed against the pre-fix revision: exit `0` and `{"error_count":0,"errors":[],"valid":true}`. A
malformed-but-wrongly-typed field passed the gate.

**P3 — no coverage for the class.** The suite exercised an unsupported schema version but contained no
case asserting rejection of a non-integer type in a schema-version field, which is why the defect
reached review at all.

## Correction

The fix was deliberately minimal: an explicit guard requiring an integer and rejecting booleans before
comparing the value, applied at both the contract and receipt check sites. Two regression tests were
added, one per site.

Review 2 verified that the guard is not merely present but effective, and extended the finding:

| Mutated input | pre-fix `a1a226d` | corrected `9d79b90` |
|---|---|---|
| both `schema_version = true` | exit `0`, `valid: true` — bypass | exit `1`, `SCHEMA_VERSION_UNSUPPORTED` |
| both `schema_version = false` | exit `1` | exit `1`, `SCHEMA_VERSION_UNSUPPORTED` |
| contract only `schema_version = true` | exit `0` — bypass | exit `1`, `SCHEMA_VERSION_UNSUPPORTED` |
| receipt only `schema_version = true` | exit `0` — bypass | exit `1`, `SCHEMA_VERSION_UNSUPPORTED` |
| both `schema_version = 1.0` | exit `0` — bypass, missed by review 1 | exit `1`, `SCHEMA_VERSION_UNSUPPORTED` |
| both `schema_version = "1"` | exit `1` | exit `1`, `SCHEMA_VERSION_UNSUPPORTED` |

The float row is the second result of the run: reviewing the fix surfaced an adjacent instance of the
same defect class that the first review had not found. The same integer guard closes it.

Non-vacuity of the regression tests was checked, not assumed: run against the pre-fix validator the two
new tests fail; run against the corrected revision they pass. A test that cannot fail on the revision
it was written to guard would have added nothing.

## Checks rerun by the reviewers

| Check | Observed on the corrected revision |
|---|---|
| `git rev-parse HEAD` | `9d79b90df4af533403e01757f6a5ca99e739d0fa` |
| commit delta over base | one commit, single parent equal to the frozen base |
| changed-path set | nine paths, set-equal to the contract's allowed paths |
| `git status --porcelain` before and after review | empty (tracked and non-ignored state unchanged) |
| `git diff --check` | exit `0` |
| `python3 -m unittest discover -s tests -p 'test_*.py' -v` | exit `0`, 17 tests collected and passed |
| validator on the committed examples | exit `0`, `{"error_count":0,"errors":[],"valid":true}` |
| validator on the zero-collected fixture | exit `1`, `{"error_count":1,"errors":["ZERO_COLLECTED"],"valid":false}` |
| determinism | repeated runs byte-identical |
| output bound | every probe stayed far below the 4 KiB cap; supplied content never echoed |
| imports | standard library only in both the validator and the tests |
| execution and network surface | no command execution, shell, network, Git, or control-plane access in the validator code itself |

Review 2 also probed type confusion at the other integer fields, malformed top-level documents,
duplicate and traversal paths, directory and non-UTF-8 inputs, and argument-edge cases. Every probe
either degraded safely with a named error and a nonzero exit, or was a documented legal case. No
traceback was observed in any case.

## Findings not acted on

Two informational observations were recorded and deliberately not fixed, because acting on them would
have changed behavior outside the contract:

- When the contract itself is structurally invalid, the cross-file path check can still add
  `FILE_OUT_OF_ALLOWED_PATHS` to the error list. The verdict and exit status are correct regardless,
  output stays deterministic and bounded, and the behavior is unchanged from before the run.
- Running the checks creates ignored interpreter cache directories. Because they are ignored,
  `git status` stays clean; the honest claim is therefore "tracked and non-ignored state unchanged",
  not "the filesystem is byte-for-byte identical".

## What this review does not establish

- It is not an approval, an acceptance, or a merge. Only the human decides those.
- It does not prove the change is correct in meaning, that any receipt is truthful, or that any
  command recorded inside a receipt ran.
- It does not establish portability, containment, or scale.
- It covers one local environment and one revision per pass. Any later change invalidates the second
  verdict and requires a new review bound to the new revision.
