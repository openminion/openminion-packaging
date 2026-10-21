"""Tests for the standalone build contract."""

from __future__ import annotations

import importlib.util
import io
import json
import re
import tarfile
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

VERSION = "0.0.28"
COMMIT = "01ef455f337422eefe81a3084c4352d85924e78d"
WHEEL_SHA256 = "a" * 64
WHEEL_URL = (
    "https://files.pythonhosted.org/packages/example/"
    f"openminion-{VERSION}-py3-none-any.whl"
)


def create_wheel(path: Path, version: str = VERSION) -> None:
    metadata = f"""Metadata-Version: 2.4
Name: openminion
Version: {version}
Requires-Dist: httpx<1,>=0.27
Requires-Dist: scrapling>=0.2.0; extra == \"fetch-scrapling\"
"""
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr(f"openminion-{version}.dist-info/METADATA", metadata)


def workflow_shell_scripts(path: Path) -> list[str]:
    lines = path.read_text().splitlines()
    scripts = []
    for index, line in enumerate(lines):
        match = re.match(r"^(?P<indent>\s*)run:\s*(?P<inline>.*)$", line)
        if not match:
            continue
        indent = len(match["indent"])
        script = [match["inline"]]
        for candidate in lines[index + 1 :]:
            candidate_indent = len(candidate) - len(candidate.lstrip())
            if candidate.strip() and candidate_indent <= indent:
                break
            script.append(candidate)
        scripts.append("\n".join(script))
    return scripts


class BuildContractTests(unittest.TestCase):
    def test_release_request_must_match_production_pypi(self) -> None:
        metadata = {
            "info": {"name": "openminion", "version": VERSION},
            "urls": [
                {
                    "filename": f"openminion-{VERSION}-py3-none-any.whl",
                    "url": WHEEL_URL,
                    "digests": {"sha256": WHEEL_SHA256},
                    "packagetype": "bdist_wheel",
                    "yanked": False,
                }
            ],
        }
        response = io.BytesIO(json.dumps(metadata).encode())
        with patch.object(build.urllib.request, "urlopen", return_value=response):
            request = build.verify_release_request(
                VERSION,
                COMMIT,
                WHEEL_URL,
                WHEEL_SHA256,
            )
        self.assertEqual(request["source_commit"], COMMIT)
        with self.assertRaisesRegex(ValueError, "stable three-part"):
            build.release_request("0.0.28rc1", COMMIT, WHEEL_URL, WHEEL_SHA256)
        with self.assertRaisesRegex(ValueError, "full lowercase"):
            build.release_request(VERSION, "main", WHEEL_URL, WHEEL_SHA256)
        with self.assertRaisesRegex(ValueError, "official PyPI wheel"):
            build.release_request(
                VERSION,
                COMMIT,
                f"https://example.com/openminion-{VERSION}-py3-none-any.whl",
                WHEEL_SHA256,
            )
        with self.assertRaisesRegex(ValueError, "full lowercase digest"):
            build.release_request(VERSION, COMMIT, WHEEL_URL, "invalid")

    def test_release_request_rejects_pypi_metadata_drift(self) -> None:
        metadata = {
            "info": {"name": "openminion", "version": VERSION},
            "urls": [],
        }
        response = io.BytesIO(json.dumps(metadata).encode())
        with (
            patch.object(build.urllib.request, "urlopen", return_value=response),
            self.assertRaisesRegex(ValueError, "production PyPI metadata"),
        ):
            build.verify_release_request(VERSION, COMMIT, WHEEL_URL, WHEEL_SHA256)

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
                        "version": VERSION,
                        "commit": COMMIT,
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
                "source_commit": COMMIT,
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
            with self.assertRaises(ValueError):
                build.candidate_manifest(
                    artifacts["cli"],
                    artifacts["daemon"],
                    **{**arguments, "min_os_version": "Ubuntu 22.04"},
                )
            with self.assertRaises(ValueError):
                build.candidate_manifest(
                    artifacts["cli"],
                    artifacts["daemon"],
                    **{**arguments, "min_libc_version": "glibc 2.35"},
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
            "runtime_version": VERSION,
            "release_id": "private.1",
            "published_at": "2026-09-20T00:00:00Z",
            "source_commit": COMMIT,
            "release_notes_url": f"{build.OPENMINION_SOURCE}/releases/tag/v{VERSION}",
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
        self.assertEqual(version, VERSION)
        self.assertEqual(requirements, ["httpx<1,>=0.27"])

    def test_local_wheel_requires_matching_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            wheel = Path(temp_dir) / "openminion.whl"
            create_wheel(wheel)
            expected = build.sha256(wheel)
            version, _, actual = build.verify_wheel(wheel, "local", expected)
        self.assertEqual(version, VERSION)
        self.assertEqual(actual, expected)

    def test_local_wheel_rejects_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            wheel = Path(temp_dir) / "openminion.whl"
            create_wheel(wheel)
            with self.assertRaisesRegex(ValueError, "local wheel SHA-256 mismatch"):
                build.verify_wheel(wheel, "local", "0" * 64)

    def test_download_rejects_unapproved_hosts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "download"
            for url in ("file:///tmp/archive", "https://example.com/archive"):
                with self.assertRaisesRegex(ValueError, "approved HTTPS host"):
                    build.download(url, destination, "0" * 64)

    def test_python_archive_rejects_unsafe_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            archive = root / "python.tar.gz"
            payload = b"outside"
            with tarfile.open(archive, "w:gz") as target:
                member = tarfile.TarInfo("../outside")
                member.size = len(payload)
                target.addfile(member, io.BytesIO(payload))

            with self.assertRaises(tarfile.FilterError):
                build.extract_python(archive, root / "work")
            self.assertFalse((root / "outside").exists())

    def test_official_wheel_uses_requested_release_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            wheel = Path(temp_dir) / f"openminion-{VERSION}-py3-none-any.whl"
            create_wheel(wheel)
            digest = build.sha256(wheel)
            version, _, actual = build.verify_wheel(
                wheel,
                "pypi",
                digest,
                VERSION,
            )
            record = build.wheel_record(
                wheel,
                version,
                "pypi",
                actual,
                WHEEL_URL,
                COMMIT,
            )
        self.assertEqual(record["origin"], WHEEL_URL)
        self.assertEqual(record["tag"], f"v{VERSION}")
        self.assertEqual(record["commit"], COMMIT)

    def test_local_wheel_record_does_not_claim_official_source(self) -> None:
        wheel = Path("openminion-local.whl")
        record = build.wheel_record(wheel, VERSION, "local", "a" * 64)
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

    def test_refresh_artifact_records_signed_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact = Path(temp_dir) / "openminion"
            artifact.write_bytes(b"unsigned")
            artifact.with_name("openminion.json").write_text(
                json.dumps({"role": "cli", "artifact": {}})
            )
            artifact.write_bytes(b"signed")
            build.refresh_artifact(artifact)
            metadata = json.loads(artifact.with_name("openminion.json").read_text())
            self.assertEqual(metadata["artifact"]["sha256"], build.sha256(artifact))
            build.verify_artifact(artifact)

    def test_native_verification_requires_every_target_once(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            paths = []
            for target in ("macos-arm64", "linux-x86_64", "windows-x86_64"):
                path = root / f"{target}.json"
                path.write_text(
                    json.dumps(build.native_verification(target, f"native.{target}.1"))
                )
                paths.append(path)
            merged = build.merge_verifications(paths)
            self.assertEqual(
                set(merged["targets"]),
                {"darwin-arm64", "linux-x64", "win32-x64"},
            )
            with self.assertRaisesRegex(ValueError, "duplicate"):
                build.merge_verifications([paths[0], paths[0]])
            with self.assertRaisesRegex(ValueError, "incomplete"):
                build.merge_verifications(paths[:2])

    def test_lock_files_use_canonical_line_endings(self) -> None:
        attributes = BUILD_PATH.parents[1] / ".gitattributes"
        self.assertIn(
            "packaging/locks/*.txt text eol=lf",
            attributes.read_text().splitlines(),
        )
        for lock in build.LOCKS_DIR.glob("*.txt"):
            self.assertNotIn(b"\r\n", lock.read_bytes())

    def test_workflow_values_enter_shells_through_environment(self) -> None:
        workflows = BUILD_PATH.parents[1] / ".github" / "workflows"
        assignment = re.compile(
            r"^\s+[A-Z][A-Z0-9_]*:\s+\$\{\{ inputs\.[a-z0-9_]+ \}\}\s*$"
        )
        direct_shell_expansion = re.compile(
            r"\$\{\{\s*(?:inputs\.|matrix\.|needs\.[^}]+\.outputs\.)"
        )
        for workflow in workflows.glob("*.yml"):
            for line in workflow.read_text().splitlines():
                if "${{ inputs." in line:
                    self.assertRegex(line, assignment, workflow.name)
            for script in workflow_shell_scripts(workflow):
                self.assertNotRegex(script, direct_shell_expansion, workflow.name)

    def test_runtime_development_wheel_download_uses_bash(self) -> None:
        workflow = (
            BUILD_PATH.parents[1] / ".github" / "workflows" / "runtime-development.yml"
        ).read_text()
        self.assertRegex(
            workflow,
            r"- name: Download the verified wheel\n\s+shell: bash\n\s+run:",
        )

    def test_runtime_development_inventory_can_read_draft_release(self) -> None:
        workflow = (
            BUILD_PATH.parents[1] / ".github" / "workflows" / "runtime-development.yml"
        ).read_text()
        complete_job = workflow.split("\n  complete:\n", 1)[1]
        self.assertRegex(
            complete_job,
            r"permissions:\n\s+contents: write",
        )

    def test_pyapp_environment_is_offline_and_isolated(self) -> None:
        target = build.load_target("macos-arm64")
        values = build.pyapp_environment(
            VERSION,
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
