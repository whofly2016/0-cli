"""Regression checks for evidence boundaries, dates, and offline life planning."""

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "life-brief.py"
SPEC = importlib.util.spec_from_file_location("life_brief", SCRIPT)
brief = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(brief)


def sample_management():
    return {
        "north_star": {"statement": "Example vision", "status": "proposed"},
        "goals": [{"id": "draft", "status": "proposed", "title": "Draft goal"}],
        "century_plan": {
            "planning_horizon": {"age_years": 100},
            "date_of_birth": None,
            "health_plan": {"baseline": [
                {"id": "sleep", "name": "睡眠", "value": None, "observed_on": None, "source": None}
            ]},
        },
    }


class LifeBriefTests(unittest.TestCase):
    def test_unknown_age_and_baseline_are_not_guessed(self):
        report = "\n".join(brief.century_section(sample_management(), "2026-09-10"))
        self.assertIn("**当前年龄**：未知", report)
        self.assertIn("0/1 项", report)
        self.assertIn("规划假设，不是寿命预测", report)

    def test_proposals_are_not_counted_as_adopted(self):
        report = "\n".join(brief.management_section(sample_management(), {}, [], "2026-09-10"))
        self.assertIn("长期方向（候选）", report)
        self.assertIn("**已采纳且未完成目标**：0 个", report)
        self.assertIn("**候选目标**：1 个", report)

    def test_age_uses_report_date_and_birthday(self):
        data = sample_management()
        data["century_plan"]["date_of_birth"] = "1990-09-11"
        before = "\n".join(brief.century_section(data, "2026-09-10"))
        birthday = "\n".join(brief.century_section(data, "2026-09-11"))
        self.assertIn("35 周岁", before)
        self.assertIn("36 周岁", birthday)

    def test_invalid_and_future_birth_dates_stay_unknown(self):
        for birth in ("not-a-date", "2026-02-30", "2030-01-01"):
            with self.subTest(birth=birth):
                data = sample_management()
                data["century_plan"]["date_of_birth"] = birth
                self.assertIn("**当前年龄**：未知", "\n".join(brief.century_section(data, "2026-09-10")))

    def test_beyond_horizon_does_not_create_negative_lifetime(self):
        data = sample_management()
        data["century_plan"]["date_of_birth"] = "1920-01-01"
        report = "\n".join(brief.century_section(data, "2026-09-10"))
        self.assertIn("可延长规划", report)
        self.assertNotIn("-6", report)

    def test_baseline_requires_source_and_nonfuture_valid_date(self):
        data = sample_management()
        data["century_plan"]["health_plan"]["baseline"] = [
            {"name": "valid", "value": 0, "source": "user", "observed_on": "2026-09-09"},
            {"name": "future", "value": 7, "source": "user", "observed_on": "2026-09-11"},
            {"name": "unsourced", "value": 7, "source": None, "observed_on": "2026-09-09"},
            {"name": "invalid", "value": 7, "source": "user", "observed_on": "yesterday"},
        ]
        report = "\n".join(brief.century_section(data, "2026-09-10"))
        self.assertIn("1/4 项", report)

    def test_offline_report_never_reads_remote_data(self):
        with patch.object(brief, "collect_tasks", side_effect=AssertionError("remote read")), patch.object(
            brief, "collect_agenda", side_effect=AssertionError("remote read")
        ):
            report = brief.generate_report("2026-09-10", 7, {"life": "life"}, management=sample_management(), offline=True)
        self.assertIn("未获取飞书任务或日程", report)
        self.assertNotIn("未完成 0 项", report)

    def test_offline_json_cli_has_explicit_remote_status(self):
        with tempfile.TemporaryDirectory() as folder:
            management = Path(folder) / "management.json"
            management.write_text(json.dumps(sample_management()), encoding="utf-8")
            argv = [str(SCRIPT), "--offline", "--json", "--management", str(management),
                    "--no-entities", "--events", str(Path(folder) / "missing.jsonl")]
            output = io.StringIO()
            with patch.object(brief.sys, "argv", argv), redirect_stdout(output), patch.object(
                brief, "run_lark", side_effect=AssertionError("remote read")
            ):
                brief.main()
            result = json.loads(output.getvalue())
            self.assertTrue(result["offline"])
            self.assertEqual(result["remote_status"], "not_fetched")

    def test_past_plans_and_closed_processes(self):
        entities = {
            "p": {"id": "p", "type": "process", "canonical": "Open"},
            "closed": {"id": "closed", "type": "process", "canonical": "CLOSED_MARKER", "status": "completed"},
        }
        events = [{"object": "p", "state": "planned", "when": "2026-09-09", "action": "Review"}]
        report = "\n".join(brief.process_section(entities, events, "2026-09-10"))
        self.assertIn("计划已过期，待核实", report)
        self.assertNotIn("CLOSED_MARKER", report)
        self.assertNotIn("计划已过期", "\n".join(brief.process_section(entities, events, "2026-09-08")))

    def test_task_overdue_uses_report_date(self):
        task = {"summary": "Task", "due_at": "2026-09-09"}
        self.assertIn("⬜", brief.fmt_task(task, report_date="2026-09-08"))
        self.assertIn("🔴", brief.fmt_task(task, report_date="2026-09-10"))

    def test_corrupt_management_is_not_silently_empty(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "broken.json"
            target.write_text("{broken", encoding="utf-8")
            with self.assertRaises(ValueError):
                brief.load_management(target)

    def test_online_json_uses_requested_multiday_window(self):
        argv = [str(SCRIPT), "--json", "--date", "2026-09-10", "--days", "7", "--profiles", "life"]
        with patch.object(brief.sys, "argv", argv), patch.object(brief, "collect_tasks", return_value={"items": []}), patch.object(
            brief, "collect_agenda", return_value={"items": []}
        ) as agenda, redirect_stdout(io.StringIO()):
            brief.main()
        agenda.assert_called_once_with("life", "2026-09-10T00:00:00+08:00", "2026-09-17T00:00:00+08:00")

    def test_review_template_includes_sections(self):
        management = sample_management()
        management["goals"] = [{"id": "g1", "status": "active", "title": "Goal", "next_action": "Do it"}]
        entities = {"p": {"id": "p", "type": "process", "canonical": "Open", "current_stage": "stage1"}}
        events = [{"object": "p", "state": "completed", "when": "2026-09-09", "action": "Done"}]
        report = brief.generate_review("2026-09-10", 7, {"life": "life"}, entities=entities, events=events, management=management, offline=True)
        self.assertIn("# 人生复盘", report)
        self.assertIn("## 已完成事项", report)
        self.assertIn("## 进行中过程", report)
        self.assertIn("## 目标进展", report)
        self.assertIn("## 复盘问题", report)

    def test_diff_outputs_unified_diff(self):
        with tempfile.TemporaryDirectory() as folder:
            previous = Path(folder) / "prev.md"
            previous.write_text("line1\nline2\n", encoding="utf-8")
            argv = [str(SCRIPT), "--offline", "--no-entities", "--diff", str(previous)]
            output = io.StringIO()
            with patch.object(brief.sys, "argv", argv), redirect_stdout(output), patch.object(
                brief, "run_lark", side_effect=AssertionError("remote read")
            ):
                brief.main()
            result = output.getvalue()
            self.assertIn("---", result)
            self.assertIn("+++", result)
            self.assertIn("@@", result)


if __name__ == "__main__":
    unittest.main()
