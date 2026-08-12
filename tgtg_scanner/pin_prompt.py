"""Browser-based PIN prompt for Docker / headless login flows."""

from __future__ import annotations

import html
import logging
import threading
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, HTTPServer
from importlib.resources import files
from urllib.parse import parse_qs, urlparse

log = logging.getLogger("tgtg")


@lru_cache(maxsize=1)
def _load_templates() -> tuple[str, str]:
    static = files("tgtg_scanner") / "static"
    css = (static / "pin.css").read_text(encoding="utf-8")
    form = (static / "pin_form.html").read_text(encoding="utf-8").replace("/* __CSS__ */", css)
    done = (static / "pin_done.html").read_text(encoding="utf-8").replace("/* __CSS__ */", css)
    return form, done


def prompt_via_browser(*, email: str | None = None, port: int = 0) -> str | None:
    """Serve a one-shot HTML form for the TGTG email PIN and return the value."""
    done = threading.Event()
    result: dict[str, str | None] = {"value": None}
    form_tpl, done_page = _load_templates()
    form_page = form_tpl.replace("__EMAIL__", html.escape(email) if email else "your TGTG account")

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args, **_kwargs) -> None:
            return

        def _send(self, code: int, body: str) -> None:
            data = body.encode()
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:  # noqa: N802
            if self.path.startswith("/submit"):
                qs = parse_qs(urlparse(self.path).query)
                result["value"] = (qs.get("value", [""])[0]).strip()
                self._send(200, done_page)
                done.set()
                return
            self._send(200, form_page)

    server = HTTPServer(("0.0.0.0", port), Handler)
    threading.Thread(target=lambda: _serve(server, done), daemon=True).start()
    log.info("Enter PIN for %s: http://localhost:%s/", email or "TGTG", server.server_port)
    done.wait()
    server.server_close()
    return result["value"]


def _serve(server: HTTPServer, done: threading.Event) -> None:
    while not done.is_set():
        server.handle_request()
