# OpenMinion Standalone Packaging

Status: public-source conversion prepared; hosted verification pending; stable
binary promotion remains gated

This repository builds target-specific OpenMinion command-line executables from
the official `openminion` wheel. It owns packaging and release mechanics only;
it never imports from or edits an OpenMinion source checkout.

The repository source may be public. Build visibility does not make an artifact
a supported download: stable binaries still require native trust qualification
and the central runtime-manifest publication flow.

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

The tracked target locks are the last reviewed `0.0.29` qualification inputs,
not an alias for the latest PyPI release. A different source release is
intentionally rejected until a packaging PR refreshes and reviews every target
lock from that release's exact wheel.

Resolve the exact released wheel identity, then validate its target lock and
build the paired CLI and daemon executables:

```bash
: "${VERSION:?set VERSION from the final release}"
: "${SOURCE_COMMIT:?set SOURCE_COMMIT to the full v$VERSION tag commit}"
: "${WHEEL_URL:?set WHEEL_URL from production PyPI metadata}"
: "${WHEEL_SHA256:?set WHEEL_SHA256 from production PyPI metadata}"

python3.11 packaging/build.py download-wheel \
  --output-dir wheel \
  --version "$VERSION" \
  --source-commit "$SOURCE_COMMIT" \
  --wheel-url "$WHEEL_URL" \
  --wheel-sha256 "$WHEEL_SHA256"

python3.11 packaging/build.py lock \
  --target macos-arm64 \
  --wheel "wheel/openminion-$VERSION-py3-none-any.whl" \
  --wheel-version "$VERSION" \
  --wheel-url "$WHEEL_URL" \
  --wheel-sha256 "$WHEEL_SHA256" \
  --source-commit "$SOURCE_COMMIT" \
  --check

python3.11 packaging/build.py build \
  --target macos-arm64 \
  --wheel "wheel/openminion-$VERSION-py3-none-any.whl" \
  --wheel-version "$VERSION" \
  --wheel-url "$WHEEL_URL" \
  --wheel-sha256 "$WHEEL_SHA256" \
  --source-commit "$SOURCE_COMMIT"
```

The `Runtime candidates` workflow accepts the exact final runtime version and
source commit from the OpenMinion release. It refuses requests that do not match
this repository's reviewed wheel and source pins, then performs the same build
and paired runtime smoke test on all three native runners. It stores unsigned
executables, metadata, checksums, and one aggregate `candidate.json` in a draft
release restricted to repository maintainers. That draft is qualification
evidence only, not a supported public release.

## Repository boundary

- `packaging/` owns the single local and CI build implementation.
- `.github/workflows/` owns read-only CI, candidate builds, unsigned development
  builds, and the separately gated promotion workflow.
- `tests/` protects input, lock, platform, and metadata contracts.
- `docs/` explains package-local operation and evidence boundaries.
- `dist/` and `wheel/` are generated and never committed.

OpenMinion runtime behavior, Desktop packaging, provider configuration, and
public release publication are outside this repository.

## Public repository boundary

Public visibility exposes build code, tests, documentation, and workflow logs.
It does not expose GitHub environment secrets or publish draft Releases. The
manual workflows remain restricted to `main`, and stable publication remains a
separate reviewed operation. See [Releasing](RELEASING.md) for the conversion
and post-conversion checklist.

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
