"""Retry logic test using a local HTTP server (no internet needed)."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from q10_api_client import fetch_json


def make_server(fail_times):
    state = {"calls": 0}

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            state["calls"] += 1
            code = 503 if state["calls"] <= fail_times else 200
            self.send_response(code)
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, state


def test_retries_then_succeeds(tmp_path):
    srv, state = make_server(fail_times=2)
    data = fetch_json(f"http://127.0.0.1:{srv.server_port}/", tmp_path / "r.json",
                      retries=3, backoff=0.01)
    assert data == {"ok": True} and state["calls"] == 3
    assert json.loads((tmp_path / "r.json").read_text()) == {"ok": True}
    srv.shutdown()


def test_gives_up_after_max_retries(tmp_path):
    srv, state = make_server(fail_times=99)
    with pytest.raises(RuntimeError):
        fetch_json(f"http://127.0.0.1:{srv.server_port}/", tmp_path / "r.json",
                   retries=2, backoff=0.01)
    assert state["calls"] == 2
    srv.shutdown()
