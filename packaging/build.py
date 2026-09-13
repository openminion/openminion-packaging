"""Build native OpenMinion launchers from one verified wheel."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from email.message import Message
from email.parser import Parser
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
INPUTS_PATH = ROOT / "packaging" / "python-distributions.json"
LOCKS_DIR = ROOT / "packaging" / "locks"

OPENMINION_VERSION = "0.0.19"
OPENMINION_WHEEL = "openminion-0.0.19-py3-none-any.whl"
OPENMINION_WHEEL_SHA256 = (
    "4c2e7d30c3b993e24834d17e9881889a78987ee2a07f8e503d7f40fdca395112"
)
OPENMINION_WHEEL_URL = "https://files.pythonhosted.org/packages/3d/bb/d6268e845a980ebf69052e0b8669edaee161e229c77a4752f506c6e0c6d8/openminion-0.0.19-py3-none-any.whl"
OPENMINION_SOURCE = "https://github.com/openminion/openminion"
OPENMINION_TAG = "v0.0.19"
OPENMINION_COMMIT = "ead891854930ed78d034b0ae41aedc7d40b86224"

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


def run(
    command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None
) -> str:
    completed = subprocess.run(
        command, cwd=cwd, env=env, text=True, capture_output=True
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


def write_download_lock(lock: Path, output: Path, dependency_wheel: Path) -> None:
    dependency_name = (
        read_wheel_metadata(dependency_wheel)["Name"].lower().replace("_", "-")
    )
    lines: list[str] = []
    skip = False
    for line in lock.read_text().splitlines():
        if line and not line[0].isspace():
            name = line.split("==", 1)[0].lower().replace("_", "-")
            skip = name == dependency_name
        if not skip:
            lines.append(line)
    output.write_text("\n".join(lines) + "\n")


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
    dependency_wheel: Path | None,
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
        if dependency_wheel is not None:
            command.extend(["--find-links", str(dependency_wheel.parent.resolve())])
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
    dependency_wheel: Path | None,
    work_dir: Path,
) -> tuple[Path, list[dict[str, str]]]:
    relative_python = Path(target["python_path"]).relative_to("runtime")
    python = runtime / relative_python
    wheelhouse = work_dir / "wheelhouse"
    wheelhouse.mkdir()
    download_lock = lock
    if dependency_wheel is not None:
        download_lock = work_dir / "download-requirements.txt"
        write_download_lock(lock, download_lock, dependency_wheel)
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
        str(download_lock),
    ]
    run(download_command)
    if dependency_wheel is not None:
        shutil.copy2(dependency_wheel, wheelhouse / dependency_wheel.name)
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
    version: str, target: dict[str, str], distribution: Path
) -> dict[str, str]:
    values = {
        "PYAPP_PROJECT_NAME": "openminion",
        "PYAPP_PROJECT_VERSION": version,
        "PYAPP_EXEC_MODULE": "openminion",
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
    dependency_wheel: Path | None,
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
    python, wheelhouse = populate_runtime(
        runtime, target, lock, wheel, dependency_wheel, work_dir
    )
    distribution = work_dir / f"openminion-runtime-{target_name}.tar.gz"
    archive_runtime(runtime, distribution)

    pyapp_source = work_dir / "pyapp"
    pyapp_source.mkdir()
    checkout_pyapp(pyapp_source)
    environment = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith("PYAPP_")
    }
    environment.update(pyapp_environment(version, target, distribution))
    run(["cargo", "build", "--release", "--locked"], cwd=pyapp_source, env=environment)

    artifact_name = f"openminion-{version}-{target_name}"
    if target["os"] == "windows":
        artifact_name += ".exe"
    artifact = output_dir / artifact_name
    shutil.copy2(
        pyapp_source
        / "target"
        / "release"
        / target["binary_name"].replace("openminion", "pyapp"),
        artifact,
    )
    artifact.chmod(artifact.stat().st_mode | 0o111)

    wheelhouse_manifest = work_dir / "wheelhouse.json"
    wheelhouse_manifest.write_text(json.dumps(wheelhouse, indent=2) + "\n")
    metadata = {
        "schema_version": 1,
        "target": target_name,
        "profile": PROFILE,
        "publishing": False,
        "wheel": wheel_record(wheel, version, origin, wheel_sha256),
        "prototype_dependency_wheel": (
            None
            if dependency_wheel is None
            else {
                "filename": dependency_wheel.name,
                "sha256": sha256(dependency_wheel),
            }
        ),
        "python": {
            "version": json.loads(INPUTS_PATH.read_text())["python_version"],
            "archive_url": target["archive_url"],
            "archive_sha256": target["archive_sha256"],
            "embedded_archive_sha256": sha256(distribution),
        },
        "pyapp": {
            "version": PYAPP_VERSION,
            "source": PYAPP_SOURCE,
            "commit": PYAPP_COMMIT,
            "cargo_lock_sha256": PYAPP_CARGO_LOCK_SHA256,
            "environment": pyapp_environment(version, target, distribution),
        },
        "tools": {
            "uv": UV_VERSION,
            "rustc": rustc_version,
            "cargo": run(["cargo", "--version"]),
        },
        "lock_sha256": sha256(lock),
        "wheelhouse_manifest_sha256": sha256(wheelhouse_manifest),
        "artifact": {
            "filename": artifact.name,
            "sha256": sha256(artifact),
            "size_bytes": artifact.stat().st_size,
        },
        "packages": installed_packages(target, runtime),
        "embedded_python": str(python.relative_to(runtime)),
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
        subparser.add_argument("--dependency-wheel", type=Path)
    subparsers.choices["lock"].add_argument("--check", action="store_true")
    subparsers.choices["build"].add_argument(
        "--output-dir", type=Path, default=ROOT / "dist"
    )
    return argument_parser


def main() -> None:
    args = parser().parse_args()
    version, requirements, _ = verify_wheel(
        args.wheel, args.wheel_origin, args.wheel_sha256
    )
    if args.command == "lock":
        write_lock(
            args.target,
            args.wheel,
            requirements,
            args.check,
            args.dependency_wheel,
        )
        return
    if version != OPENMINION_VERSION and args.wheel_origin == "pypi":
        raise ValueError(f"expected OpenMinion {OPENMINION_VERSION}")
    build(
        args.target,
        args.wheel,
        args.wheel_origin,
        args.wheel_sha256,
        args.dependency_wheel,
        args.output_dir,
    )


if __name__ == "__main__":
    main()
