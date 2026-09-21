"""Exercise the paired packaged CLI and foreground daemon on a native host."""

from __future__ import annotations

import argparse
import http.client
import json
import os
import signal
import socket
import subprocess
import tempfile
import time
from pathlib import Path

WINDOWS_CONTROL_EXIT = 0xC000013A
WINDOWS_DAEMON_CLEANUP_TIMEOUT_SECONDS = 30


def available_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def log_tail(path: Path) -> str:
    if not path.is_file():
        return f"{path.name} was not created"
    return path.read_text(encoding="utf-8", errors="replace")[-8000:]


def wait_for_health(
    port: int,
    process: subprocess.Popen[str],
    daemon_log_path: Path,
    stdout_path: Path,
    stderr_path: Path,
) -> dict:
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                f"foreground daemon exited early ({process.returncode})\n"
                f"stdout:\n{log_tail(stdout_path)}\n"
                f"stderr:\n{log_tail(stderr_path)}"
            )
        try:
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=1)
            connection.request("GET", "/health")
            response = connection.getresponse()
            body = response.read()
            connection.close()
            if response.status == 200:
                return json.loads(body)
        except (ConnectionError, OSError, TimeoutError):
            pass
        time.sleep(0.2)
    raise TimeoutError(
        "foreground daemon health endpoint did not become ready\n"
        f"daemon log:\n{log_tail(daemon_log_path)}\n"
        f"stdout:\n{log_tail(stdout_path)}\n"
        f"stderr:\n{log_tail(stderr_path)}"
    )


def stop(process: subprocess.Popen[str], *, require_graceful: bool = True) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        process.send_signal(signal.CTRL_BREAK_EVENT)
    else:
        process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            completed = subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode != 0 and process.poll() is None:
                raise RuntimeError(
                    "failed to terminate foreground daemon process tree\n"
                    f"{completed.stdout}\n{completed.stderr}"
                )
        else:
            process.kill()
        process.wait(timeout=10)
        if require_graceful:
            raise RuntimeError(
                "foreground daemon did not stop after its supported signal"
            )


def stopped_cleanly(process: subprocess.Popen[str], pid_file: Path) -> bool:
    if process.returncode == 0:
        return True
    return (
        os.name == "nt"
        and process.returncode == WINDOWS_CONTROL_EXIT
        and not pid_file.exists()
    )


def wait_for_daemon_cleanup(pid_file: Path, *, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while pid_file.exists() and time.monotonic() < deadline:
        time.sleep(0.1)
    return not pid_file.exists()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", required=True, type=Path)
    parser.add_argument("--daemon", required=True, type=Path)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    for executable in (args.cli, args.daemon):
        if not executable.is_file():
            parser.error(f"missing executable: {executable}")

    with tempfile.TemporaryDirectory(
        prefix="openminion-packaged-smoke-",
        ignore_cleanup_errors=os.name == "nt",
    ) as directory:
        root = Path(directory)
        pid_file = root / "openminiond.pid"
        environment = {
            **os.environ,
            "OPENMINION_HOME": str(root / "home"),
            "OPENMINION_DATA_ROOT": str(root / "data"),
            "PYAPP_INSTALL_DIR_OPENMINION": str(root / "installed"),
        }
        version = subprocess.run(
            [str(args.cli), "--version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=90,
            env=environment,
        ).stdout.strip()
        if version != args.version:
            raise ValueError(
                f"packaged CLI reported {version!r}, expected {args.version!r}"
            )

        config = root / "config.json"
        config.write_text(
            json.dumps(
                {
                    "agents": {
                        "openminion": {"name": "openminion", "provider": "echo"}
                    },
                    "providers": {"echo": {"model": "echo"}},
                }
            )
            + "\n"
        )
        port = available_port()
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        stdout_path = root / "daemon.stdout.log"
        stderr_path = root / "daemon.stderr.log"
        with (
            stdout_path.open("w", encoding="utf-8") as stdout_stream,
            stderr_path.open("w", encoding="utf-8") as stderr_stream,
        ):
            process = subprocess.Popen(
                [
                    str(args.daemon),
                    "serve",
                    "--config",
                    str(config),
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                    "--pid-file",
                    str(pid_file),
                ],
                stdout=stdout_stream,
                stderr=stderr_stream,
                text=True,
                env=environment,
                creationflags=creationflags,
            )
            try:
                health = wait_for_health(
                    port,
                    process,
                    root / "data/logs/openminiond.log",
                    stdout_path,
                    stderr_path,
                )
            except Exception:
                stop(process, require_graceful=False)
                raise
            stop(process)
        if os.name == "nt" and process.returncode == WINDOWS_CONTROL_EXIT:
            wait_for_daemon_cleanup(
                pid_file,
                timeout=WINDOWS_DAEMON_CLEANUP_TIMEOUT_SECONDS,
            )
        if not stopped_cleanly(process, pid_file):
            raise RuntimeError(
                f"foreground daemon stopped with {process.returncode}\n"
                f"pid file present: {pid_file.exists()}\n"
                f"stdout:\n{log_tail(stdout_path)}\n"
                f"stderr:\n{log_tail(stderr_path)}"
            )
        if pid_file.exists():
            raise RuntimeError(
                "foreground daemon left its PID file after graceful stop"
            )
        print(json.dumps({"version": version, "health": health}, sort_keys=True))


if __name__ == "__main__":
    main()
