"""Unit tests for frontend/tools/browser_check.py (Member 2, Q4).

These cover the runner's own machinery without a browser: WebSocket framing and handshake
key, fail-closed result accounting, PowerShell-compatible glob matching, path confinement and
MIME types of the local servers, and authoritative browser selection. The 47 browser checks
themselves need Chrome and run through `python frontend/tools/browser_check.py`.
"""

import importlib.util
import io
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "browser_check", ROOT / "frontend" / "tools" / "browser_check.py"
)
bc = importlib.util.module_from_spec(_spec)
sys.modules["browser_check"] = bc
_spec.loader.exec_module(bc)


# --- WebSocket ---------------------------------------------------------------------


def test_accept_key_matches_rfc6455_example():
    assert bc.accept_key("dGhlIHNhbXBsZSBub25jZQ==") == "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="


@pytest.mark.parametrize("size", [0, 5, 125, 126, 300, 65535, 65536, 70000])
def test_masked_client_frame_round_trips(size):
    payload = bytes(i % 251 for i in range(size))
    frame = bc.encode_frame(payload, mask=b"\x01\x02\x03\x04")
    assert frame[0] == 0x81  # FIN + text
    assert frame[1] & 0x80  # client frames must be masked
    stream = io.BytesIO(frame)
    fin, opcode, decoded = bc.decode_frame(stream.read)
    assert (fin, opcode, decoded) == (True, 0x1, payload)
    assert stream.read() == b""


def test_unmasked_server_frame_with_16_bit_length_decodes():
    payload = b"x" * 200
    frame = bytes([0x81, 126]) + (200).to_bytes(2, "big") + payload
    assert bc.decode_frame(io.BytesIO(frame).read) == (True, 0x1, payload)


# --- fail-closed accounting --------------------------------------------------------


def _results(n_ok, n_fail=0, expected=47):
    r = bc.Results(expected=expected, out=lambda *_: None)
    for i in range(n_ok):
        r.check(f"ok {i}", True)
    for i in range(n_fail):
        r.check(f"bad {i}", False, "detail")
    return r


def test_full_clean_run_passes():
    assert _results(47).exit_code() == 0


@pytest.mark.parametrize(
    ("n_ok", "n_fail", "expected"),
    [(46, 1, 47), (46, 0, 47), (48, 0, 47), (0, 0, 47), (0, 0, 0)],
    ids=["one-failure", "missing-check", "extra-check", "zero-checks", "zero-even-if-any"],
)
def test_anything_but_a_full_clean_run_fails(n_ok, n_fail, expected):
    assert _results(n_ok, n_fail, expected).exit_code() == 1


def test_abort_fails_even_after_passing_checks():
    r = _results(47)
    r.abort("RuntimeError: DevTools closed")
    assert r.exit_code() == 1
    assert "aborted" in r.summary()


def test_summary_flags_an_incomplete_run():
    assert "INCOMPLETE" in _results(40).summary()


# --- matching, paths, MIME, browser selection ----------------------------------------


def test_like_is_case_insensitive_glob_like_powershell():
    assert bc.like("A | #main | Skip to content | ring | visible", "a | #MAIN*ring*visible")
    assert not bc.like("A | #main | x | NO-RING | visible", "*| ring |*")
    assert bc.like("rgb(1, 2, 3)/7", "*/7")


def test_confine_keeps_paths_inside_the_root(tmp_path):
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    assert bc.confine(str(tmp_path), "a.txt") == str((tmp_path / "a.txt").resolve())
    outside = bc.confine(str(tmp_path), "../../etc/passwd")
    assert outside.endswith("__outside_root__")


def test_static_server_mime_mount_and_traversal(tmp_path):
    front = tmp_path / "frontend"
    examples = tmp_path / "contracts" / "examples"
    front.mkdir(parents=True)
    examples.mkdir(parents=True)
    (front / "app.js").write_text("export {};", encoding="utf-8")
    (examples / "health.example.json").write_text("{}", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("no", encoding="utf-8")
    server, base = bc.start_server(front, contracts=examples)
    try:
        with urllib.request.urlopen(base + "app.js") as r:  # noqa: S310 (local test server)
            assert r.headers["Content-Type"].startswith("text/javascript")
        with urllib.request.urlopen(base + "contracts/examples/health.example.json") as r:  # noqa: S310
            assert r.status == 200
        with pytest.raises(urllib.error.HTTPError) as err:
            urllib.request.urlopen(base + "..%2fsecret.txt")  # noqa: S310
        assert err.value.code == 404
    finally:
        server.shutdown()


def test_explicit_browser_path_is_authoritative(tmp_path, monkeypatch):
    monkeypatch.delenv("CHROME", raising=False)
    assert bc.find_chrome(str(tmp_path / "nope")) is None
    monkeypatch.setenv("CHROME", str(tmp_path / "nope"))
    assert bc.find_chrome(None) is None


def test_missing_browser_exits_nonzero(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("CHROME", raising=False)
    assert bc.main(["--chrome", str(tmp_path / "nope")]) == 2
    assert "FAIL" in capsys.readouterr().out
