"""Tests for packaged runtime smoke behavior."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

SMOKE_PATH = Path(__file__).parents[1] / "packaging" / "smoke.py"
SPEC = importlib.util.spec_from_file_location("openminion_packaging_smoke", SMOKE_PATH)
smoke = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(smoke)


class FakeProcess:
    def __init__(self) -> None:
        self.returncode = None
        self.signals: list[int] = []

    def poll(self) -> None:
        return None

    def send_signal(self, signal_number: int) -> None:
        self.signals.append(signal_number)

    def wait(self, timeout: int) -> int:
        del timeout
        self.returncode = 0
        return self.returncode


class SmokeTests(unittest.TestCase):
    def test_windows_stop_uses_targetable_break_event(self) -> None:
        process = FakeProcess()

        with (
            patch.object(smoke.os, "name", "nt"),
            patch.object(smoke.signal, "CTRL_BREAK_EVENT", 21, create=True),
        ):
            smoke.stop(process)

        self.assertEqual(process.signals, [21])

    def test_windows_control_exit_requires_daemon_cleanup(self) -> None:
        process = FakeProcess()
        process.returncode = smoke.WINDOWS_CONTROL_EXIT
        pid_file = Path("openminiond.pid")

        with (
            patch.object(smoke.os, "name", "nt"),
            patch.object(Path, "exists", return_value=False),
        ):
            self.assertTrue(smoke.stopped_cleanly(process, pid_file))

        with (
            patch.object(smoke.os, "name", "nt"),
            patch.object(Path, "exists", return_value=True),
        ):
            self.assertFalse(smoke.stopped_cleanly(process, pid_file))


if __name__ == "__main__":
    unittest.main()
