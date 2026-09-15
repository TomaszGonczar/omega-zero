# Omega Zero

Omega Zero is a small operating profile for AI-assisted development on top of Orca. It defines who
holds authority, how bounded work is specified, what evidence a result must carry, and where the
work stops for a human decision. It is a set of rules and templates — not a runtime.

In its first real run this profile produced the reference validator; independent review then found a
schema-version bypass on a candidate whose tests were green, the defect was fixed and locally
integrated, and hosted CI across Python 3.11–3.13 on GitHub Actions has now been verified.


An optional reference validator now lives at `tools/validate_evidence.py` for local JSON sanity checks.
It validates Task Contracts and Result Receipts against the profile requirements only and prints a
deterministic report. This is a local script for validation only, not an installed agent CLI or runtime.

Orca supplies the control and workspace plane: durable Run/Task/Dispatch identity, worker process
lifecycle, terminal and worktree placement, messages, and settlement. Omega Zero supplies the human
contract around that machinery: one semantic Principal, bounded worker tasks, independent review of
the exact candidate, and evidence-before-completion.

## Contents

| Path | Purpose |
|---|---|
| `AGENTS.md` | The operating contract an agent reads before acting |
| `docs/ARCHITECTURE.md` | Runtime sequence, authority matrix, monitoring, threat boundary |
| `docs/WORKFLOW.md` | Task Contract and Result Receipt templates, run sequence, evidence rules |
| `docs/CASE_STUDY.md` | One real run of the loop, its correction, and its evidence boundary |
| `README.md` | Purpose, quick use, and honest limits |
| `tools/validate_evidence.py` | Optional standard-library reference validator for contract/receipt JSON |
| `examples/` | A valid contract and receipt pair |
| `tests/` | Standard-library tests plus the zero-collected negative fixture |
| `evidence/first-real-run/` | Sanitized public derivatives of the first real run's local evidence |
| `.github/workflows/ci.yml` | Version-tagged GitHub Actions checks for this repository |
| `.gitignore` | Local-only files |

The profile is Markdown. The one executable is the optional validator. There is no package, runtime
service, database, scheduler, or dashboard here. The consuming repository owns its code, checks, and
integration in place of or alongside these.

## What CI checks

`.github/workflows/ci.yml` is configured to run on `ubuntu-latest` for explicit Python versions
`3.11`, `3.12`, and `3.13`. As configured, on a clean checkout it:

1. Fails if test discovery collects zero tests: it discovers the suite, prints the count, and fails
   with `ZERO_COLLECTED` when the count is below one. A missing or unreadable `tests/` directory, or a
   directory-level discovery failure, fails with `DISCOVERY_ERROR` instead. A test module that fails at
   import or contains a syntax error is not a directory-level failure: `unittest` represents it as a
   failed test, so the guard still sees a nonzero count and the following suite step fails.
2. Runs the standard-library test suite with `python3 -m unittest discover -s tests -p 'test_*.py' -v`.
3. Validates the committed examples and the committed first-real-run evidence pair through
   `tools/validate_evidence.py`, both of which must report `valid: true`.
4. Checks the negative fixture, which must exit `1`, report `valid: false`, and include
   `ZERO_COLLECTED`.

Notes on what that CI is and is not. Action references are explicit version tags, not commit-SHA
pins: a tag is a moveable reference under the action author's control, and none of them is claimed to
be the newest or universally available. The interpreter list is a version list to run on, not a
support claim. This repository declares and installs no project dependencies because the suite and
the validator use only the standard library — but the workflow is not self-contained: the checkout and
setup steps run on GitHub-hosted infrastructure, `setup-python` provisions an interpreter, and the run
therefore depends on that infrastructure and cannot be described as network-free or install-free. What
was originally executed locally was the repository-owned run scripts — the unittest, validator, and
guard commands the workflow invokes. Following public release, the GitHub Actions workflow was
executed on hosted runners (`ubuntu-latest`, Python 3.11, 3.12, 3.13) under run ID `34937827742`,
verifying that runner checkout, Python provisioning, matrix execution, and all check steps succeed as
declared.


## Quick use

1. Read `AGENTS.md`.
2. Adapt it into the repository that will actually consume the profile. The profile is only real
   where a target repository uses it.
3. Write one Task Contract from `docs/WORKFLOW.md`: intent, frozen base revision, allowed paths,
   capability envelope, and observable acceptance.
4. Run the loop: Principal decomposes → Orca dispatches one Builder into a separate worktree → the
   exact candidate is reviewed by an independent Reviewer → Git, checks, and receipts are
   reconciled.
5. Stop at the human decision. Integration and merge are human acts.
6. Optionally run:
   `python3 tools/validate_evidence.py --contract examples/task-contract.json --receipt examples/result-receipt.json`

Running the repository-owned checks locally, in full:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tools/validate_evidence.py --contract examples/task-contract.json --receipt examples/result-receipt.json
python3 tools/validate_evidence.py --contract evidence/first-real-run/task-contract.json --receipt evidence/first-real-run/result-receipt.json
python3 tools/validate_evidence.py --contract tests/fixtures/zero-collected/task-contract.json --receipt tests/fixtures/zero-collected/result-receipt.json
```

The first three commands must exit 0; the last must exit 1 with `ZERO_COLLECTED`.

## Status

Honest status, as of this profile revision:

- A real run of the loop, `B1`, has been exercised end to end against this repository and produced the
  reference validator. Its record is in `evidence/first-real-run/`, and the narrative is in
  `docs/CASE_STUDY.md`.
- Independent review mattered. The first reviewed candidate passed its suite but accepted a JSON
  boolean `schema_version` — and, as the second review showed, a float `1.0` — because Python treats
  `True == 1`. The reviewer's report was reproduced independently, the candidate was corrected with a
  strict integer guard and two non-vacuous regression tests, and the corrected revision was reviewed
  again as acceptable.
- The human then locally integrated the exact reviewed revision. Local `main` equals that revision.
- The repository is published at `https://github.com/TomaszGonczar/omega-zero` under the MIT license.
  Hosted continuous integration on GitHub Actions has been verified across Python 3.11, 3.12, and
  3.13 (run ID `34937827742`).

- The run's evidence is point-in-time. The files in `evidence/first-real-run/` are sanitized public
  derivatives of the run's local records, not the verbatim originals; the private originals remain
  outside this package. The derivative Result Receipt preserves the original temporal fact — the
  candidate was unmerged when the source receipt was written — and `evidence/first-real-run/LIFECYCLE.md`
  records the later local integration that superseded that status.
- One run in one local environment is evidence that the loop runs, not that it is production-ready.
  No second platform and no continuous-integration runner were exercised during the run.
- No auto-merge.
- No semantic-correctness claim: checks and reviews bound behavior and evidence, not meaning.
- No containment claim: nothing here isolates untrusted execution.
- No scaling claim: one Builder and one Reviewer is the default, and parallel mutation is untested.
- The validator is a reference-only gate and does not execute commands, inspect Git/Orca state,
  run through any agent CLI automation path, make network calls of its own, read any declared evidence
  paths, judge truth, request approval, or perform merges. It validates supplied JSON structure and
  declared counts only.

## Limits

- A Git worktree separates source state for cooperative writers; it is not a security sandbox.
- Orca monitors process lifecycle, not semantic correctness.
- The Principal interprets intent, decomposes, judges evidence, and reconciles, but cannot
  self-approve and cannot merge.
- Skills are optional procedures a worker CLI may load; they are not agents and carry no authority.
- A passing test suite and a worker completion claim are not evidence of correctness. In this
  repository's own run, both were true of a revision that was wrong.
