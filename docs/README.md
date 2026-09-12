# Packaging documentation

This documentation covers the private OpenMinion standalone-packaging
prototype. It describes this repository's build contract, validation, and
release boundary without duplicating OpenMinion runtime documentation.

## Guides

| Document | Purpose |
| --- | --- |
| [Getting started](getting-started.md) | Prepare and run a native prototype build. |
| [Engineering patterns](engineering-patterns.md) | Follow the repository's implementation constraints. |
| [Code-quality enforcement](code-quality-enforcement.md) | Understand the local and continuous-integration checks. |
| [Testing and validation](testing-and-validation.md) | Prove changes at the appropriate level. |
| [Source-tree owner map](source-tree-owner-map.md) | Find the owner for each repository surface. |
| [Certification readiness matrix](certification-readiness-matrix.md) | See what the prototype proves and what remains. |

Repository-wide policies and project information live at the root:

- [README](../README.md)
- [API compatibility](../API_COMPATIBILITY.md)
- [Code quality](../CODE_QUALITY.md)
- [Contributing](../CONTRIBUTING.md)
- [Releasing](../RELEASING.md)
- [Security](../SECURITY.md)
- [Support](../SUPPORT.md)

## Boundary

This repository owns standalone CLI packaging. OpenMinion runtime behavior,
Desktop application packaging, provider configuration, and public artifact
publication remain with their respective owners.
