# OpenMinion Packaging Changelog

Status: active
Last updated: 2026-09-21

## Unreleased

### Added

- Added the shared OpenMinion-family contributor, security, support, release,
  compatibility, and package-documentation foundation.
- Added one package-local `make check` entrypoint.

### Changed

- Updated native candidate inputs to the verified OpenMinion 0.0.26 PyPI wheel
  and protected-main source revision, including completed packaged Windows
  console-shutdown cleanup.
- Expanded the README into the repository landing page and corrected the local
  prototype build example to include the required dependency wheel.

## Prototype foundation - 2026-09-12

### Added

- Added one PyApp build implementation shared by local and native CI builds.
- Added verified OpenMinion wheel, CPython distribution, target-lock, and
  artifact metadata contracts.
- Added native macOS ARM64, Linux x86-64, and Windows x86-64 prototype jobs.
