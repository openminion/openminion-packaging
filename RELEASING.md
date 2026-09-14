# OpenMinion Standalone Packaging Releases

Status: prototype only
Last updated: 2026-09-13

This repository does not currently publish production artifacts. The manual
`Prototype` workflow produces unsigned temporary evidence only.

## Current prototype gate

Before reviewing a packaging change:

1. run `make check`,
2. verify the exact official OpenMinion wheel and dependency inputs,
3. run the manual workflow from the commit being reviewed,
4. require successful native builds, relocated-path launches, and two-pass
   offline runtime smoke checks for every target,
5. verify generated artifact metadata and checksums before upload,
6. record artifact hashes, sizes, toolchain identities, and timing evidence,
7. test the Windows artifact separately on the declared Windows 11 support
   floor.

## Production release gate

Production release work remains disabled until the project explicitly approves:

1. the packager and supported target set,
2. official dependency-wheel inputs,
3. release workflows separate from the prototype workflow,
4. macOS signing and notarization,
5. Windows signing,
6. checksum and provenance publication,
7. clean-machine install, upgrade, rollback, and uninstall evidence,
8. versioned installation guidance.

Never publish a source-built prototype dependency, an unsigned artifact, or a
binary produced from a dirty or unreviewed commit. Do not treat a successful CI
prototype as release authorization.
