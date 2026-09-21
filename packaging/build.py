"""Build native OpenMinion launchers from one verified wheel."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from datetime import UTC, datetime
from email.message import Message
from email.parser import Parser
from pathlib import Path
from urllib.parse import urlparse
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
INPUTS_PATH = ROOT / "packaging" / "python-distributions.json"
LOCKS_DIR = ROOT / "packaging" / "locks"

OPENMINION_VERSION = "0.0.23"
OPENMINION_WHEEL = "openminion-0.0.23-py3-none-any.whl"
OPENMINION_WHEEL_SHA256 = (
    "996067a0fcc80387ac085b54c1d36f14b5d92474f8a80fcc6efe16d7e6cc5075"
)
OPENMINION_WHEEL_URL = "https://files.pythonhosted.org/packages/fa/c4/6ad79c9db011dc8199cb0a6c8aea3df5255aaf7eb6e0e6fedde161c4f21f/openminion-0.0.23-py3-none-any.whl"
OPENMINION_SOURCE = "https://github.com/openminion/openminion"
OPENMINION_TAG = "v0.0.23"
OPENMINION_COMMIT = "974d832a039e2ca68431a1bfd77eebc3050a4851"

PYAPP_VERSION = "0.29.0"
PYAPP_SOURCE = "https://github.com/ofek/pyapp"
PYAPP_COMMIT = "09bfa79cebf2ffc9fb54bda916043ce6165b984a"
PYAPP_CARGO_LOCK_SHA256 = (
    "03c7d769f582a11db6ce728600839d6a8d30d94a8faf8fd57a5a439337b80344"
)
UV_VERSION = "0.9.21"
RUST_VERSION = "1.89.0"
PROFILE = "core"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_checksum(artifact: Path, destination: Path) -> None:
    destination.write_bytes(f"{sha256(artifact)}  {artifact.name}\n".encode())


def verify_artifact(artifact: Path) -> None:
    metadata = json.loads(artifact.with_name(f"{artifact.name}.json").read_text())
    actual_sha256 = sha256(artifact)
    expected = metadata["artifact"]
    if expected != {
        "filename": artifact.name,
        "sha256": actual_sha256,
        "size_bytes": artifact.stat().st_size,
    }:
        raise ValueError("artifact metadata does not match the executable")
    checksum = artifact.with_name(f"{artifact.name}.sha256").read_text()
    if checksum != f"{actual_sha256}  {artifact.name}\n":
        raise ValueError("artifact checksum does not match the executable")
    print(f"verified {artifact}")


def candidate_manifest(
    cli_artifact: Path,
    daemon_artifact: Path,
    *,
    release_id: str,
    source_commit: str,
    cli_url: str,
    daemon_url: str,
    desktop_min: str,
    desktop_max: str,
    min_os_version: str,
    min_libc_version: str | None = None,
) -> dict:
    """Describe verified candidate bytes privately, without claiming promotion."""
    artifacts = {"cli": cli_artifact, "daemon": daemon_artifact}
    metadata = {}
    for role, artifact in artifacts.items():
        verify_artifact(artifact)
        item = json.loads(artifact.with_name(f"{artifact.name}.json").read_text())
        if item.get("role") != role:
            raise ValueError(f"candidate {role} artifact role mismatch")
        metadata[role] = item
    cli_metadata = metadata["cli"]
    if metadata["daemon"]["target"] != cli_metadata["target"]:
        raise ValueError("candidate executables must have the same target")
    if metadata["daemon"]["wheel"] != cli_metadata["wheel"]:
        raise ValueError("candidate executables must embed the same wheel")
    targets = {
        "macos-arm64": ("darwin", "arm64"),
        "linux-x86_64": ("linux", "x64"),
        "windows-x86_64": ("win32", "x64"),
    }
    target_platform, arch = targets[cli_metadata["target"]]
    if cli_metadata["wheel"]["version"] != OPENMINION_VERSION:
        raise ValueError("candidate wheel version does not match the packaging pin")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", release_id):
        raise ValueError("invalid candidate release identity")
    if not re.fullmatch(r"[a-f0-9]{40}", source_commit):
        raise ValueError("candidate requires exact source revision")
    official_commit = cli_metadata["wheel"].get("commit")
    if official_commit and official_commit != source_commit:
        raise ValueError("candidate source revision does not match the wheel")
    locations = {}
    for role, artifact in artifacts.items():
        artifact_url = cli_url if role == "cli" else daemon_url
        url = urlparse(artifact_url)
        if (
            url.scheme != "https"
            or not url.netloc
            or url.username
            or url.password
            or url.query
            or url.fragment
            or not url.path.endswith("/" + artifact.name)
        ):
            raise ValueError("candidate requires fixed HTTPS artifact locations")
        locations[role] = {**metadata[role]["artifact"], "url": artifact_url}
    bounds = []
    for value in (desktop_min, desktop_max):
        if not re.fullmatch(r"\d+\.\d+\.\d+", value):
            raise ValueError("invalid proposed Desktop bounds")
        bounds.append(tuple(int(part) for part in value.split(".")))
    if bounds[0] >= bounds[1] or not min_os_version:
        raise ValueError("invalid proposed native baseline")
    entry = {
        "platform": target_platform,
        "arch": arch,
        "format": "executables",
        "min_os_version": min_os_version,
        "cli": locations["cli"],
        "daemon": locations["daemon"],
    }
    if target_platform == "linux":
        if not min_libc_version:
            raise ValueError("Linux candidate requires its proposed glibc baseline")
        entry.update(libc_family="glibc", min_libc_version=min_libc_version)
    return {
        "schema_version": 1,
        "product": "openminion",
        "distribution": "binary",
        "channel": "stable",
        "promotion_status": "candidate",
        "runtime_version": OPENMINION_VERSION,
        "release_id": release_id,
        "source_commit": source_commit,
        "published_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "release_notes_url": f"{OPENMINION_SOURCE}/releases/tag/v{OPENMINION_VERSION}",
        "desktop_compatibility": {
            "min_version": desktop_min,
            "max_version_exclusive": desktop_max,
        },
        "artifacts": [entry],
    }


def merge_candidates(paths: list[Path], release_id: str) -> dict:
    if not paths:
        raise ValueError("at least one candidate record is required")
    records = [json.loads(path.read_text()) for path in paths]
    first = records[0]
    shared_keys = (
        "schema_version",
        "product",
        "distribution",
        "channel",
        "promotion_status",
        "runtime_version",
        "source_commit",
        "release_notes_url",
        "desktop_compatibility",
    )
    if any(
        tuple(record.get(key) for key in shared_keys)
        != tuple(first.get(key) for key in shared_keys)
        for record in records[1:]
    ):
        raise ValueError("candidate records do not share one release identity")
    if first.get("promotion_status") != "candidate":
        raise ValueError("only private candidate records can be merged")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", release_id):
        raise ValueError("invalid candidate release identity")
    artifacts = []
    targets = set()
    for record in records:
        if len(record.get("artifacts", [])) != 1:
            raise ValueError("each native job must contribute exactly one target")
        artifact = record["artifacts"][0]
        target = (artifact.get("platform"), artifact.get("arch"))
        if target in targets:
            raise ValueError("duplicate candidate target")
        targets.add(target)
        artifacts.append(artifact)
    artifacts.sort(key=lambda item: (item["platform"], item["arch"]))
    return {
        **{key: first[key] for key in shared_keys},
        "release_id": release_id,
        "published_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "artifacts": artifacts,
    }


def run(
    command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None
) -> str:
    completed = subprocess.run(
        command, cwd=cwd, env=env, text=True, capture_output=True, check=False
    )
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="")
    completed.check_returncode()
    return completed.stdout.strip()


def read_wheel_metadata(wheel: Path) -> Message:
    with ZipFile(wheel) as archive:
        metadata_path = next(
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        )
        return Parser().parsestr(archive.read(metadata_path).decode())


def wheel_metadata(wheel: Path) -> tuple[str, list[str]]:
    metadata = read_wheel_metadata(wheel)
    requirements = [
        item for item in metadata.get_all("Requires-Dist", []) if "extra ==" not in item
    ]
    return metadata["Version"], requirements


def verify_wheel(
    wheel: Path, origin: str, expected_sha256: str | None
) -> tuple[str, list[str], str]:
    actual_sha256 = sha256(wheel)
    version, requirements = wheel_metadata(wheel)
    if origin == "pypi":
        if wheel.name != OPENMINION_WHEEL or version != OPENMINION_VERSION:
            raise ValueError(f"expected official wheel {OPENMINION_WHEEL}")
        if actual_sha256 != OPENMINION_WHEEL_SHA256:
            raise ValueError("official wheel SHA-256 mismatch")
    elif not expected_sha256:
        raise ValueError("local wheel builds require --wheel-sha256")
    elif actual_sha256 != expected_sha256:
        raise ValueError("local wheel SHA-256 mismatch")
    return version, requirements, actual_sha256


def wheel_record(
    wheel: Path, version: str, origin: str, wheel_sha256: str
) -> dict[str, str]:
    record = {
        "version": version,
        "filename": wheel.name,
        "origin": OPENMINION_WHEEL_URL
        if origin == "pypi"
        else f"local:{wheel.resolve()}",
        "sha256": wheel_sha256,
    }
    if origin == "pypi":
        record.update(
            source=OPENMINION_SOURCE, tag=OPENMINION_TAG, commit=OPENMINION_COMMIT
        )
    return record


def load_target(target_name: str) -> dict[str, str]:
    inputs = json.loads(INPUTS_PATH.read_text())
    return inputs["targets"][target_name]


def require_native_host(target_name: str) -> None:
    system = platform.system().lower()
    machine = platform.machine().lower()
    host = {
        ("darwin", "arm64"): "macos-arm64",
        ("linux", "x86_64"): "linux-x86_64",
        ("windows", "amd64"): "windows-x86_64",
        ("windows", "x86_64"): "windows-x86_64",
    }.get((system, machine))
    if host != target_name:
        raise RuntimeError(
            f"{target_name} must build on its native host; detected {system}/{machine}"
        )


def write_lock(
    target_name: str,
    wheel: Path,
    requirements: list[str],
    check: bool,
) -> None:
    uv_version = run(["uv", "--version"]).split()[1]
    if uv_version != UV_VERSION:
        raise RuntimeError(f"expected uv {UV_VERSION}, found {uv_version}")
    target = load_target(target_name)
    lock_path = LOCKS_DIR / f"{target_name}.txt"
    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = Path(temp_dir) / "requirements.in"
        output_path = Path(temp_dir) / "requirements.txt"
        input_path.write_text("\n".join(requirements) + "\n")
        command = [
            "uv",
            "--quiet",
            "pip",
            "compile",
            str(input_path),
            "--generate-hashes",
            "--no-annotate",
            "--no-header",
            "--only-binary",
            ":all:",
            "--python-version",
            "3.11",
            "--python-platform",
            target["uv_platform"],
            "--output-file",
            str(output_path),
        ]
        run(command)
        generated = output_path.read_text()
    if check:
        if lock_path.read_text() != generated:
            raise RuntimeError(f"{lock_path.name} is not current for {wheel.name}")
        print(f"verified {lock_path}")
        return
    lock_path.write_text(generated)
    print(f"wrote {lock_path}")


def download(url: str, destination: Path, expected_sha256: str) -> None:
    if destination.exists() and sha256(destination) == expected_sha256:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output)
    if sha256(destination) != expected_sha256:
        destination.unlink()
        raise ValueError(f"SHA-256 mismatch for {url}")


def extract_python(archive: Path, work_dir: Path) -> Path:
    extracted = work_dir / "python-extracted"
    with tarfile.open(archive, "r:gz") as source:
        source.extractall(extracted)
    runtime = work_dir / "runtime"
    shutil.move(str(extracted / "python"), runtime)
    return runtime


def populate_runtime(
    runtime: Path,
    target: dict[str, str],
    lock: Path,
    wheel: Path,
    work_dir: Path,
) -> tuple[Path, list[dict[str, str]]]:
    relative_python = Path(target["python_path"]).relative_to("runtime")
    python = runtime / relative_python
    wheelhouse = work_dir / "wheelhouse"
    wheelhouse.mkdir()
    download_command = [
        str(python),
        "-m",
        "pip",
        "download",
        "--require-hashes",
        "--only-binary",
        ":all:",
        "--dest",
        str(wheelhouse),
        "-r",
        str(lock),
    ]
    run(download_command)
    manifest = [
        {"filename": item.name, "sha256": sha256(item)}
        for item in sorted(wheelhouse.iterdir())
    ]
    run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--require-hashes",
            "--no-index",
            "--find-links",
            str(wheelhouse),
            "-r",
            str(lock),
        ]
    )
    run([str(python), "-m", "pip", "install", "--no-deps", "--no-index", str(wheel)])
    run([str(python), "-m", "pip", "check"])
    return python, manifest


def archive_runtime(runtime: Path, destination: Path) -> None:
    with tarfile.open(destination, "w:gz") as archive:
        archive.add(runtime, arcname="runtime")


def checkout_pyapp(destination: Path) -> None:
    run(["git", "init"], cwd=destination)
    run(["git", "remote", "add", "origin", PYAPP_SOURCE], cwd=destination)
    run(["git", "fetch", "--depth", "1", "origin", PYAPP_COMMIT], cwd=destination)
    run(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=destination)
    if run(["git", "rev-parse", "HEAD"], cwd=destination) != PYAPP_COMMIT:
        raise RuntimeError("PyApp source commit mismatch")
    if sha256(destination / "Cargo.lock") != PYAPP_CARGO_LOCK_SHA256:
        raise RuntimeError("PyApp Cargo.lock SHA-256 mismatch")


def pyapp_environment(
    version: str, target: dict[str, str], distribution: Path, module: str
) -> dict[str, str]:
    values = {
        "PYAPP_PROJECT_NAME": "openminion",
        "PYAPP_PROJECT_VERSION": version,
        "PYAPP_EXEC_MODULE": module,
        "PYAPP_PYTHON_VERSION": "3.11",
        "PYAPP_DISTRIBUTION_PATH": str(distribution.resolve()),
        "PYAPP_DISTRIBUTION_PYTHON_PATH": target["python_path"],
        "PYAPP_DISTRIBUTION_SITE_PACKAGES_PATH": target["site_packages_path"],
        "PYAPP_FULL_ISOLATION": "1",
        "PYAPP_SKIP_INSTALL": "1",
    }
    if target["os"] == "macos":
        values["MACOSX_DEPLOYMENT_TARGET"] = "14.0"
    return values


def installed_packages(target: dict[str, str], runtime: Path) -> list[dict[str, str]]:
    site_packages = runtime / Path(target["site_packages_path"]).relative_to("runtime")
    packages = []
    for metadata_path in sorted(site_packages.glob("*.dist-info/METADATA")):
        metadata = Parser().parsestr(metadata_path.read_text(errors="replace"))
        packages.append(
            {
                "name": metadata.get("Name", ""),
                "version": metadata.get("Version", ""),
                "license": metadata.get("License-Expression")
                or metadata.get("License", ""),
            }
        )
    return packages


def build(
    target_name: str,
    wheel: Path,
    origin: str,
    expected_sha256: str | None,
    output_dir: Path,
) -> None:
    require_native_host(target_name)
    version, _, wheel_sha256 = verify_wheel(wheel, origin, expected_sha256)
    rustc_version = run(["rustc", "--version"])
    if rustc_version.split()[1] != RUST_VERSION:
        raise RuntimeError(f"expected Rust {RUST_VERSION}, found {rustc_version}")
    target = load_target(target_name)
    lock = LOCKS_DIR / f"{target_name}.txt"
    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir = output_dir / f"work-{target_name}"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir()

    python_archive = work_dir / Path(target["archive_url"]).name
    download(target["archive_url"], python_archive, target["archive_sha256"])
    runtime = extract_python(python_archive, work_dir)
    python, wheelhouse = populate_runtime(runtime, target, lock, wheel, work_dir)
    distribution = work_dir / f"openminion-runtime-{target_name}.tar.gz"
    archive_runtime(runtime, distribution)

    pyapp_source = work_dir / "pyapp"
    pyapp_source.mkdir()
    checkout_pyapp(pyapp_source)
    wheelhouse_manifest = work_dir / "wheelhouse.json"
    wheelhouse_manifest.write_text(json.dumps(wheelhouse, indent=2) + "\n")
    common_metadata = {
        "schema_version": 1,
        "target": target_name,
        "profile": PROFILE,
        "publishing": False,
        "wheel": wheel_record(wheel, version, origin, wheel_sha256),
        "python": {
            "version": json.loads(INPUTS_PATH.read_text())["python_version"],
            "archive_url": target["archive_url"],
            "archive_sha256": target["archive_sha256"],
            "embedded_archive_sha256": sha256(distribution),
        },
        "tools": {
            "uv": UV_VERSION,
            "rustc": rustc_version,
            "cargo": run(["cargo", "--version"]),
        },
        "lock_sha256": sha256(lock),
        "wheelhouse_manifest_sha256": sha256(wheelhouse_manifest),
        "packages": installed_packages(target, runtime),
        "embedded_python": str(python.relative_to(runtime)),
    }
    base_environment = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith("PYAPP_")
    }
    binary_name = target["binary_name"].replace("openminion", "pyapp")
    for role, module in (("cli", "openminion"), ("daemon", "openminion.daemon_main")):
        target_dir = (work_dir / f"pyapp-target-{role}").resolve()
        environment = {
            **base_environment,
            **pyapp_environment(version, target, distribution, module),
            "CARGO_TARGET_DIR": str(target_dir),
        }
        run(
            ["cargo", "build", "--release", "--locked"],
            cwd=pyapp_source,
            env=environment,
        )
        command = "openminion" if role == "cli" else "openminiond"
        artifact_name = f"{command}-{version}-{target_name}"
        if target["os"] == "windows":
            artifact_name += ".exe"
        artifact = output_dir / artifact_name
        shutil.copy2(target_dir / "release" / binary_name, artifact)
        artifact.chmod(artifact.stat().st_mode | 0o111)
        metadata = {
            **common_metadata,
            "role": role,
            "pyapp": {
                "version": PYAPP_VERSION,
                "source": PYAPP_SOURCE,
                "commit": PYAPP_COMMIT,
                "cargo_lock_sha256": PYAPP_CARGO_LOCK_SHA256,
                "environment": pyapp_environment(version, target, distribution, module),
            },
            "artifact": {
                "filename": artifact.name,
                "sha256": sha256(artifact),
                "size_bytes": artifact.stat().st_size,
            },
        }
        metadata_path = output_dir / f"{artifact.name}.json"
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
        write_checksum(artifact, output_dir / f"{artifact.name}.sha256")
        print(f"built {artifact}")


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    subparsers = argument_parser.add_subparsers(dest="command", required=True)
    for command in ("lock", "build"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument(
            "--target",
            required=True,
            choices=sorted(json.loads(INPUTS_PATH.read_text())["targets"]),
        )
        subparser.add_argument("--wheel", required=True, type=Path)
        subparser.add_argument(
            "--wheel-origin", choices=("pypi", "local"), default="pypi"
        )
        subparser.add_argument("--wheel-sha256")
    subparsers.choices["lock"].add_argument("--check", action="store_true")
    subparsers.choices["build"].add_argument(
        "--output-dir", type=Path, default=ROOT / "dist"
    )
    verify = subparsers.add_parser("verify")
    verify.add_argument("--artifact", required=True, type=Path)
    download_wheel = subparsers.add_parser("download-wheel")
    download_wheel.add_argument("--output-dir", required=True, type=Path)
    merge = subparsers.add_parser("merge-candidates")
    merge.add_argument("--input", required=True, action="append", type=Path)
    merge.add_argument("--release-id", required=True)
    merge.add_argument("--output", required=True, type=Path)
    candidate = subparsers.add_parser("candidate-manifest")
    candidate.add_argument("--cli-artifact", required=True, type=Path)
    candidate.add_argument("--daemon-artifact", required=True, type=Path)
    candidate.add_argument("--release-id", required=True)
    candidate.add_argument("--source-commit", required=True)
    candidate.add_argument("--cli-url", required=True)
    candidate.add_argument("--daemon-url", required=True)
    candidate.add_argument("--desktop-min", required=True)
    candidate.add_argument("--desktop-max", required=True)
    candidate.add_argument("--min-os-version", required=True)
    candidate.add_argument("--min-libc-version")
    candidate.add_argument("--output", required=True, type=Path)
    return argument_parser


def main() -> None:
    args = parser().parse_args()
    if args.command == "download-wheel":
        destination = args.output_dir / OPENMINION_WHEEL
        download(OPENMINION_WHEEL_URL, destination, OPENMINION_WHEEL_SHA256)
        print(destination)
        return
    if args.command == "merge-candidates":
        record = merge_candidates(args.input, args.release_id)
        args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        return
    if args.command == "candidate-manifest":
        record = candidate_manifest(
            args.cli_artifact,
            args.daemon_artifact,
            release_id=args.release_id,
            source_commit=args.source_commit,
            cli_url=args.cli_url,
            daemon_url=args.daemon_url,
            desktop_min=args.desktop_min,
            desktop_max=args.desktop_max,
            min_os_version=args.min_os_version,
            min_libc_version=args.min_libc_version,
        )
        args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        return
    if args.command == "verify":
        verify_artifact(args.artifact)
        return
    version, requirements, _ = verify_wheel(
        args.wheel, args.wheel_origin, args.wheel_sha256
    )
    if args.command == "lock":
        write_lock(
            args.target,
            args.wheel,
            requirements,
            args.check,
        )
        return
    if version != OPENMINION_VERSION and args.wheel_origin == "pypi":
        raise ValueError(f"expected OpenMinion {OPENMINION_VERSION}")
    build(
        args.target,
        args.wheel,
        args.wheel_origin,
        args.wheel_sha256,
        args.output_dir,
    )


if __name__ == "__main__":
    main()
