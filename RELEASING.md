# OpenMinion Standalone Packaging Releases

Status: candidate production enabled; stable promotion remains gated
Last updated: 2026-10-01

This repository produces private native release candidates. The
`Runtime candidates` workflow builds paired `openminion` and `openminiond`
executables from the exact official OpenMinion wheel, verifies their bytes,
starts the real daemon, probes `/health`, and records one cross-platform
candidate identity in a private draft release.

Every request supplies the final three-part runtime version, full source commit,
official production wheel URL, and SHA-256. The workflow independently checks
those values against the immutable source tag and version-specific PyPI
metadata before downloading or building. A successful final source release can
request this private candidate automatically; that request grants no
stable-publication authority.

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

Before publishing the final source release, generate every target lock from the
final-version TestPyPI wheel, review the dependency diff, and land the locks on
packaging `main`. The production wheel must have the same core requirements as
that accepted wheel. After PyPI publication, verify all three locks again with
the exact production wheel before dispatching `Runtime candidates`. This keeps
dependency resolution reviewable without silently resolving new versions in a
release job.

For each target, run:

```bash
python3.11 packaging/build.py lock \
  --target <target> \
  --wheel <verified-wheel> \
  --wheel-version <version> \
  --wheel-url <official-wheel-url> \
  --wheel-sha256 <wheel-sha256> \
  --source-commit <source-commit>
```

Repeat with `--check` after review and for the production wheel. A lock mismatch
blocks native candidate publication and requires a packaging PR; do not remove
the check or regenerate locks inside the candidate workflow.

Before reviewing a packaging change:

1. run `make check`,
2. verify the exact official OpenMinion wheel, source commit, and all target locks,
3. run the workflow from the commit being reviewed with the exact final version,
   source commit, production wheel URL, and SHA-256,
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

## Signed promotion sequence

1. Configure the `runtime-signing` secret environment with the Apple
   certificate, identity, notarization credentials, Windows signing certificate
   and trusted timestamp URL named in `runtime-candidates.yml`.
2. Require the candidate matrix and fresh-runner verification matrix to pass.
   `candidate.json` describes the final signed bytes and `verification.json`
   carries one passing native identity for every supported target.
3. Configure the `runtime-publication` secret environment with the
   runtime-publisher GitHub App ID/private key. The App needs contents write only on
   `openminion/runtime`. Enable immutable Releases there before the first use.
4. Approve **Runtime promotion** with the exact candidate tag and a new release
   ID. It publishes the immutable runtime Release but deliberately leaves the
   OpenMinion stable feed unchanged.
5. Continue in Desktop's **Runtime qualification** workflow. Only after its
   evidence PR reaches Desktop main may the separate protected OpenMinion
   metadata workflow advertise these bytes.

Both packaging workflows fail closed unless dispatched from `main`. The
packaging repository is private on GitHub Free, where required-reviewer
environment rules are unavailable; manual dispatch plus the hard main-ref guard
is the enforceable packaging approval boundary. The public OpenMinion metadata
environment retains its required reviewer.

Do not add the central manifest dispatch back to this repository. Keeping asset
publication and discoverability separate prevents an unqualified packaged
Desktop/runtime pair from reaching clients.
