"""The frontend CI runner must fail closed: only a clean PASS n/n with n > 0 is a pass."""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "run_frontend_tests", ROOT / ".github" / "scripts" / "run_frontend_tests.py"
)
runner = importlib.util.module_from_spec(_spec)
sys.modules["run_frontend_tests"] = runner
_spec.loader.exec_module(runner)


def page(title, results=""):
    body = f'<pre id="results">{results}</pre>'
    return f"<html><head><title>{title}</title></head><body>{body}</body></html>"


def test_clean_pass():
    out = runner.parse_dom(page("PASS 65/65", "ok 1\n65 passed, 0 failed, 65 total"))
    assert out.ok and out.summary == "PASS 65/65" and out.failures == ()


def test_failure_lists_the_failing_tests():
    dom = page("FAIL 2/65", "FAIL filter: empty filters\n  Error: x\nFAIL model: other &amp; more")
    out = runner.parse_dom(dom)
    assert not out.ok and out.summary == "FAIL 2/65"
    assert out.failures == ("FAIL filter: empty filters", "FAIL model: other & more")


@pytest.mark.parametrize(
    "dom",
    [
        "",
        "<html><head><title>layout test</title></head></html>",  # harness never reported
        "<html><body>Chrome error page</body></html>",
        page("PASS 0/0"),  # zero tests is not a pass
        page("PASS 5/65"),  # not every test passed
    ],
    ids=["empty", "no-result", "error-page", "zero-tests", "partial"],
)
def test_anything_unexpected_is_a_failure(dom):
    assert not runner.parse_dom(dom).ok


def test_pass_title_with_a_failing_line_is_still_a_failure():
    """The title and the result list must agree; a contradiction fails closed."""
    assert not runner.parse_dom(page("PASS 3/3", "FAIL something broke")).ok


def test_missing_harness_is_skipped_not_passed(tmp_path, capsys):
    assert runner.main(["--root", str(tmp_path)]) == 0
    assert "SKIPPED (not verified)" in capsys.readouterr().out


def test_missing_harness_fails_when_required(tmp_path, capsys):
    assert runner.main(["--root", str(tmp_path), "--require"]) == 1
    assert "FAIL" in capsys.readouterr().out


def _with_harness(tmp_path):
    (tmp_path / "frontend" / "tests").mkdir(parents=True)
    (tmp_path / "frontend" / "tests" / "index.html").write_text("<html></html>", encoding="utf-8")


def test_explicit_chrome_path_is_authoritative(tmp_path, capsys, monkeypatch):
    _with_harness(tmp_path)
    monkeypatch.delenv("CHROME", raising=False)
    assert runner.main(["--root", str(tmp_path), "--chrome", str(tmp_path / "nope")]) == 1
    assert "no Chrome" in capsys.readouterr().out


def test_chrome_env_var_is_authoritative_too(tmp_path, monkeypatch):
    monkeypatch.setenv("CHROME", str(tmp_path / "nope"))
    assert runner.find_chrome(None) is None


def test_run_reports_a_chrome_crash_as_failure(tmp_path, monkeypatch):
    _with_harness(tmp_path)
    fake = tmp_path / "chrome"
    fake.write_text("#!/bin/sh\nexit 3\n", encoding="utf-8")
    fake.chmod(0o755)
    outcome = runner.run(tmp_path, str(fake), timeout=20)
    assert not outcome.ok and "Chrome exited 3" in outcome.summary
