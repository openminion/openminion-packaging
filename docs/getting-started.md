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
: "${VERSION:?set VERSION from the final release}"
: "${SOURCE_COMMIT:?set SOURCE_COMMIT to the full v$VERSION tag commit}"
: "${WHEEL_URL:?set WHEEL_URL from production PyPI metadata}"
: "${WHEEL_SHA256:?set WHEEL_SHA256 from production PyPI metadata}"

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
unsigned artifacts and aggregate candidate metadata in a draft release visible
only to repository maintainers. That draft cannot be consumed by the public
stable manifest.
