# OpenMinion Packaging Changelog

Status: active
Last updated: 2026-10-20

## Unreleased

- Refreshed official GitHub Actions pins to their current Node.js 24 releases
  and recorded the completed public-source and Git-history audit.
- Aligned public documentation with the current CI, candidate, development,
  and promotion workflow boundaries.
- Marked the tracked 0.0.29 locks and candidate run as historical qualification
  evidence rather than current-release readiness.
- Routed manual release inputs, matrix targets, and upstream job outputs through
  quoted environment variables; serialized manual release workflows; and added
  regression coverage against direct shell interpolation.
- Restricted downloads to approved HTTPS hosts and used Python's data filter
  when extracting pinned runtime archives.
- Added direct private-reporting and support links, completed post-conversion
  hosted CI verification, and recorded third-party
  redistribution evidence as an explicit binary-release gate.
- Prepared the repository for public source visibility without changing the
  candidate, signing, or stable-publication gates.
- Replaced repository-privacy assumptions with explicit restricted-draft and
  artifact-promotion boundaries.
- Documented the shared `dev` to `main` contribution path and public conversion
  safeguards.
- Added a read-only pull-request and branch quality workflow for the required
  repository check.
- Refreshed all native dependency locks for OpenMinion 0.0.29 after the
  reviewed SQLAlchemy 2.1.2 resolution and documented the required preflight
  lock gate for future source releases.

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
