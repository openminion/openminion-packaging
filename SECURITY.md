# Security Policy

## Reporting a vulnerability

Do not open a public issue containing exploit details, credentials, signing
material, non-public build evidence, or unreleased artifact locations.

Use
[GitHub private vulnerability reporting](https://github.com/openminion/openminion-packaging/security/advisories/new).
If that form is unavailable, ask an OpenMinion organization owner for a
secure handoff without including sensitive details in an issue or discussion.

## Scope

Reports should identify whether the issue affects:

1. wheel, lock, Python-distribution, or toolchain verification,
2. artifact assembly, metadata, or native platform isolation,
3. CI permissions, temporary artifacts, signing, or publication,
4. install, update, rollback, removal, or user-data preservation, or
5. an upstream OpenMinion or dependency repository instead.

Include the packaging commit, target, artifact hash, reproduction steps, and
impact when possible. Never attach production credentials or private keys.
