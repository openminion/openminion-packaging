# Contributing to OpenMinion Packaging

Thanks for contributing.

## Before changing the repository

Read:

1. [Engineering patterns](docs/engineering-patterns.md)
2. [Code quality enforcement](docs/code-quality-enforcement.md)
3. [Source tree owner map](docs/source-tree-owner-map.md)
4. [Testing and validation](docs/testing-and-validation.md)
5. [Code quality](CODE_QUALITY.md)

## Development flow

1. Make one focused change under the existing owner.
2. Add or update a behavior-focused test.
3. Update public repository docs when an operator contract changes.
4. Run `make check`.
5. Run the native candidate workflow when build behavior or pinned inputs
   change.
6. Include exact validation results in the pull request.

Run `make release-check` when changing packaging, workflows, or public
repository guidance.

Do not commit `dist/`, `wheel/`, extracted runtimes, logs, credentials, signing
material, or scratch evidence.

Use commit subjects in the form `<type>(<scope>): <summary>`. Suitable types
include `build`, `docs`, `fix`, `refactor`, `test`, and `chore`.

## Pull requests

Use a short title, a flat bullet summary, and a plain `Validation` section with
the exact commands and results. Keep unrelated refactors out of the change.
Open pull requests against `dev`; promote reviewed `dev` changes to `main`
through a separate release or repository-maintenance pull request.

## Security and conduct

Report security issues through [SECURITY.md](SECURITY.md), and follow
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

By contributing, you agree that your contribution is licensed under Apache
License 2.0 and that you have the right to submit it.
