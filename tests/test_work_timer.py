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

    def test_mixed_offsets_are_ordered_by_instant(self) -> None:
        work_timer.command_mark(
            argparse.Namespace(
                ledger=self.ledger,
                state="work_started",
                at="2026-03-01T10:00:00+05:00",
                reason=None,
            )
        )
        work_timer.command_mark(
            argparse.Namespace(
                ledger=self.ledger,
                state="work_finished",
                at="2026-03-01T08:00:00+00:00",
                reason=None,
            )
        )
        source = work_timer.command_export(
            argparse.Namespace(ledger=self.ledger, output=None)
        )
        self.assertEqual(source["coverage"]["started_at"], "2026-03-01T10:00:00+05:00")
        self.assertEqual(source["coverage"]["ended_at"], "2026-03-01T08:00:00+00:00")

    def test_earlier_event_is_rejected(self) -> None:
        work_timer.command_mark(
            argparse.Namespace(
                ledger=self.ledger,
                state="work_started",
                at="2026-03-01T10:00:00+00:00",
                reason=None,
            )
        )
        with self.assertRaises(work_timer.TimerError):
            work_timer.command_pulse(
                argparse.Namespace(
                    ledger=self.ledger,
                    at="2026-03-01T09:00:00+00:00",
                    category="model",
                )
            )


if __name__ == "__main__":
    unittest.main()
