# Certification readiness matrix

Status: 0.0.29 native qualification in progress; stable binary release not certified

| Capability | Current evidence | State |
| --- | --- | --- |
| Repository documentation and governance | Root policies and package-local guides are present and structurally tested. | Ready |
| Local code-quality gate | Ruff, unit tests, and actionlint are grouped under `make check`. | Ready |
| Reproducible input contract | Wheel versions, hashes, dependency locks, and target runtime hashes are explicit. | Ready |
| Native macOS ARM64 candidate | OpenMinion 0.0.29 paired executables build successfully; signing and the later smoke stages are blocked because the Apple signing and notarization secrets are not configured. | Blocked on credentials |
| Native Linux x86-64 candidate | OpenMinion 0.0.29 paired executables pass the offline CLI/daemon smoke and stage candidate evidence. | Ready |
| Native Windows x86-64 candidate | OpenMinion 0.0.29 paired executables build successfully; signing and the later smoke stages are blocked because the Windows certificate, password, and timestamp URL are not configured. | Blocked on credentials |
| Official dependency closure | All target locks reproduce from the official OpenMinion 0.0.29 wheel after the reviewed SQLAlchemy 2.1.2 refresh. | Ready |
| Cross-platform candidate identity | Aggregation remains fail-closed until all three signed target jobs and fresh-host verification jobs pass. | Blocked on signing |
| Disposable Windows 11 acceptance | End-user launch and command flow have not been certified on a clean host. | Pending |
| Windows build-time budget | Prototype timing needs a release-owner decision. | Pending |
| Signing and notarization | Fail-closed macOS signing/notarization and Windows Authenticode steps are implemented; their protected-environment credentials are not configured. | Blocked on credentials |
| Desktop staging behavior | Paired executable download, digest verification, pending activation, pause and pin contracts are implemented in Desktop. | Implemented; native acceptance pending |
| Immutable public release | Public `openminion/runtime` release bytes and final native verification evidence do not yet exist. | Pending |
| Stable manifest publication | Central verification and protected metadata-PR support are implemented; no binary record may publish before the immutable release gate. | Gated |
| Public release | Publication is not authorized and no supported binary download is claimed. | Blocked |

The candidate path establishes reproducible build and consumption mechanics.
Stable release still requires signing, clean-host and Desktop lifecycle
acceptance, an immutable public runtime release, and protected manifest merge.

Current 0.0.29 evidence: [candidate run 36984135141](https://github.com/openminion/openminion-packaging/actions/runs/36984135141) at packaging commit `066e98f`. The run proves the refreshed locks and Linux candidate path; it does not certify macOS, Windows, aggregate, public runtime, or Desktop upgrade acceptance.

Historical prototype evidence: [run 34801523320](https://github.com/openminion/openminion-packaging/actions/runs/34801523320) at commit `874dab1`.
