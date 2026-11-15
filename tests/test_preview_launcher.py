"""The double-click launchers must serve and open the SAME address, even when 8790 is busy.

Found in the final rehearsal: with an old preview on 8790 the launcher printed a port error and then
still opened http://127.0.0.1:8790/, which showed the OLD preview. The launchers now delegate to
`run.py --auto-port --open`, which opens the address it actually serves, and only once it is ready.
"""

import importlib.util
import socket
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("preview_run", ROOT / "preview" / "run.py")
run = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = run
_spec.loader.exec_module(run)


def occupy(port):
    sock = socket.socket()
    sock.bind(("127.0.0.1", port))
    sock.listen(128)
    return sock


def free_base():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_pick_port_skips_busy_ports_and_is_deterministic():
    base = free_base()
    holders = []
    try:
        assert run.pick_port(base) == base
        holders.append(occupy(base))
        assert run.pick_port(base) == base + 1
        try:
            holders.append(occupy(base + 1))
        except OSError:
            pytest.skip("neighbouring port in use")
        assert run.pick_port(base) == base + 2
        assert run.port_is_free(base) is False
    finally:
        for h in holders:
            h.close()


def test_pick_port_gives_up_clearly_when_nothing_is_free():
    base = free_base()
    holder = occupy(base)
    try:
        with pytest.raises(SystemExit, match="No free port"):
            run.pick_port(base, tries=1)
    finally:
        holder.close()


def test_the_launchers_delegate_to_auto_port_and_open_and_never_open_a_fixed_address():
    for name in ("Start-Preview-Mac.command", "Start-Preview-Windows.bat"):
        text = (ROOT / "preview" / name).read_text(encoding="utf-8")
        assert "preview/run.py --auto-port --open" in text.replace("\\", "/"), name
        assert "127.0.0.1:8790" not in text, f"{name} must not open a hard-coded address"
        assert "sleep 12" not in text and "timeout /t" not in text, "no blind wait-then-open"


def test_run_py_opens_the_browser_only_after_the_server_is_ready_and_on_its_own_url():
    src = (ROOT / "preview" / "run.py").read_text(encoding="utf-8")
    ready = src.index("wait_ready(url)")
    opened = src.index("webbrowser.open(url)")
    assert ready < opened, "the browser must not open before the server answers"
    assert 'url = f"http://127.0.0.1:{args.port}/"' in src
    assert src.index("args.port = chosen") < src.index('url = f"http://127.0.0.1:{args.port}/"')


def test_a_failed_git_fetch_does_not_block_a_demo():
    src = (ROOT / "preview" / "run.py").read_text(encoding="utf-8")
    assert "check=False" in src[src.index('"fetch"') - 80 : src.index('"fetch"') + 200]
    assert "Could not reach GitHub" in src


def test_the_illustrations_are_pinned_exported_and_labelled():
    import json

    pins = json.loads((ROOT / "preview" / "pins.json").read_text(encoding="utf-8"))
    assert pins["illustrations"]["ref"] == "origin/viz/blender-illustrative"
    assert len(pins["illustrations"]["sha"]) == 40
    gallery = (ROOT / "preview" / "gallery.html").read_text(encoding="utf-8")
    assert "ILLUSTRATION ONLY. Not a validated combustion simulation. Not NASA data." in gallery
    for name in ("earth", "mars", "moon", "microgravity"):
        assert f'src="{name}.png"' in gallery
    server = (ROOT / "preview" / "server.py").read_text(encoding="utf-8")
    assert '"/illustrations"' in server and "add_api_route" not in server
