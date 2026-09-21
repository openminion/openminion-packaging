# Engineering patterns

Keep this repository small and reproducible. Packaging mechanics belong here;
OpenMinion behavior does not.

## One build owner

`packaging/build.py` is the implementation used locally and in continuous
integration. Workflows pass inputs to it rather than reimplementing build
steps.

## Verified immutable inputs

Builds consume explicit wheel files, versions, and SHA-256 identities. Target
metadata lives in `packaging/python-distributions.json`; dependency resolution
is frozen in `packaging/locks/`.

## Native builds

Each executable is built on its target platform. Do not add cross-compilation
fallbacks or silently substitute a different target.

## Clear ownership boundaries

- Do not import from or modify an OpenMinion source checkout.
- Do not add OpenMinion runtime behavior to the packager.
- Keep Desktop application packaging out of this repository.
- Keep generated wheels, runtimes, and executables out of Git.

## Direct implementation

Prefer explicit data and small functions over wrappers, registries, retry
layers, or speculative compatibility paths. Add an abstraction only when the
current build contract needs it.

## Truthful lifecycle labels

Candidate artifacts are unsigned and temporary. Do not describe them as
certified, released, or supported until the corresponding release gates exist
and pass.
