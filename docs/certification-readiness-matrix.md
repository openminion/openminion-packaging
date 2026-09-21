# Certification readiness matrix

Status: private native candidates; stable binary release not yet certified

| Capability | Current evidence | State |
| --- | --- | --- |
| Repository documentation and governance | Root policies and package-local guides are present and structurally tested. | Ready |
| Local code-quality gate | Ruff, unit tests, and actionlint are grouped under `make check`. | Ready |
| Reproducible input contract | Wheel versions, hashes, dependency locks, and target runtime hashes are explicit. | Ready |
| Native macOS ARM64 candidate | OpenMinion 0.0.25 paired CLI/daemon build and real daemon health/shutdown smoke are implemented. | Ready for CI rerun |
| Native Linux x86-64 candidate | OpenMinion 0.0.25 paired CLI/daemon build and real daemon health/shutdown smoke are implemented. | Ready for CI rerun |
| Native Windows x86-64 candidate | OpenMinion 0.0.25 paired CLI/daemon build and real daemon health/shutdown smoke are implemented. | Ready for CI rerun |
| Official dependency closure | All target locks resolve the official OpenMinion 0.0.25 wheel and official published dependencies. | Ready |
| Cross-platform candidate identity | Per-target records merge into one binary candidate without duplicate targets. | Ready |
| Disposable Windows 11 acceptance | End-user launch and command flow have not been certified on a clean host. | Pending |
| Windows build-time budget | Prototype timing needs a release-owner decision. | Pending |
| Signing and notarization | No production signing or notarization path is implemented. | Pending |
| Desktop staging behavior | Paired executable download, digest verification, pending activation, pause and pin contracts are implemented in Desktop. | Implemented; native acceptance pending |
| Immutable public release | Public `openminion/runtime` release bytes and final native verification evidence do not yet exist. | Pending |
| Stable manifest publication | Central verification and protected metadata-PR support are implemented; no binary record may publish before the immutable release gate. | Gated |
| Public release | Publication is not authorized and no supported binary download is claimed. | Blocked |

The candidate path establishes reproducible build and consumption mechanics.
Stable release still requires signing, clean-host and Desktop lifecycle
acceptance, an immutable public runtime release, and protected manifest merge.

Historical prototype evidence: [run 34801523320](https://github.com/openminion/openminion-packaging/actions/runs/34801523320) at commit `874dab1`. It is not evidence for the new paired 0.0.23 candidate flow.
