"""Tests for fail-closed runtime Release promotion."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PUBLISH_PATH = Path(__file__).parents[1] / "packaging" / "publish.py"
SPEC = importlib.util.spec_from_file_location(
    "openminion_packaging_publish", PUBLISH_PATH
)
publish = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(publish)


class PublicationPlanTests(unittest.TestCase):
    def test_accepts_only_complete_verified_candidate_bytes(self) -> None:
        with fixture() as item:
            plan = publish.publication_plan(*item.paths, "build.1")
            self.assertEqual(plan["tag"], "runtime-v1.2.3-build.1")
            self.assertEqual(len(plan["assets"]), 6)

    def test_rejects_changed_executable(self) -> None:
        with fixture() as item:
            item.artifacts[0].write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "differs"):
                publish.publication_plan(*item.paths, "build.1")

    def test_rejects_missing_target_or_verification(self) -> None:
        with fixture() as item:
            candidate = json.loads(item.candidate.read_text())
            candidate["artifacts"].pop()
            item.candidate.write_text(json.dumps(candidate))
            with self.assertRaisesRegex(ValueError, "all supported"):
                publish.publication_plan(*item.paths, "build.1")
        with fixture() as item:
            verification = json.loads(item.verification.read_text())
            verification["targets"]["darwin-arm64"]["result"] = "failed"
            item.verification.write_text(json.dumps(verification))
            with self.assertRaisesRegex(ValueError, "verification"):
                publish.publication_plan(*item.paths, "build.1")


class fixture:
    def __enter__(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.artifact_dir = root / "artifacts"
        self.artifact_dir.mkdir()
        records = []
        self.artifacts = []
        for platform, arch, suffix in (
            ("darwin", "arm64", "macos-arm64"),
            ("linux", "x64", "linux-x86_64"),
            ("win32", "x64", "windows-x86_64.exe"),
        ):
            identities = {}
            for role in ("cli", "daemon"):
                command = "openminion" if role == "cli" else "openminiond"
                path = self.artifact_dir / f"{command}-1.2.3-{suffix}"
                path.write_bytes(f"{platform}-{role}".encode())
                self.artifacts.append(path)
                identities[role] = {
                    "filename": path.name,
                    "sha256": publish.sha256(path),
                    "size_bytes": path.stat().st_size,
                }
            records.append(
                {
                    "platform": platform,
                    "arch": arch,
                    "format": "executables",
                    "min_os_version": "1.0",
                    **identities,
                }
            )
        candidate = {
            "schema_version": 1,
            "product": "openminion",
            "distribution": "binary",
            "channel": "stable",
            "promotion_status": "candidate",
            "runtime_version": "1.2.3",
            "source_commit": "a" * 40,
            "desktop_compatibility": {
                "min_version": "1.0.0",
                "max_version_exclusive": "2.0.0",
            },
            "artifacts": records,
        }
        verification = {
            "schema_version": 1,
            "targets": {
                "darwin-arm64": {
                    "verification_id": "native.macos.1",
                    "result": "passed",
                },
                "linux-x64": {"verification_id": "native.linux.1", "result": "passed"},
                "win32-x64": {
                    "verification_id": "native.windows.1",
                    "result": "passed",
                },
            },
        }
        self.candidate = root / "candidate.json"
        self.verification = root / "verification.json"
        self.candidate.write_text(json.dumps(candidate))
        self.verification.write_text(json.dumps(verification))
        self.paths = (self.candidate, self.verification, self.artifact_dir)
        return self

    def __exit__(self, *_args):
        self.temporary.cleanup()
