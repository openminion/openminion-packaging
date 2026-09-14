# Getting started

The prototype produces a standalone OpenMinion executable from verified wheel
inputs. Builds are native: run each target on its matching operating system and
architecture.

## Prerequisites

- Python 3.11
- `uv` 0.9.21
- Rust 1.89.0
- the exact official OpenMinion wheel
- the current prototype Sophiagraph dependency wheel

Ruff and actionlint are also required for the complete contributor gate.

## Validate the checkout

```bash
make check
```

## Build a native prototype

Place both verified wheels in the ignored `wheel/` directory. The filenames
below illustrate the currently pinned versions:

```bash
python3.11 packaging/build.py lock \
  --target macos-arm64 \
  --wheel wheel/openminion-0.0.20-py3-none-any.whl \
  --dependency-wheel wheel/sophiagraph-0.0.10-py3-none-any.whl \
  --check

python3.11 packaging/build.py build \
  --target macos-arm64 \
  --wheel wheel/openminion-0.0.20-py3-none-any.whl \
  --dependency-wheel wheel/sophiagraph-0.0.10-py3-none-any.whl
```

Use `linux-x86_64` or `windows-x86_64` only on that native target. Successful
build output is written beneath the ignored `dist/` directory.

## Full target matrix

The manual GitHub `Prototype` workflow runs the same builder on native macOS,
Linux, and Windows runners. It uploads unsigned temporary artifacts for
prototype verification and does not create a public release.
