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

The optional reference validator may be used between acceptance and reconciliation:
`python3 tools/validate_evidence.py --contract <contract> --receipt <receipt>`.
This validator only checks JSON shape and declared evidence totals.
The required machine format for this repository is JSON, schema_version 1, not the YAML sketch below.
It is not an Orca runtime or agent CLI path, it executes no workflow commands, and it does not grant
approvals.

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
- The workflow validator is bounded: errors are deterministic and bounded in output, but it does not
  inspect command output truthfully, run commands, access Git/Orca internals, read declared evidence
  paths, access networks, judge correctness, or make merge decisions.

## 3. Task Contract template

One page, approved before dispatch. Prompt text expresses the contract; the tooling in use enforces
only the capabilities it actually exposes. Unknown or expanded action classes stop and escalate
rather than inheriting permission.

```yaml
# Human-readable intent sketch only.
intent: one sentence in the human's terms
base_sha: frozen before work
human_merge_only: true
allowed_paths: ["path/relative"]
evidence_required: ["candidate revision", "check evidence"]
minimum_total_collected: 1
schema_version: 1
```

```json
{
  "schema_version": 1,
  "intent": "string",
  "base_sha": "string",
  "allowed_paths": ["path/relative"],
  "evidence_required": ["candidate revision", "check evidence", "tests run"],
  "minimum_total_collected": 1,
  "human_merge_only": true
}
```

Keep it short enough that a human re-reads it before approving.

## 4. Result Receipt template

Written after each attempt. The Principal reconciles against it; the human reads it at the decision
point.

```yaml
schema_version: 1
outcome: succeeded | failed
artifact_or_commit: candidate revision, or the artifact path
files: the actual changed-path set
checks_run:
  - command: the exact command
    exit_code: integer or null
    collected: count, or not_applicable
    outcome: passed | failed | skipped | error | unknown
observed_output: bounded excerpt of the most important command output
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

```json
{
  "schema_version": 1,
  "intent": "keep the evidence validation profile deterministic and bounded for local checks",
  "base_sha": "9f89350b7385fb17c4a8991acfca3accb8d3070c",
  "allowed_paths": [
    "README.md",
    "tools/validate_evidence.py",
    "docs/WORKFLOW.md"
  ],
  "evidence_required": [
    "candidate revision",
    "check evidence",
    "tests run"
  ],
  "minimum_total_collected": 1,
  "human_merge_only": true
}
```

```json
{
  "schema_version": 1,
  "outcome": "succeeded",
  "artifact_or_commit": "0000000000000000000000000000000000000000",
  "files": [
    "README.md",
    "tools/validate_evidence.py",
    "docs/WORKFLOW.md"
  ],
  "checks_run": [
    {
      "command": "python3 tools/validate_evidence.py --contract examples/task-contract.json --receipt examples/result-receipt.json",
      "exit_code": 0,
      "collected": 1,
      "outcome": "passed"
    },
    {
      "command": "python3 -m unittest discover -s tests -v",
      "exit_code": 0,
      "collected": 1,
      "outcome": "passed"
    }
  ],
  "observed_output": "validator and tests reports passed",
  "facts": [
    "validator and tests run"
  ],
  "inferences": [
    "both inputs satisfied required shape"
  ],
  "uncertainties": [
    "no run evidence beyond this validator input pair"
  ]
}
```
