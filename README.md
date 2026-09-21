# OpenMinion Standalone Packaging

Status: private release candidates; public binary promotion is gated

This repository builds target-specific OpenMinion command-line executables from
the official `openminion` wheel. It owns packaging and release mechanics only;
it never imports from or edits an OpenMinion source checkout.

No artifact produced here is a supported public download until it completes
native trust qualification and the central runtime-manifest publication flow.

## Start here

| Goal | Documentation |
| --- | --- |
| Prepare a local native build | [Getting started](docs/getting-started.md) |
| Understand repository ownership | [Source tree owner map](docs/source-tree-owner-map.md) |
| Run the validation gates | [Testing and validation](docs/testing-and-validation.md) |
| Review release readiness | [Certification readiness matrix](docs/certification-readiness-matrix.md) |
| Understand release restrictions | [Releasing](RELEASING.md) |

The complete documentation index is in [docs/README.md](docs/README.md).

## Current candidate targets

The native candidate targets are:

- `macos-arm64`
- `linux-x86_64`
- `windows-x86_64`

The build uses Python 3.11, `uv==0.9.21`, Rust `1.89.0`, and PyApp `0.29.0`.
Run it only on the matching native platform.

Download the pinned official wheel, then validate its target lock and build the
paired CLI and daemon executables:

```bash
python3.11 packaging/build.py download-wheel --output-dir wheel

python3.11 packaging/build.py lock \
  --target macos-arm64 \
  --wheel wheel/openminion-0.0.25-py3-none-any.whl \
  --wheel-origin pypi \
  --check

python3.11 packaging/build.py build \
  --target macos-arm64 \
  --wheel wheel/openminion-0.0.25-py3-none-any.whl \
  --wheel-origin pypi
```

The manual `Runtime candidates` workflow performs the same build and paired
runtime smoke test on all three native runners. It stores unsigned executables,
metadata, checksums, and one aggregate `candidate.json` in a private draft
release. That draft is qualification evidence only, not a public release.

## Repository boundary

- `packaging/` owns the single local and CI build implementation.
- `.github/workflows/runtime-candidates.yml` invokes that same implementation.
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
