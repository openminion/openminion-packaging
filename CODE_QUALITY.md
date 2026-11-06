# OpenMinion Packaging Code Quality

This repository follows the same practical quality baseline as the other
OpenMinion-family repositories.

## Rules

1. Keep one build implementation in `packaging/build.py`; workflows call it
   rather than duplicating build behavior.
2. Keep wheel, Python, lock, toolchain, and artifact identities explicit and
   hash verified.
3. Build each artifact on its matching native platform.
4. Keep generated wheels, executables, runtimes, and evidence out of Git.
5. Do not add OpenMinion runtime compatibility branches to solve packaging
   problems.
6. Prefer direct code over wrappers, registries, retries, or fallback systems
   without a demonstrated requirement.
7. Update tests and documentation with every operator-facing contract change.

## Required validation

Run:

```bash
make check
```

For build behavior changes, also run the manual native `Runtime candidates`
workflow.
Passing local checks is not evidence that another operating-system artifact
builds or launches.

## Comment and docstring review

This rule applies to every contributor and coding agent, including tests and
scripts. Let clear names, types and direct control flow explain ordinary steps.
Review every added or changed comment and docstring in the final diff; remove
obvious restatements, decorative banners and duplicated walkthroughs. Keep one
concise explanation at the owner when a constraint is not obvious.

Preserve public API and model-facing descriptions, required notices/directives,
and useful safety, compatibility and regression-oracle rationale. Keep short
factual module explainers; move longer design/history narratives to docs.
Passing automated checks does not replace this review, and there is no comment
quota. Check current source and existing reports before filing cleanup debt;
keep unrelated cleanup out of a feature PR.

## Minimum usable code

These rules apply to maintainers, external contributors and coding agents, in
new work and cleanup of merged code. Start with actual callers, supported inputs
and concrete failure paths. Use the existing owner and a direct implementation;
add a helper or abstraction only when current callers need it.

Do not add speculative frameworks, unused modes or extension points,
pass-through wrappers, duplicate validation, silent defaults, blanket exception
handling, or retries that hide failures. Validate at the boundary that owns the
contract instead of repeatedly normalizing internal values. A retry needs a
specific transient failure, a bound and safe repeat behavior. Preserve necessary
trust-boundary checks, permissions, compatibility, persistence/replay and cleanup.

Keep build behavior in the existing packaging owner. Preserve pinned inputs,
hashes, artifact verification and explicit subprocess failures.

## Review and cleanup evidence

Review the complete final diff and every new delta for simplicity and the
[comment and docstring rules](#comment-and-docstring-review). Record the exact
reviewed head, checked callers, supported failure cases, findings and disposition
in the PR or linked review evidence. Passing automated checks does not replace
this review. Block approval or merge while a substantiated finding remains;
request the smaller existing-owner change when it satisfies the same contract.
Validate the current integration with the target branch and require all required
hosted checks on the exact head before merging. Never relax a gate to land cleanup.

For merged work, first verify that the code still exists on the current
development branch. Reuse existing findings and respect active ownership; record
obsolete findings without reopening old PRs, duplicating issues or taking over
another contributor's branch. Do not label all historical code clean from a
partial review.

A broad cleanup starts with a fresh file inventory at a recorded revision. Keep
source, tests and scripts separate, give each claimed file a trim, keep or explicit
defer disposition, and work in bounded tranches. Record callers, rationale,
validation and remaining work after each tranche; deferred files remain open.
Refresh evidence if the tree changes during validation. Record before/after LOC
for source cleanup and retain a simplification only when it reduces code and
improves readability while preserving the contract. Review the changed files
again after authoring; this is not proof of a package-wide sweep.

Preserve test assertions and negative controls. Do not introduce skips, expected
failures, extra waits or retries to conceal a regression. Preserve script output,
exit behavior and operator clarity. Run the repository's documented gates and
report local, hosted, installed-package and live-system evidence separately.
