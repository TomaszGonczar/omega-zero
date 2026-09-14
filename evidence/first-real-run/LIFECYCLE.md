# Run lifecycle — reference evidence validator

Lifecycle record for the `B1` run of the Omega Zero loop, the run that produced
`tools/validate_evidence.py`. It records the observed sequence of stages, the authority that owned
each one, and the state reached at the end.

This record is written after the fact from durable state: Git history, the machine Task Contract and
Result Receipt in this directory, and the independent review evidence in `REVIEW.md`. Run-level
control-plane identifiers and machine-specific details are intentionally not reproduced here.

Like every artifact in this directory, this file is a sanitized public derivative of the run's own
records. Stage outcomes, the correction timeline, and the integration fact are reported as observed;
the wording is not the verbatim original, and the private originals remain outside this package.

## Revision map

| Name | Revision | Meaning |
|---|---|---|
| Frozen base | `9f89350b7385fb17c4a8991acfca3accb8d3070c` | The human-approved starting point of the run |
| Pre-fix candidate | `a1a226d52fa9517a34ec936e229df46790d8650b` | First candidate, carried the schema-version defect |
| Corrected candidate | `9d79b90df4af533403e01757f6a5ca99e739d0fa` | Corrected revision, reviewed and integrated |

The corrected candidate has a single parent equal to the frozen base and is the only commit above it.
The pre-fix candidate is a point-in-time revision of the run and is not an ancestor of the integrated
result.

## Stages

| # | Stage | Authority | Observed outcome |
|---|---|---|---|
| 1 | Intent, product boundary, and contract approval | Human | A bounded contract: one validator, nine allowed paths, no project dependencies, no merge |
| 2 | Base freeze | Human | The base revision above; one separate worktree, initially clean |
| 3 | Build | One Builder | One candidate commit over the base |
| 4 | Independent review 1 | Reviewer, separate worktree | `CHANGES_REQUIRED` — one P2 schema-version type-confusion defect |
| 5 | Correction | Builder | Strict integer guard at both check sites plus two regression tests |
| 6 | Independent review 2 | Reviewer, separate worktree | `ACCEPTABLE`, no blocking findings, bound to the corrected revision |
| 7 | Evidence packaging | Principal | Machine Task Contract and Result Receipt written for the run |
| 8 | Human decision | Human | Authorization to integrate the exact reviewed revision, locally only |
| 9 | Local integration | Human | Local fast-forward of the reviewed revision, then revalidation |

Every mutating stage had exactly one writer. Review stages produced no mutation of the candidate; the
review worktree was read-only by contract.

## Observed state per stage

- **Build.** Changed-path set equalled the nine contract-allowed paths. The operating contract file
  was not modified.
- **Review 1.** The reviewer reproduced the boolean bypass on the exact revision under review, then
  required changes. The coordinating principal repeated the reproduction independently rather than
  accepting the report.
- **Correction.** Two regression tests were verified to fail against the pre-fix revision and pass
  against the corrected one, so the tests genuinely discriminate the fix.
- **Review 2.** The reviewer reran the acceptance checks on the corrected revision: 17 tests collected
  and passed, the example pair exited 0 with `valid: true`, the zero-collected fixture exited 1 with
  `ZERO_COLLECTED`, repeated runs were byte-identical, and the validator code was confirmed to be
  standard-library only, with no execution, network, Git, or control-plane access in the code itself.
- **Decision.** The authorization was scoped to one exact local integration of the reviewed revision.
  It did not authorize a remote, a push, or publication.
- **Integration.** The reviewed revision was fast-forwarded into the local main line, so local main
  then equalled `9d79b90df4af533403e01757f6a5ca99e739d0fa`. Post-integration revalidation reran the 17
  tests successfully, and the integrated validator validated the machine contract and receipt pair
  with exit 0 and `valid: true`.

## Temporal truth of the evidence in this directory

`result-receipt.json` is a sanitized public derivative of the run's local point-in-time worker record,
written **before** integration. It reports the candidate as unmerged, and that was true of the source
record when it was written; the derivative preserves that temporal fact. The private original remains
outside this public package and is not reproduced here verbatim. The derivative carries an explicit
provenance block stating this, and it is not edited to imply that the later integration had already
happened.

Two honest statements therefore hold at once, at different times:

- At the time the source receipt was written, the candidate was unmerged and unpushed.
- After the human decision, the reviewed revision was integrated locally.

**Current integrated state.** Local main equals `9d79b90df4af533403e01757f6a5ca99e739d0fa`. No remote
exists for this line of work, nothing has been pushed, and nothing has been published.

## Anomalies recorded, not hidden

- **Placement misfire.** An early worker placement inherited an active context instead of the intended
  directory and created a worktree under the wrong repository. It wrote no commit and left no tracked
  change in the intended repository. The lesson recorded at the time: process working directory is not
  placement evidence; the target must be resolved explicitly.
- **Provider substitution.** The originally named reviewer provider reached an account usage limit
  during the correction. The human changed the worker policy, and a different model completed the
  correction and gave the second review. The two reviews therefore came from different models, and
  model diversity is not itself a correctness claim.
- **Retained session.** One abandoned worker session was left retained because the control plane marked
  it user-owned after an interactive usage prompt. It was fenced from the remaining work and never
  reused. It is not counted as a completed stage.
- **Recovery report corrected.** A fresh worker process given only durable state reconstructed the run
  and recovered the revision, path set, evidence, and correction timeline, but also asserted a
  control-plane defect that reconciliation disproved. The claim was withdrawn. Durable state enables
  recovery; it does not guarantee a correct recovery.
- **Ignored build artifacts.** The checks create ignored interpreter cache directories. Tracked and
  non-ignored state stayed clean throughout; the filesystem was not byte-for-byte frozen.

## Boundaries that held

- No project dependency was installed at any stage, and the repository's own checks never contacted a
  network origin, package index, or remote. The work still ran inside vendor tooling that has its own
  network behaviour, so this is a statement about the repository's checks, not about every process
  involved.
- No remote was created, nothing was pushed, and nothing was published.
- No merge occurred except the one local fast-forward explicitly authorized by the human.
- No containment claim is made: the worktrees used here separate source state for cooperative writers
  and are not sandboxes.
- No claim is made that the validator proves truth, semantic correctness, approval, or merge. It
  checks the shape of supplied JSON and the counts those inputs declare.

## Unobserved at this point

- The repository-owned run scripts that the continuous-integration workflow invokes were executed
  locally. The workflow itself was never run: `actions/checkout`, `actions/setup-python`, and
  GitHub-hosted runner behavior were not executed or observed locally, and no result from a hosted
  run exists.
- No second platform and no second interpreter version beyond the single local environment were
  exercised during the run.
- Parallel mutation of one worktree was never tested, so no scaling claim is available.
