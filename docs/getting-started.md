# Getting started

The candidate builder produces paired OpenMinion CLI and daemon executables
from one verified official wheel. Builds are native: run each target on its
matching operating system and architecture.

## Prerequisites

- Python 3.11
- `uv` 0.9.21
- Rust 1.89.0
- the exact official OpenMinion wheel

Ruff and actionlint are also required for the complete contributor gate.

## Validate the checkout

```bash
make check
```

## Build a native candidate

Download the exact pinned wheel into the ignored `wheel/` directory:

```bash
python3.11 packaging/build.py download-wheel --output-dir wheel

python3.11 packaging/build.py lock \
  --target macos-arm64 \
  --wheel wheel/openminion-0.0.23-py3-none-any.whl \
  --wheel-origin pypi \
  --check

python3.11 packaging/build.py build \
  --target macos-arm64 \
  --wheel wheel/openminion-0.0.23-py3-none-any.whl \
  --wheel-origin pypi
```

Use `linux-x86_64` or `windows-x86_64` only on that native target. Successful
build output is written beneath the ignored `dist/` directory.

## Full target matrix

The manual GitHub `Runtime candidates` workflow runs the same builder and real
daemon smoke check on native macOS, Linux, and Windows runners. It stages
unsigned artifacts and aggregate candidate metadata in a private draft release.
That draft cannot be consumed by the public stable manifest.
