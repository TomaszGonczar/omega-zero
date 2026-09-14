# Omega Zero workflow

One run = one human goal, one Task Contract, one bounded Builder, one independent Reviewer, one
human decision. This file holds the two templates everything else refers to.

## 1. Run sequence

1. **Intent.** The human states a goal and the risk they are willing to accept.
2. **Contract.** The Principal writes a Task Contract (section 3) and gets it approved before any
   work starts. If the contract is incomplete, work does not start.
3. **Dispatch.** Orca records Run/Task/Dispatch identity and launches one Builder into a separate
   worktree, with the contract as the prompt. Record the frozen base revision and the launch
   configuration Orca reports as effective.
4. **Build.** The Builder makes one bounded change in its worktree, runs the contract's checks, and
   commits. It reports a Result Receipt (section 4).
5. **Reconcile.** `worker_done` is a claim. The Principal checks the dispatch identity, the candidate
   revision and changed paths, the commands and exit statuses, and the receipt's facts against
   inferences. Worker completion is not acceptance.
6. **Review.** A different process reviews the exact candidate: revision, ancestry, diff, changed
   paths, and a rerun of the same checks. Review does not mutate.
7. **Decide.** The human accepts for integration, asks for revision, rejects, or holds. Merging is a
   separate human act.
8. **Close.** Record the decision, preserve the candidate and receipts, and stop. If the human did
   not decide, the endpoint is `AWAITING_HUMAN`.

Roles are task shapes, not permanent personas. Default fleet: one Principal, one Builder, one
independent Reviewer; add a Scout only when the task needs discovery.

## 2. Workspace and check rules

- One mutating worker per worktree. The Builder is the sole writer of its worktree.
- Freeze the base revision before dispatch; identify the candidate by revision, never by branch name
  or terminal title.
- Record the exact changed-path set, and the worktree status before and after.
- Run the checks the target repository already documents. Do not invent a parallel test suite to
  make a result look verified.
- Record the exact command, the exit status, and the observed output. Count what was collected.
- Zero tests collected, a missing summary, a clipped summary, or unexpected paths means `unknown` or
  failure — never a pass.
- The Reviewer reruns the same command on the exact candidate. If the candidate revision changes,
  the review is void.
- Record warnings for truncation, dirty state, missing fields, and nondeterminism. Persistent
  disagreement between runs is `NONDETERMINISTIC`: do not keep rerunning merely until the result
  turns green. Investigate the cause and record the nondeterminism instead.

## 3. Task Contract template

One page, approved before dispatch. Prompt text expresses the contract; the tooling in use enforces
only the capabilities it actually exposes. Unknown or expanded action classes stop and escalate
rather than inheriting permission.

```yaml
intent: one sentence in the human's terms
acceptance: observable outcomes
out_of_scope: explicit exclusions
repository: exact path or identity
base_sha: frozen before work
allowed_paths: exact list, or a bounded pattern
capabilities:
  read: scope
  write: scope
  exec: exact command classes
  network: denied, or named hosts and purpose
  external_tool: allow | ask | deny
evidence_required: candidate revision, diff, checks, counts, warnings
escalate_when: scope expands; secrets, network, external, or irreversible action is needed; state is unknown
human_merge_only: true
```

Keep it short enough that a human re-reads it before approving.

## 4. Result Receipt template

Written after each attempt. The Principal reconciles against it; the human reads it at the decision
point.

```yaml
outcome: succeeded | failed
artifact_or_commit: candidate revision, or the artifact path
files: the actual changed-path set
checks_run:
  - command: the exact command
    exit_code: integer or null
    collected: count, or not_applicable
    outcomes: passed / failed / skipped / xfail / xpass / error
observed_output: bounded excerpt of what the command actually printed
facts: what was directly observed
inferences: what was concluded but not directly observed, and why
uncertainties: known gaps, residual risk, and suggested follow-up
```

Use `unknown`, `not_applicable`, or an explicit warning when a value is unavailable. Never
synthesize a comfortable value from prose. Keep `facts` and `inferences` separate: a check that ran
is a fact; a claim that the change is correct is an inference.

## 5. Escalate

Stop and ask the human when:

- scope expands beyond `allowed_paths`;
- a secret, credential, network destination, external tool, or irreversible action is required;
- the repository state, the base revision, or the environment is not what the contract says;
- two workers or a worker and a check disagree and the Principal cannot resolve it from primary
  evidence;
- the work would require a new runtime, a new service, or an invented enforcement layer.

## 6. Stop conditions

Stop before merge. Present the exact candidate, the review, the check evidence, the limitations, and
the friction observed, then wait for a human decision. Do not merge, push, or publish unless the
human explicitly authorized that exact action.

## 7. Reference: a filled contract and receipt

The vertical-slice rehearsal exercised this loop end to end on a disposable fixture: the Principal
wrote the contract, one Builder produced a one-file candidate revision, an independent Reviewer ran
the same command on that exact candidate, the evidence was reconciled, every worker was released,
and the run stopped at the human decision with the candidate unmerged.

The Contract and Receipt below follow the same shape as that run. Values are illustrative.

```yaml
# Task Contract (filled)
intent: make the label normalizer collapse whitespace so callers get a single-line label
acceptance: the repository test command passes on the candidate revision
out_of_scope: any change to tests, configuration, or callers
repository: <absolute path to the target repository>
base_sha: <frozen base revision>
allowed_paths:
  - src/normalizer.py
capabilities:
  read: the repository worktree
  write: src/normalizer.py only
  exec: the repository test command
  network: denied
  external_tool: deny
evidence_required: candidate revision, diff, test command output and exit status
escalate_when: the fix needs a second file, a new dependency, or network access
human_merge_only: true
```

```yaml
# Result Receipt (filled)
outcome: succeeded
artifact_or_commit: <candidate revision>
files:
  - src/normalizer.py
checks_run:
  - command: <the repository test command, exactly as documented>
    exit_code: 0
    collected: 3
    outcomes: passed
observed_output: three tests reported ok, run summary printed, process exited 0
facts: the candidate changes one allowed file; the test command ran in the candidate worktree and exited 0
inferences: the change satisfies the stated acceptance because the documented command passed on the
  reviewed revision
uncertainties: the tests exercise one function only; no load, integration, or concurrency evidence;
  merge is a human decision that has not been made
```
