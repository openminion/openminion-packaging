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

Before a native candidate dispatch, run `lock --check` for macOS ARM64, Linux
x86-64, and Windows x86-64 against the exact production wheel. A mismatch means
the reviewed dependency closure is stale; refresh the locks in a packaging PR,
run the complete local gate, merge it, and only then rerun the candidate matrix.
The workflow must not resolve and accept new dependency versions on its own.

## Complete local gate

```bash
make check
```

This proves formatting, lint, unit contracts, and workflow syntax. It does not
prove that an executable runs correctly on every target.

The read-only `CI` workflow runs this same gate for pull requests and pushes to
`dev` and `main`. Its `Repository check` job is the required protected-branch
status check.

## Native candidate evidence

Use the manual GitHub `Runtime candidates` workflow for the three-target
matrix. A successful run proves that the pinned inputs build on native GitHub
runners and that each paired candidate staged in its restricted draft release:

- matches its generated metadata and checksum,
- exposes the exact expected CLI version,
- starts the packaged daemon as a foreground child with isolated state,
- serves a healthy response from the real `/health` endpoint,
- stops through the supported signal and removes its PID file, and
- appears in one aggregate cross-platform `candidate.json` identity.

The following remain separate from a green prototype workflow:

- disposable Windows 11 acceptance
- signing and notarization
- install, upgrade, rollback, and uninstall behavior
- signed stable runtime release and protected manifest publication

Record only the evidence actually run. Do not infer public availability from a
local build or restricted draft release.
