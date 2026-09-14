# Certification readiness matrix

Status: private prototype

| Capability | Current evidence | State |
| --- | --- | --- |
| Repository documentation and governance | Root policies and package-local guides are present and structurally tested. | Ready |
| Local code-quality gate | Ruff, unit tests, and actionlint are grouped under `make check`. | Ready |
| Reproducible input contract | Wheel versions, hashes, dependency locks, and target runtime hashes are explicit. | Ready |
| Native macOS ARM64 prototype | OpenMinion 0.0.20 built and passed the native smoke checks. | Ready |
| Native Linux x86-64 prototype | OpenMinion 0.0.20 built and passed the native smoke checks. | Ready |
| Native Windows x86-64 prototype | OpenMinion 0.0.20 built and passed the native smoke checks. | Ready |
| Offline packaged-runtime smoke | Metadata, relocation, first/repeat runtime startup, state initialization, and schema-drift checks passed on every prototype target. | Ready |
| Official corrected Sophiagraph wheel | The current source-built wheel is a nonpublishing bridge. | Pending |
| Disposable Windows 11 acceptance | End-user launch and command flow have not been certified on a clean host. | Pending |
| Windows build-time budget | Prototype timing needs a release-owner decision. | Pending |
| Signing and notarization | No production signing or notarization path is implemented. | Pending |
| Install and lifecycle behavior | Install, upgrade, rollback, and uninstall contracts are not implemented. | Pending |
| Public release | Publication is not authorized and no supported download is claimed. | Blocked |

The native prototype establishes technical feasibility. Production release
work begins only after the pending dependency, clean-host, lifecycle, and
signing requirements receive explicit ownership and validation.

Current native evidence: [Prototype run 34801523320](https://github.com/openminion/openminion-packaging/actions/runs/34801523320) at commit `874dab1`.
