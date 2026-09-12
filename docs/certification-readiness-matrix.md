# Certification readiness matrix

Status: private prototype

| Capability | Current evidence | State |
| --- | --- | --- |
| Repository documentation and governance | Root policies and package-local guides are present and structurally tested. | Ready |
| Local code-quality gate | Ruff, unit tests, and actionlint are grouped under `make check`. | Ready |
| Reproducible input contract | Wheel versions, hashes, dependency locks, and target runtime hashes are explicit. | Ready |
| Native macOS ARM64 prototype | GitHub native-runner build and smoke test completed. | Ready |
| Native Linux x86-64 prototype | GitHub native-runner build and smoke test completed. | Ready |
| Native Windows x86-64 prototype | GitHub native-runner build and smoke test completed. | Ready |
| Official corrected Sophiagraph wheel | The current source-built wheel is a nonpublishing bridge. | Pending |
| Disposable Windows 11 acceptance | End-user launch and command flow have not been certified on a clean host. | Pending |
| Windows build-time budget | Prototype timing needs a release-owner decision. | Pending |
| Signing and notarization | No production signing or notarization path is implemented. | Pending |
| Install and lifecycle behavior | Install, upgrade, rollback, and uninstall contracts are not implemented. | Pending |
| Public release | Publication is not authorized and no supported download is claimed. | Blocked |

The native prototype establishes technical feasibility. Production release
work begins only after the pending dependency, clean-host, lifecycle, and
signing requirements receive explicit ownership and validation.
