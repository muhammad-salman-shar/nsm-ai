import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from src.brain import Brain
from src import persistence

DEFAULT_STATE = "data/brain_state.json"
STATIC_DIR = "static"
_brain = None


def get_brain():
    global _brain
    if _brain is None:
        _brain = Brain(auto_save_path=DEFAULT_STATE)
    return _brain


def _json_response(handler, status, data):
    body = json.dumps(data).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(body)


def _html_response(handler, path):
    if not os.path.exists(path):
        handler.send_error(404)
        return
    with open(path, "rb") as f:
        content = f.read()
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(content)))
    handler.end_headers()
    handler.wfile.write(content)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            _html_response(self, os.path.join(STATIC_DIR, "index.html"))
        elif parsed.path == "/state":
            _json_response(self, 200, get_brain().state())
        elif parsed.path == "/health":
            _json_response(self, 200, {"ok": True})
        else:
            handler_404(self)

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b""
            data = json.loads(raw) if raw else {}
        except (json.JSONDecodeError, ValueError):
            _json_response(self, 400, {"error": "invalid json"})
            return

        if parsed.path == "/chat":
            text = (data.get("text") or "").strip()
            if not text:
                _json_response(self, 400, {"error": "empty text"})
                return
            result = get_brain().observe(text)
            _json_response(self, 200, result)
        elif parsed.path == "/reset":
            global _brain
            persistence.reset(DEFAULT_STATE)
            _brain = Brain(auto_save_path=DEFAULT_STATE)
            _json_response(self, 200, {"ok": True, "message": "reset"})
        else:
            handler_404(self)


def handler_404(handler):
    _json_response(handler, 404, {"error": "not found"})


def run(host="0.0.0.0", port=8000):
    os.makedirs(STATIC_DIR, exist_ok=True)
    server = HTTPServer((host, port), Handler)
    print(f"NSM VB server on http://{host}:{port}")
    print(f"Open in browser: http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down...")
        server.shutdown()


if __name__ == "__main__":
    run()
