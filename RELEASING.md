# OpenMinion Standalone Packaging Releases

Status: signed candidate and unsigned development publication enabled
Last updated: 2026-10-19

This repository produces restricted native release candidates. The
`Runtime candidates` workflow builds paired `openminion` and `openminiond`
executables from the exact official OpenMinion wheel, verifies their bytes,
starts the real daemon, probes `/health`, and records one cross-platform
candidate identity in a draft release visible only to repository maintainers.

The separate `Runtime development binaries` workflow builds and smoke-tests the
same paired executables without signing. It exists so every final source release
can have complete macOS arm64, Linux x86_64, and Windows x86_64 binaries while
signing is unavailable. Its outputs may be transferred only to an explicitly
unsigned prerelease in `openminion/runtime`; they never enter the stable binary
manifest and do not satisfy signing, native trust, Desktop compatibility, or
automatic-update acceptance.

Every request supplies the final three-part runtime version, full source commit,
official production wheel URL, and SHA-256. The workflow independently checks
those values against the immutable source tag and version-specific PyPI
metadata before downloading or building. A successful final source release can
request this candidate automatically; that request grants no
stable-publication authority.

## Candidate metadata

After verifying an artifact, the existing builder can describe it for staged
native qualification:

```bash
python3.11 packaging/build.py candidate-manifest --help
```

Supply its exact source commit, release identity, fixed restricted HTTPS artifact
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

Never publish an unsigned artifact as a stable runtime or publish a binary
produced from a dirty or unreviewed commit. A successful signed candidate
workflow is necessary evidence for stable promotion, not release authorization.

## Unsigned development sequence

Use this sequence after the final PyPI wheel and source tag are public:

1. dispatch **Runtime development binaries** from packaging `main` with the
   exact runtime version, source commit, wheel URL, and wheel SHA-256,
2. require all three native jobs and the completion inventory to pass,
3. transfer every `openminion` and `openminiond` executable, its `.json`
   metadata, and its `.sha256` sidecar from the restricted draft to a public
   `runtime-dev-v<version>-build.<number>` prerelease,
4. add `runtime-release.json` and `SHA256SUMS`, clearly recording that signing,
   notarization, stable-feed promotion, and Desktop qualification are absent,
5. download every public asset again and verify its SHA-256, and
6. delete the temporary draft only after the public readback passes.

This is the required binary disposition for a source release while signing is
unavailable. It is intentionally separate from the signed candidate and
promotion sequence below.

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

All packaging workflows fail closed unless dispatched from `main`. Manual
dispatch, the hard main-ref guard, and protected deployment environments are
the packaging approval boundary. The public OpenMinion metadata environment
retains its required reviewer.

Do not add the central manifest dispatch back to this repository. Keeping asset
publication and discoverability separate prevents an unqualified packaged
Desktop/runtime pair from reaching clients.

## Public repository conversion

Repository visibility changes source access and Actions billing; it does not
change artifact status or publication authority. Complete this checklist when
the repository is made public:

1. require pull requests and the passing `CI / Repository check` status for
   `main` and `dev`, and block force pushes and branch deletion,
2. retain read-only default workflow permissions and grant write permissions
   only to the jobs that create restricted draft Releases,
3. keep `Runtime candidates`, `Runtime development binaries`, and
   `Runtime promotion` manual and guarded to `refs/heads/main`,
4. configure required reviewers for `runtime-signing` and
   `runtime-publication` before adding signing or publisher credentials,
5. confirm that no signing certificate, notarization credential, publisher
   private key, generated binary, wheel, or restricted evidence is tracked in
   Git history,
6. review existing draft Releases and delete obsolete transfer drafts after
   their evidence is no longer needed,
7. run `make check`, then dispatch one unsigned development build with an exact
   production release identity and verify every public runtime asset after its
   controlled transfer, and
8. leave stable manifest publication disabled until the signed qualification
   and Desktop compatibility gates above are satisfied.

Public workflow logs and source code are expected. Draft Release assets remain
restricted to repository maintainers until deliberately published or
transferred to `openminion/runtime`.
