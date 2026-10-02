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

Resolve the exact URL and digest from the version-specific production PyPI JSON,
then download that immutable wheel into the ignored `wheel/` directory:

```bash
VERSION=0.0.28
SOURCE_COMMIT=01ef455f337422eefe81a3084c4352d85924e78d
WHEEL_URL=https://files.pythonhosted.org/packages/b8/e6/0c7b3c2ca7198d7e4fa0be6450934b61dcd37c4c643e0ff32c4e9b0ddc0e/openminion-0.0.28-py3-none-any.whl
WHEEL_SHA256=5ab92bf9d40535aa460383ef57b4aeabb9b17fb11edfde251cd9d919a4819ae2

python3.11 packaging/build.py verify-release \
  --version "$VERSION" \
  --source-commit "$SOURCE_COMMIT" \
  --wheel-url "$WHEEL_URL" \
  --wheel-sha256 "$WHEEL_SHA256"

python3.11 packaging/build.py download-wheel \
  --output-dir wheel \
  --version "$VERSION" \
  --source-commit "$SOURCE_COMMIT" \
  --wheel-url "$WHEEL_URL" \
  --wheel-sha256 "$WHEEL_SHA256"

python3.11 packaging/build.py lock \
  --target macos-arm64 \
  --wheel "wheel/openminion-$VERSION-py3-none-any.whl" \
  --wheel-origin pypi \
  --wheel-version "$VERSION" \
  --wheel-url "$WHEEL_URL" \
  --wheel-sha256 "$WHEEL_SHA256" \
  --source-commit "$SOURCE_COMMIT" \
  --check

python3.11 packaging/build.py build \
  --target macos-arm64 \
  --wheel "wheel/openminion-$VERSION-py3-none-any.whl" \
  --wheel-origin pypi \
  --wheel-version "$VERSION" \
  --wheel-url "$WHEEL_URL" \
  --wheel-sha256 "$WHEEL_SHA256" \
  --source-commit "$SOURCE_COMMIT"
```

Use `linux-x86_64` or `windows-x86_64` only on that native target. Successful
build output is written beneath the ignored `dist/` directory.

## Full target matrix

The manual GitHub `Runtime candidates` workflow runs the same builder and real
daemon smoke check on native macOS, Linux, and Windows runners. It stages
unsigned artifacts and aggregate candidate metadata in a private draft release.
That draft cannot be consumed by the public stable manifest.
