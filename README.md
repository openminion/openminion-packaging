# OpenMinion Standalone Packaging

Status: private prototype

This repository builds target-specific OpenMinion command-line executables from
the official `openminion` wheel. It owns packaging and release mechanics only;
it never imports from or edits an OpenMinion source checkout.

No artifact produced here is currently a supported public download.

## Start here

| Goal | Documentation |
| --- | --- |
| Prepare a local native build | [Getting started](docs/getting-started.md) |
| Understand repository ownership | [Source tree owner map](docs/source-tree-owner-map.md) |
| Run the validation gates | [Testing and validation](docs/testing-and-validation.md) |
| Review prototype readiness | [Certification readiness matrix](docs/certification-readiness-matrix.md) |
| Understand release restrictions | [Releasing](RELEASING.md) |

The complete documentation index is in [docs/README.md](docs/README.md).

## Current prototype

The native prototype targets are:

- `macos-arm64`
- `linux-x86_64`
- `windows-x86_64`

The build uses Python 3.11, `uv==0.9.21`, Rust `1.89.0`, and PyApp `0.29.0`.
Run it only on the matching native platform.

Place the exact OpenMinion and prototype dependency wheels in `wheel/`, then
run:

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

The manual `Prototype` workflow obtains and verifies these inputs, builds on
all three native runners, and uploads unsigned temporary artifacts. It does not
publish releases.

The source-built Sophiagraph wheel is a nonpublishing bridge for a Windows
filename correction. Releasable OpenMinion artifacts must use the corrected
official dependency wheel after that package completes its own release process.

## Repository boundary

- `packaging/` owns the single local and CI build implementation.
- `.github/workflows/prototype.yml` invokes that same implementation.
- `tests/` protects input, lock, platform, and metadata contracts.
- `docs/` explains package-local operation and evidence boundaries.
- `dist/` and `wheel/` are generated and never committed.

OpenMinion runtime behavior, Desktop packaging, provider configuration, and
public release publication are outside this repository.

## Development

Run the standard repository gate before submitting changes:

```bash
make check
```

See [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_QUALITY.md](CODE_QUALITY.md), and
[SECURITY.md](SECURITY.md) for the shared OpenMinion-family expectations.

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) and
[NOTICE](NOTICE).
