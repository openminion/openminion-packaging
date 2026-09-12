# Source-tree owner map

| Path | Ownership |
| --- | --- |
| `.github/workflows/prototype.yml` | Manual native prototype matrix and temporary artifact upload. |
| `packaging/build.py` | Canonical local and continuous-integration build implementation. |
| `packaging/locks/` | Hashed dependency inputs for each supported target. |
| `packaging/python-distributions.json` | Target Python runtime identities, paths, and checksums. |
| `tests/` | Build-contract and repository-structure tests. |
| `docs/` | Package-local operation, validation, and ownership guidance. |
| Root policy files | Contribution, compatibility, security, support, and release boundaries. |
| `dist/` | Ignored generated executables and build output. |
| `wheel/` | Ignored local wheel inputs. |

OpenMinion source, Desktop source, and sibling-package source are external
inputs or consumers. They are not owned or modified by this repository.
