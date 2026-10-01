"""Validate one signed runtime candidate before public Release publication."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


TARGETS = {"darwin-arm64", "linux-x64", "win32-x64"}
IDENTITY = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
DIGEST = re.compile(r"[a-f0-9]{64}")
VERSION = re.compile(r"\d+\.\d+\.\d+")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def publication_plan(
    candidate_path: Path,
    verification_path: Path,
    artifact_dir: Path,
    release_id: str,
) -> dict:
    """Return the exact immutable Release identity after validating local bytes."""
    candidate = json.loads(candidate_path.read_text())
    verification = json.loads(verification_path.read_text())
    version = candidate.get("runtime_version")
    if (
        candidate.get("schema_version") != 1
        or candidate.get("product") != "openminion"
        or candidate.get("distribution") != "binary"
        or candidate.get("channel") != "stable"
        or candidate.get("promotion_status") != "candidate"
        or not isinstance(version, str)
        or not VERSION.fullmatch(version)
        or not re.fullmatch(r"[a-f0-9]{40}", str(candidate.get("source_commit", "")))
        or not IDENTITY.fullmatch(release_id)
    ):
        raise ValueError("invalid candidate publication identity")
    bounds = candidate.get("desktop_compatibility")
    if not isinstance(bounds, dict) or not all(
        isinstance(bounds.get(name), str) and VERSION.fullmatch(bounds[name])
        for name in ("min_version", "max_version_exclusive")
    ):
        raise ValueError("candidate lacks fixed Desktop compatibility bounds")
    checks = verification.get("targets") if isinstance(verification, dict) else None
    if verification.get("schema_version") != 1 or not isinstance(checks, dict):
        raise ValueError("invalid native verification evidence")

    assets = []
    target_names = set()
    filenames = set()
    for target in candidate.get("artifacts", []):
        if not isinstance(target, dict):
            raise ValueError("invalid candidate target")
        name = f"{target.get('platform')}-{target.get('arch')}"
        evidence = checks.get(name)
        if (
            name not in TARGETS
            or name in target_names
            or target.get("format") != "executables"
            or not isinstance(evidence, dict)
            or not IDENTITY.fullmatch(str(evidence.get("verification_id", "")))
            or evidence.get("result") != "passed"
        ):
            raise ValueError("candidate target lacks native verification evidence")
        target_names.add(name)
        for role in ("cli", "daemon"):
            identity = target.get(role)
            if not isinstance(identity, dict):
                raise ValueError("invalid candidate executable identity")
            filename = identity.get("filename")
            path = artifact_dir / str(filename)
            if (
                not isinstance(filename, str)
                or not IDENTITY.fullmatch(filename)
                or filename in filenames
                or not path.is_file()
                or identity.get("size_bytes") != path.stat().st_size
                or not DIGEST.fullmatch(str(identity.get("sha256", "")))
                or identity["sha256"] != sha256(path)
            ):
                raise ValueError("candidate executable differs from verified bytes")
            filenames.add(filename)
            assets.append(str(path))
    if target_names != TARGETS or set(checks) != TARGETS:
        raise ValueError("candidate requires all supported native targets")
    return {
        "tag": f"runtime-v{version}-{release_id}",
        "title": f"OpenMinion runtime {version}",
        "assets": sorted(assets),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--verification", required=True, type=Path)
    parser.add_argument("--artifact-dir", required=True, type=Path)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    plan = publication_plan(
        args.candidate,
        args.verification,
        args.artifact_dir,
        args.release_id,
    )
    args.output.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
