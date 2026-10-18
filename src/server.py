import time
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from src.brain import Brain
from src import persistence
from src import database

DEFAULT_STATE = "data/brain_state.json"
STATIC_DIR = "static"
_brain_cache = {}

def get_brain(user_id="default"):
    if user_id not in _brain_cache:
        # Create fresh brain
        b = Brain(auto_save_path=None)
        # Try loading from SQLite database
        state = database.load_brain(user_id)
        if state:
            persistence.from_dict(b, state)
        _brain_cache[user_id] = b
    return _brain_cache[user_id]


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

        if parsed.path == "/v1/chat/completions":
            messages = data.get("messages", [])
            text = ""
            if messages:
                # Get the last message from user
                for msg in reversed(messages):
                    if msg.get("role") == "user":
                        text = msg.get("content", "")
                        break
            if not text:
                _json_response(self, 400, {"error": "no user message"})
                return
            
            user_id = data.get("user_id", "default")
            brain = get_brain(user_id)
            result = brain.observe(text)
            database.save_brain(user_id, persistence.to_dict(brain))
            response_text = result["response"]
            
            # Check if the app is asking for a stream
            if data.get("stream", False):
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                
                # Split by words to simulate token streaming
                words = response_text.split(" ")
                for i, word in enumerate(words):
                    chunk_text = word + (" " if i < len(words) - 1 else "")
                    chunk_data = {
                        "id": "chatcmpl-nsm",
                        "object": "chat.completion.chunk",
                        "model": "nsm-vb",
                        "choices": [{"index": 0, "delta": {"content": chunk_text}, "finish_reason": None}]
                    }
                    self.wfile.write(f"data: {json.dumps(chunk_data)}\n\n".encode())
                    self.wfile.flush()
                    time.sleep(0.05)
                
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()
                return

            # If not streaming, send normal JSON
            openai_resp = {
                "id": "chatcmpl-nsm",
                "object": "chat.completion",
                "created": 1234567890,
                "model": "nsm-vb",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": result["response"]
                    },
                    "finish_reason": "stop"
                }]
            }
            _json_response(self, 200, openai_resp)

        elif parsed.path == "/chat":
            text = (data.get("text") or "").strip()
            if not text:
                _json_response(self, 400, {"error": "empty text"})
                return
            user_id = data.get("user_id", "default")
            brain = get_brain(user_id)
            result = brain.observe(text)
            database.save_brain(user_id, persistence.to_dict(brain))
            _json_response(self, 200, result)
        elif parsed.path == "/reset":
            user_id = data.get("user_id", "default")
            database.delete_brain(user_id)
            if user_id in _brain_cache:
                del _brain_cache[user_id]
            _json_response(self, 200, {"ok": True, "message": f"reset for {user_id}"})
        else:
            handler_404(self)


def handler_404(handler):
    _json_response(handler, 404, {"error": "not found"})


def run(host="0.0.0.0", port=8081):
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
