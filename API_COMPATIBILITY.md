# OpenMinion Packaging Compatibility Policy

Owner: `openminion-packaging`
Status: candidate contract
Scope: build entrypoints, target identifiers, and emitted artifact metadata

## Supported operator surface

The repository currently exposes two maintained build commands:

```bash
python3.11 packaging/build.py lock --help
python3.11 packaging/build.py build --help
```

Release workflows also call package-local verification and metadata helpers.
Those helper commands are workflow implementation details rather than a stable
operator API.

The maintained target identifiers are `macos-arm64`, `linux-x86_64`, and
`windows-x86_64`. Their exact toolchain, Python distribution, and lock inputs
are repository-owned data.

## Stability

This is a pre-stable candidate pipeline, so the command and candidate metadata
contracts may change before the first stable binary publication.
Changes must update the README, package docs, tests, and changelog together.

Only command-line behavior and emitted artifact metadata are compatibility
surfaces. Functions inside `packaging/build.py`, workflow step names, tests,
temporary directories, and generated files are internal implementation details.

## Boundary

This repository does not define OpenMinion runtime APIs, configuration formats,
plugin contracts, or Desktop behavior. Those remain owned by their source
repositories. A successful candidate build is not a public support or release
claim.
