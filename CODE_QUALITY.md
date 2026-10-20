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
