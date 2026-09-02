from __future__ import annotations

import argparse
import tempfile
import unittest
from pathlib import Path

from scripts import work_timer


class WorkTimerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.ledger = Path(self.temporary.name) / "timer.json"
        work_timer.command_init(
            argparse.Namespace(
                ledger=self.ledger,
                work_item="CASE-1",
                source_id="codex-1",
                source_kind="harness",
            )
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def mark(self, state: str) -> None:
        work_timer.command_mark(
            argparse.Namespace(ledger=self.ledger, state=state, at=None, reason=None)
        )

    def test_pause_requires_resume(self) -> None:
        self.mark("work_started")
        self.mark("pause_started")
        with self.assertRaises(work_timer.TimerError):
            self.mark("ready_for_handoff")
        self.mark("resume")
        self.mark("ready_for_handoff")
        self.mark("handoff")
        source = work_timer.command_export(
            argparse.Namespace(ledger=self.ledger, output=None)
        )
        self.assertEqual(source["coverage"]["status"], "complete")

    def test_terminal_stop_cannot_resume(self) -> None:
        self.mark("work_started")
        self.mark("user_stopped")
        with self.assertRaises(work_timer.TimerError):
            self.mark("resume")


if __name__ == "__main__":
    unittest.main()
