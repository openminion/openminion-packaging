# OpenMinion Standalone Packaging Releases

Status: candidate production enabled; stable promotion remains gated
Last updated: 2026-09-20

This repository produces private native release candidates. The manual
`Runtime candidates` workflow builds paired `openminion` and `openminiond`
executables from the exact official OpenMinion wheel, verifies their bytes,
starts the real daemon, probes `/health`, and records one cross-platform
candidate identity in a private draft release.

## Private Candidate Metadata

After verifying an artifact, the existing builder can describe it for private
native qualification:

```bash
python3.11 packaging/build.py candidate-manifest --help
```

Supply its exact source commit, release identity, fixed private HTTPS artifact
URLs, proposed Desktop bounds and native OS baseline. Linux also requires the
proposed glibc minimum. The output always has `promotion_status: candidate`;
proposed bounds are not certification. `merge-candidates` combines the three
native records without changing that status.

## Candidate gate

Before reviewing a packaging change:

1. run `make check`,
2. verify the exact official OpenMinion wheel and all target locks,
3. run the manual workflow from the commit being reviewed,
4. require successful paired native builds and a real foreground-daemon health
   and graceful-shutdown smoke check for every target,
5. verify generated artifact metadata and checksums before upload,
6. record artifact hashes, sizes, toolchain identities, and timing evidence,
7. retain the aggregate `candidate.json` and per-target native evidence.

## Production release gate

Stable binary promotion remains disabled until all of these are complete:

1. the packager and supported target set,
2. macOS signing and notarization,
3. Windows signing,
4. clean-host native verification with recorded verification IDs,
5. Desktop install, activation, restart, reply-continuity, rollback, and
   uninstall evidence for explicit compatibility bounds,
6. an immutable public `openminion/runtime` GitHub Release containing the exact
   executables, `candidate.json`, and `verification.json`,
7. central verification of those public bytes followed by the protected
   runtime-metadata PR and human merge commit.

Never publish an unsigned artifact or a binary produced from a dirty or
unreviewed commit. A successful candidate workflow is necessary evidence, not
release authorization.
