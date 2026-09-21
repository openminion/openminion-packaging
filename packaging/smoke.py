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


def available_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def wait_for_health(port: int, process: subprocess.Popen[str], log_path: Path) -> dict:
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise RuntimeError(
                f"foreground daemon exited early ({process.returncode})\n{stdout}\n{stderr}"
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
    daemon_log = (
        log_path.read_text(encoding="utf-8", errors="replace")[-8000:]
        if log_path.is_file()
        else "daemon log was not created"
    )
    raise TimeoutError(
        "foreground daemon health endpoint did not become ready\n" + daemon_log
    )


def stop(process: subprocess.Popen[str], *, require_graceful: bool = True) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        process.send_signal(signal.CTRL_C_EVENT)
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", required=True, type=Path)
    parser.add_argument("--daemon", required=True, type=Path)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    for executable in (args.cli, args.daemon):
        if not executable.is_file():
            parser.error(f"missing executable: {executable}")

    with tempfile.TemporaryDirectory(prefix="openminion-packaged-smoke-") as directory:
        root = Path(directory)
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
                str(root / "openminiond.pid"),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=environment,
            creationflags=creationflags,
        )
        try:
            health = wait_for_health(port, process, root / "data/logs/openminiond.log")
        except Exception:
            stop(process, require_graceful=False)
            raise
        stop(process)
        if process.returncode != 0:
            stdout, stderr = process.communicate()
            raise RuntimeError(
                f"foreground daemon stopped with {process.returncode}\n{stdout}\n{stderr}"
            )
        if (root / "openminiond.pid").exists():
            raise RuntimeError(
                "foreground daemon left its PID file after graceful stop"
            )
        print(json.dumps({"version": version, "health": health}, sort_keys=True))


if __name__ == "__main__":
    main()
