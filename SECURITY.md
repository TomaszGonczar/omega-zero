# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Security Invariants & Boundaries

Omega Zero defines an operating profile and authority contract:
- **Worktree Boundary**: Git worktrees separate filesystem state for cooperative agent processes. They are **not** an OS-level security sandbox.
- **Validator Scope**: The reference validator parses JSON payloads and verifies structure against schema rules. It does not execute arbitrary code or interact with external networks.

## Reporting a Vulnerability

If you discover a security vulnerability or authority bypass in Omega Zero:

1. Please do not open a public GitHub issue.
2. Report the vulnerability privately to Tomasz Gonczar via email at `tomaszgonczar96@gmail.com` or through GitHub Private Vulnerability Reporting.
3. Include a minimal reproduction case and the specific revision evaluated.

You will receive an acknowledgment within 48 hours.
