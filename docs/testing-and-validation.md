# Testing and validation

Choose the smallest gate that proves the change, then run the complete local
gate before committing.

## Focused checks

Run the build-contract tests after changing the builder, locks, metadata, or
documentation structure:

```bash
python3.11 -m unittest discover -s tests -p 'test_*.py'
```

Inspect the command surface after changing arguments or operator guidance:

```bash
python3.11 packaging/build.py --help
```

## Complete local gate

```bash
make check
```

This proves formatting, lint, unit contracts, and workflow syntax. It does not
prove that an executable runs correctly on every target.

## Native prototype evidence

Use the manual GitHub `Prototype` workflow for the three-target matrix. A
successful run proves that the pinned inputs build on native GitHub runners and
that the temporary artifacts pass the workflow smoke checks.

The following remain separate from a green prototype workflow:

- disposable Windows 11 acceptance
- signing and notarization
- install, upgrade, rollback, and uninstall behavior
- public release publication

Record only the evidence actually run. Do not infer public availability from a
local build or uploaded workflow artifact.
