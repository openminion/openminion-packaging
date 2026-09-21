"""Tests for the standalone build contract."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZIP_DEFLATED, ZipFile

BUILD_PATH = Path(__file__).parents[1] / "packaging" / "build.py"
SPEC = importlib.util.spec_from_file_location("openminion_packaging_build", BUILD_PATH)
build = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(build)


def create_wheel(path: Path, version: str = build.OPENMINION_VERSION) -> None:
    metadata = f"""Metadata-Version: 2.4
Name: openminion
Version: {version}
Requires-Dist: httpx<1,>=0.27
Requires-Dist: scrapling>=0.2.0; extra == \"fetch-scrapling\"
"""
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr(f"openminion-{version}.dist-info/METADATA", metadata)


class BuildContractTests(unittest.TestCase):
    def test_private_manifest_accepts_uncertified_prototype_but_never_promotes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifacts = {
                "cli": root / "openminion-linux-x86_64",
                "daemon": root / "openminiond-linux-x86_64",
            }
            for role, artifact in artifacts.items():
                artifact.write_bytes(f"prototype {role}".encode())
                metadata = {
                    "target": "linux-x86_64",
                    "publishing": False,
                    "role": role,
                    "wheel": {
                        "version": build.OPENMINION_VERSION,
                        "commit": build.OPENMINION_COMMIT,
                    },
                    "artifact": {
                        "filename": artifact.name,
                        "sha256": build.sha256(artifact),
                        "size_bytes": artifact.stat().st_size,
                    },
                }
                artifact.with_name(artifact.name + ".json").write_text(
                    json.dumps(metadata)
                )
                build.write_checksum(
                    artifact, artifact.with_name(artifact.name + ".sha256")
                )
            arguments = {
                "release_id": "private.1",
                "source_commit": build.OPENMINION_COMMIT,
                "cli_url": "https://staging.example.invalid/" + artifacts["cli"].name,
                "daemon_url": "https://staging.example.invalid/"
                + artifacts["daemon"].name,
                "desktop_min": "0.0.0",
                "desktop_max": "1.0.0",
                "min_os_version": "22.04",
                "min_libc_version": "2.35",
            }
            record = build.candidate_manifest(
                artifacts["cli"], artifacts["daemon"], **arguments
            )
            self.assertEqual(record["promotion_status"], "candidate")
            self.assertEqual(record["artifacts"][0]["platform"], "linux")
            self.assertEqual(record["artifacts"][0]["format"], "executables")
            self.assertEqual(
                record["artifacts"][0]["cli"]["sha256"],
                build.sha256(artifacts["cli"]),
            )
            self.assertEqual(
                record["artifacts"][0]["daemon"]["sha256"],
                build.sha256(artifacts["daemon"]),
            )
            self.assertNotIn("verification_id", record["artifacts"][0])
            with self.assertRaises(ValueError):
                build.candidate_manifest(
                    artifacts["cli"],
                    artifacts["daemon"],
                    **{**arguments, "release_id": "../stable"},
                )
            with self.assertRaises(ValueError):
                build.candidate_manifest(
                    artifacts["cli"],
                    artifacts["daemon"],
                    **{**arguments, "min_libc_version": None},
                )
            artifacts["daemon"].write_bytes(b"changed")
            with self.assertRaises(ValueError):
                build.candidate_manifest(
                    artifacts["cli"], artifacts["daemon"], **arguments
                )

    def test_native_candidates_merge_without_duplicating_targets(self) -> None:
        common = {
            "schema_version": 1,
            "product": "openminion",
            "distribution": "binary",
            "channel": "stable",
            "promotion_status": "candidate",
            "runtime_version": build.OPENMINION_VERSION,
            "release_id": "private.1",
            "published_at": "2026-09-20T00:00:00Z",
            "source_commit": build.OPENMINION_COMMIT,
            "release_notes_url": f"{build.OPENMINION_SOURCE}/releases/tag/{build.OPENMINION_TAG}",
            "desktop_compatibility": {
                "min_version": "0.0.0",
                "max_version_exclusive": "1.0.0",
            },
        }
        target = {
            "arch": "arm64",
            "platform": "darwin",
            "format": "executables",
            "min_os_version": "14.0",
            "cli": {"filename": "openminion", "sha256": "a" * 64, "size_bytes": 1},
            "daemon": {
                "filename": "openminiond",
                "sha256": "b" * 64,
                "size_bytes": 1,
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.json"
            second = Path(directory) / "second.json"
            first.write_text(json.dumps({**common, "artifacts": [target]}))
            linux = {
                **target,
                "platform": "linux",
                "arch": "x64",
                "min_os_version": "22.04",
                "libc_family": "glibc",
                "min_libc_version": "2.35",
            }
            second.write_text(json.dumps({**common, "artifacts": [linux]}))
            merged = build.merge_candidates([first, second], "candidate.2")
            self.assertEqual(merged["release_id"], "candidate.2")
            self.assertEqual(len(merged["artifacts"]), 2)
            second.write_text(json.dumps({**common, "artifacts": [target]}))
            with self.assertRaisesRegex(ValueError, "duplicate"):
                build.merge_candidates([first, second], "candidate.2")

    def test_repository_documentation_surface_is_complete(self) -> None:
        root = Path(__file__).parents[1]
        root_docs = {
            "API_COMPATIBILITY.md",
            "CHANGELOG.md",
            "CODE_OF_CONDUCT.md",
            "CODE_QUALITY.md",
            "CONTRIBUTING.md",
            "LICENSE",
            "NOTICE",
            "README.md",
            "RELEASING.md",
            "SECURITY.md",
            "SUPPORT.md",
        }
        package_docs = {
            "README.md",
            "certification-readiness-matrix.md",
            "code-quality-enforcement.md",
            "engineering-patterns.md",
            "getting-started.md",
            "source-tree-owner-map.md",
            "testing-and-validation.md",
        }

        self.assertTrue(root_docs.issubset({path.name for path in root.iterdir()}))
        self.assertTrue(
            package_docs.issubset({path.name for path in (root / "docs").iterdir()})
        )

    def test_wheel_metadata_keeps_only_core_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            wheel = Path(temp_dir) / "openminion.whl"
            create_wheel(wheel)
            version, requirements = build.wheel_metadata(wheel)
        self.assertEqual(version, build.OPENMINION_VERSION)
        self.assertEqual(requirements, ["httpx<1,>=0.27"])

    def test_local_wheel_requires_matching_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            wheel = Path(temp_dir) / "openminion.whl"
            create_wheel(wheel)
            expected = build.sha256(wheel)
            version, _, actual = build.verify_wheel(wheel, "local", expected)
        self.assertEqual(version, build.OPENMINION_VERSION)
        self.assertEqual(actual, expected)

    def test_local_wheel_rejects_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            wheel = Path(temp_dir) / "openminion.whl"
            create_wheel(wheel)
            with self.assertRaisesRegex(ValueError, "local wheel SHA-256 mismatch"):
                build.verify_wheel(wheel, "local", "0" * 64)

    def test_local_wheel_record_does_not_claim_official_source(self) -> None:
        wheel = Path("openminion-local.whl")
        record = build.wheel_record(wheel, build.OPENMINION_VERSION, "local", "a" * 64)
        self.assertEqual(record["origin"], f"local:{wheel.resolve()}")
        self.assertNotIn("source", record)
        self.assertNotIn("tag", record)
        self.assertNotIn("commit", record)

    def test_checksum_file_is_portable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact = root / "openminion.exe"
            checksum = root / "openminion.exe.sha256"
            artifact.write_bytes(b"artifact")
            build.write_checksum(artifact, checksum)

            self.assertEqual(
                checksum.read_bytes(),
                f"{build.sha256(artifact)}  openminion.exe\n".encode(),
            )

    def test_artifact_verification_checks_metadata_and_checksum(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact = Path(temp_dir) / "openminion.exe"
            artifact.write_bytes(b"artifact")
            digest = build.sha256(artifact)
            artifact.with_name("openminion.exe.json").write_text(
                json.dumps(
                    {
                        "artifact": {
                            "filename": artifact.name,
                            "sha256": digest,
                            "size_bytes": artifact.stat().st_size,
                        }
                    }
                )
            )
            build.write_checksum(artifact, artifact.with_name("openminion.exe.sha256"))

            build.verify_artifact(artifact)

            artifact.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "metadata"):
                build.verify_artifact(artifact)

            artifact.write_bytes(b"artifact")
            artifact.with_name("openminion.exe.sha256").write_text(
                f"{'0' * 64}  {artifact.name}\n"
            )
            with self.assertRaisesRegex(ValueError, "checksum"):
                build.verify_artifact(artifact)

    def test_lock_files_use_canonical_line_endings(self) -> None:
        attributes = BUILD_PATH.parents[1] / ".gitattributes"
        self.assertIn(
            "packaging/locks/*.txt text eol=lf",
            attributes.read_text().splitlines(),
        )
        for lock in build.LOCKS_DIR.glob("*.txt"):
            self.assertNotIn(b"\r\n", lock.read_bytes())

    def test_pyapp_environment_is_offline_and_isolated(self) -> None:
        target = build.load_target("macos-arm64")
        values = build.pyapp_environment(
            build.OPENMINION_VERSION,
            target,
            Path("runtime.tar.gz"),
            "openminion.daemon_main",
        )
        self.assertEqual(values["PYAPP_FULL_ISOLATION"], "1")
        self.assertEqual(values["PYAPP_SKIP_INSTALL"], "1")
        self.assertEqual(values["PYAPP_EXEC_MODULE"], "openminion.daemon_main")
        self.assertNotIn("PYAPP_ALLOW_UPDATES", values)
        self.assertNotIn("PYAPP_EXPOSE_ALL_COMMANDS", values)

    def test_all_targets_have_explicit_runtime_paths(self) -> None:
        inputs = json.loads(build.INPUTS_PATH.read_text())
        self.assertEqual(
            set(inputs["targets"]),
            {"macos-arm64", "windows-x86_64", "linux-x86_64"},
        )
        for target in inputs["targets"].values():
            self.assertTrue(target["python_path"].startswith("runtime/"))
            self.assertTrue(target["site_packages_path"].startswith("runtime/"))
            self.assertEqual(len(target["archive_sha256"]), 64)

    def test_build_rejects_non_native_host(self) -> None:
        with (
            patch.object(build.platform, "system", return_value="Darwin"),
            patch.object(build.platform, "machine", return_value="arm64"),
            self.assertRaisesRegex(RuntimeError, "native host"),
        ):
            build.require_native_host("windows-x86_64")


if __name__ == "__main__":
    unittest.main()
