# Omega Zero

Omega Zero is a small operating profile for AI-assisted development on top of Orca. It defines who
holds authority, how bounded work is specified, what evidence a result must carry, and where the
work stops for a human decision. It is a set of rules and templates — not a runtime.

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
| `README.md` | Purpose, quick use, and honest limits |
| `.gitignore` | Local-only files |

No package, CLI, service, database, scheduler, dashboard, or CI pipeline lives here. The profile is
Markdown; the consuming repository owns its code, checks, and integration.

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

## Status

Honest status, as of this profile revision:

- The vertical-slice rehearsal of this loop was exercised and observed once, with limitations:
  contract, dispatch, separate-worktree candidate, independent review of the exact revision,
  evidence reconciliation, worker release, and a stop before merge. One run on a disposable fixture
  is evidence that the loop runs, not that it is production-ready.
- A real, public-safe run is pending.
- No auto-merge.
- No semantic-correctness claim: checks and reviews bound behavior and evidence, not meaning.
- No containment claim: nothing here isolates untrusted execution.
- No scaling claim: one Builder and one Reviewer is the default, and parallel mutation is untested.

## Limits

- A Git worktree separates source state for cooperative writers; it is not a security sandbox.
- Orca monitors process lifecycle, not semantic correctness.
- The Principal interprets intent, decomposes, judges evidence, and reconciles, but cannot
  self-approve and cannot merge.
- Skills are optional procedures a worker CLI may load; they are not agents and carry no authority.
