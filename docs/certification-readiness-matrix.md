# Certification readiness matrix

Status: historical 0.0.29 qualification snapshot; current stable binary release
not certified

| Capability | Current evidence | State |
| --- | --- | --- |
| Public source visibility | Protected `main` and `dev`, read-only default Actions permissions, private vulnerability reporting, secret scanning with push protection, and the 2026-10-20 tracked-history audit are active. | Ready |
| Repository documentation and governance | Root policies and package-local guides are present and structurally tested. | Ready |
| Local code-quality gate | Ruff, unit tests, and actionlint are grouped under `make check`. | Ready |
| Reproducible input contract | Wheel versions, hashes, dependency locks, and target runtime hashes are explicit. | Ready |
| Native macOS ARM64 candidate | Historical OpenMinion 0.0.29 paired executables built successfully; signing and later smoke stages were blocked because the Apple signing and notarization secrets were not configured. | Historical; signing blocked |
| Native Linux x86-64 candidate | Historical OpenMinion 0.0.29 paired executables passed the offline CLI/daemon smoke and staged candidate evidence. | Historical pass |
| Native Windows x86-64 candidate | Historical OpenMinion 0.0.29 paired executables built successfully; signing and later smoke stages were blocked because the Windows certificate, password, and timestamp URL were not configured. | Historical; signing blocked |
| Official dependency closure | The tracked target locks reproduce from the official OpenMinion 0.0.29 wheel after the reviewed SQLAlchemy 2.1.2 refresh. | Historical pass |
| Third-party redistribution evidence | Artifact metadata records installed package names, versions, and declared licenses; a reviewed consolidated notice/SBOM has not been published with the binaries. | Pending |
| Cross-platform candidate identity | Aggregation remains fail-closed until all three signed target jobs and fresh-host verification jobs pass. | Blocked on signing |
| Disposable Windows 11 acceptance | End-user launch and command flow have not been certified on a clean host. | Pending |
| Windows build-time budget | Prototype timing needs a release-owner decision. | Pending |
| Signing and notarization | Fail-closed macOS signing/notarization and Windows Authenticode steps are implemented; their protected-environment credentials are not configured. | Blocked on credentials |
| Desktop staging behavior | Paired executable download, digest verification, pending activation, pause and pin contracts are implemented in Desktop. | Implemented; native acceptance pending |
| Immutable public release | Normal public `openminion/runtime` GitHub Releases with `-dev-` tags contain explicitly unsigned development bytes; no signed stable release with final native verification exists. | Development only; stable pending |
| Stable manifest publication | Central verification and protected metadata-PR support are implemented; no binary record may publish before the immutable release gate. | Gated |
| Public release | Publication is not authorized and no supported binary download is claimed. | Blocked |

The candidate path establishes reproducible build and consumption mechanics.
It does not establish compatibility with a newer PyPI release. Each new source
release requires a reviewed target-lock refresh before either candidate
workflow can pass. Stable release still requires signing, clean-host and
Desktop lifecycle acceptance, an immutable public runtime release, and
protected manifest merge.

Latest recorded packaging evidence: [candidate run 36984135141](https://github.com/openminion/openminion-packaging/actions/runs/36984135141) at packaging commit `066e98f`. The run proves the historical 0.0.29 locks and Linux candidate path; it does not certify a newer source release, macOS, Windows, aggregate, public runtime, or Desktop upgrade acceptance.

Historical prototype evidence: [run 34801523320](https://github.com/openminion/openminion-packaging/actions/runs/34801523320) at commit `874dab1`.
