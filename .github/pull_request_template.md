## Description
<!-- Provide a brief description of the intent and context of this change. -->

## Bounded Scope
- [ ] Changes are restricted to declared paths
- [ ] No external dependencies introduced (Python standard library only)

## Verification & Evidence
- [ ] `python3 -m unittest discover -s tests -p 'test_*.py' -v` passes
- [ ] `python3 tools/validate_evidence.py` passes on example and first-run pairs
- [ ] Negative fixture exits 1 with `ZERO_COLLECTED`
- [ ] Regression test added (if fixing a defect or schema bypass)

## Authority & Decision Boundary
<!-- Reconcile against Omega Zero authority model: human approval required before merge. -->
- [ ] Human acceptance required
