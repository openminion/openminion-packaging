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
