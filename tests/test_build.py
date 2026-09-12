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
        record = build.wheel_record(wheel, "0.0.19", "local", "a" * 64)
        self.assertEqual(record["origin"], f"local:{wheel.resolve()}")
        self.assertNotIn("source", record)
        self.assertNotIn("tag", record)
        self.assertNotIn("commit", record)

    def test_dependency_wheel_adds_one_local_source(self) -> None:
        wheel = Path("wheelhouse/sophiagraph.whl")
        self.assertEqual(
            build.dependency_find_links(wheel),
            ["--find-links", str(wheel.parent.resolve())],
        )

    def test_download_lock_omits_local_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            dependency = root / "sophiagraph.whl"
            with ZipFile(dependency, "w", ZIP_DEFLATED) as archive:
                archive.writestr(
                    "sophiagraph-0.0.10.dist-info/METADATA",
                    "Metadata-Version: 2.4\nName: sophiagraph\nVersion: 0.0.10\n",
                )
            lock = root / "requirements.txt"
            lock.write_text(
                "httpx==0.28.1 \\\n    --hash=sha256:aaa\n"
                "sophiagraph==0.0.10 \\\n    --hash=sha256:bbb\n"
                "typer==0.27.2 \\\n    --hash=sha256:ccc\n"
            )
            output = root / "download.txt"
            build.write_download_lock(lock, output, dependency)
            content = output.read_text()

        self.assertNotIn("sophiagraph", content)
        self.assertIn("httpx==0.28.1", content)
        self.assertIn("typer==0.27.2", content)

    def test_pyapp_environment_is_offline_and_isolated(self) -> None:
        target = build.load_target("macos-arm64")
        values = build.pyapp_environment(
            build.OPENMINION_VERSION, target, Path("runtime.tar.gz")
        )
        self.assertEqual(values["PYAPP_FULL_ISOLATION"], "1")
        self.assertEqual(values["PYAPP_SKIP_INSTALL"], "1")
        self.assertEqual(values["PYAPP_EXEC_MODULE"], "openminion")
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
        ):
            with self.assertRaisesRegex(RuntimeError, "native host"):
                build.require_native_host("windows-x86_64")


if __name__ == "__main__":
    unittest.main()
