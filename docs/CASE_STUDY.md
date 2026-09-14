# Case study — one real run of the Omega Zero loop

This is a public-safe record of one complete pass of the Omega Zero loop against its own repository:
the reference evidence validator. The run is called `B1`. It produced the validator you can run today
from `tools/validate_evidence.py`.

The point of the record is not that the loop worked. It is the narrow band of things the run actually
established, and how a plausible-looking result was corrected by independent challenge.

## 1. Problem

Supervised AI coding produces abundant claims and little durable evidence. A typical delivery ends as
prose: a summary, a list of files, and an assertion that tests passed. Nothing in that shape lets a
later reader re-derive what happened, and nothing forces a distinction between these three very
different questions:

1. Did a command run at all?
2. Does the recorded evidence have the shape the process required?
3. Is the work correct in meaning?

Most automation collapses them. Omega Zero separates them by authority: one concern, one authority,
and no actor may shadow another. Git owns revision identity and diffs. The target repository's own
commands own deterministic check evidence. The human owns intent, permission, risk acceptance, and
merge. A validator owns structural shape only — never truth.

## 2. What was built

A single standard-library-only reference validator, `tools/validate_evidence.py`, plus JSON examples,
a negative fixture, and a suite of tests. It reads two JSON files supplied on the command line — a
Task Contract and a Result Receipt — and prints one deterministic, bounded JSON verdict.

It is deliberately small in what it does:

- **Contract checks:** schema version, intent, frozen base revision, a non-empty unique list of
  relative allowed paths, required evidence descriptions, a positive minimum collected count, and an
  explicit human-merge-only flag.
- **Receipt checks:** schema version, outcome, artifact or commit, relative and unique changed files,
  a non-empty list of checks with command, exit code, collected count and outcome, and separate lists
  for facts, inferences, and uncertainties.
- **Cross-file checks:** every file the receipt claims must fall inside the contract's allowed paths,
  and the receipt's declared collected total must meet the contract's minimum. Below that minimum the
  validator fails with `ZERO_COLLECTED`.
- **Output discipline:** errors are deduplicated in first-seen order, the verdict is printed as
  sorted, compact JSON, and output is capped at 4 KiB. Supplied content is never echoed.

It does not execute the commands it reads about, does not open any path named inside its inputs, does
not inspect Git or the control plane, makes no network calls of its own, proves nothing about truth,
approves nothing, and merges nothing.

That boundary is the design, not a limitation to be patched later. A structural checker that also
ran commands would silently become a trust authority it has no standing to be.

## 3. The run

| Stage | Authority | Observed |
|---|---|---|
| Frozen base | Human-approved contract | One commit, nine allowed paths, one local checkout |
| Build | One Builder in a separate worktree | One candidate commit over the base |
| Review 1 | Independent Reviewer, separate worktree | `CHANGES_REQUIRED` |
| Correction | Builder, same candidate line | Strict integer guard, two regression tests |
| Review 2 | Independent Reviewer, separate worktree | `ACCEPTABLE`, no blocking findings |
| Decision | Human | Authorization to integrate the exact reviewed revision locally |
| Integration | Human | Local fast-forward of that exact revision, then revalidation |

The candidate was exactly one commit above the frozen base and touched exactly the nine paths its
contract allowed. The suite ran 17 tests in 17 collected cases; the committed example pair validated
`valid: true` with exit 0; the negative fixture exited 1 with `ZERO_COLLECTED`.

## 4. Correction

The first review found a real defect that the first version had shipped past a green suite.

The schema-version check compared the parsed value directly against the integer `1`. In Python,
`True == 1`, so a contract or receipt carrying `schema_version: true` — a JSON boolean, not an
integer — passed validation and exited 0. The bypass was reproduced independently, not taken on
report. The correction added an explicit integer guard rejecting booleans at both check sites, and
two regression tests. The second review then confirmed that the same guard also closes `1.0`, a float
variant that the first review had missed.

The second review checked that the new tests were not vacuous: run against the pre-fix validator, they
fail; run against the corrected candidate, they pass. A regression test that cannot fail on the
revision it was written to guard is decoration.

This is the most useful output of the run. The Builder completed its task, reported success, and the
suite was green — and the candidate was still wrong. A passing suite plus a completion claim did not
substitute for an independent adversarial check bound to the exact revision.

## 5. Evidence boundary

What the run supports:

- Nine allowed paths changed; the operating contract file was not touched.
- The suite collected and passed 17 tests on the exact candidate.
- The example pair validated true; the negative fixture failed with `ZERO_COLLECTED`.
- A boolean and a float schema version are rejected by the corrected validator, and the regression
  tests discriminate the fix from the pre-fix revision.
- The reviewer bound its verdict to one exact revision, so any change to the candidate voided it.

What the run does not support, stated plainly:

- It does not prove that any command listed in a receipt ran. The validator reads declarations; a
  caller can write a receipt asserting anything.
- It does not prove the evidence is truthful, that the change is correct in meaning, that the work
  was approved, or that anything was merged. Those are claims about truth and authority, and a
  structural checker holds neither.
- It does not prove the loop is production-ready. One run in one local environment is one data point.
- It does not establish portability. No continuous-integration runner and no second platform were
  exercised during the run. The repository-owned run scripts were executed locally; the workflow
  itself was not run, and `actions/checkout`, `actions/setup-python`, and GitHub-hosted runner
  behavior were not executed or observed locally.
- It does not establish containment. A Git worktree separates source state for cooperative writers;
  it is not a sandbox and does not contain hostile execution.
- It does not establish scale. One Builder and one Reviewer is the default, and parallel mutation of
  a single worktree is untested.

Temporal honesty is part of the boundary. `evidence/first-real-run/result-receipt.json` is a sanitized
public derivative of the run's local point-in-time receipt, not that receipt verbatim; the private
original remains outside this package. The derivative preserves the original temporal fact: at the time
the source receipt was written, the candidate was unmerged. `LIFECYCLE.md` records the later
human-authorized local integration that superseded that status. The pre-merge record and the post-run
lifecycle record are different documents with different scopes, and the difference is visible on
purpose.

## 6. Honest limitations

- **Single environment.** One local checkout on one operating system and one interpreter version. The
  workflow names interpreter versions explicitly and does not use a commit-SHA pin for its action
  references; that is a version list, not a proven one.
- **Vendor substitution.** The originally named reviewer provider reached an account usage limit
  during the correction. The human changed the worker policy, and a different model completed the
  correction and the final review. The two reviews of this run therefore came from different models,
  and model diversity is not a correctness claim.
- **Context transfer with gaps.** A fresh worker process was given only durable state — the control
  plane record, Git, the machine contract, and the receipt — and reconstructed the run. It recovered
  the revision, path set, evidence, and correction timeline, but it also asserted a control-plane
  defect that reconciliation disproved: it had read an unscoped, paginated listing and the wrong
  count field. Durable state makes recovery possible; it does not make recovery correct.
- **One abandoned worker session was never closed.** The control plane marked it user-owned after an
  interactive usage prompt, so it was retained rather than force-closed. It was fenced from the
  remaining work and not reused.
- **One placement attempt misfired.** A worker placement inherited an active context and created a
  worktree in the wrong repository. It produced no commit and left no tracked change, but the incident
  is recorded because placement-by-working-directory is not placement evidence.

## 7. Where this stands

The loop has run once, end to end, against a real change, and stopped where it is supposed to stop:
at the human decision. Integration so far is local. No remote was created, nothing was pushed, and
nothing was published. Whether the committed workflow passes on hosted runners is unobserved here.

The validator is a small, honest gate for the shape of evidence. It is not a runtime, not a sandbox,
not a correctness proof, and not a production system.
