# OpenMinion Standalone Packaging

Private build source for target-specific OpenMinion executables. The build
consumes the official `openminion` wheel and never imports from or edits an
OpenMinion source checkout.

## Build

Install Python 3.11, `uv==0.9.21`, Git, and Rust `1.89.0`, then run on the
matching native platform:

```bash
python3.11 packaging/build.py lock --target macos-arm64 \
  --wheel openminion-0.0.19-py3-none-any.whl --check
python3.11 packaging/build.py build --target macos-arm64 \
  --wheel openminion-0.0.19-py3-none-any.whl
```

Supported prototype targets are `macos-arm64`, `windows-x86_64`, and
`linux-x86_64`. Generated binaries and build evidence belong in `dist/` or CI
artifacts and are never committed.

The manual prototype workflow builds unsigned, non-release artifacts. It does
not publish them.

