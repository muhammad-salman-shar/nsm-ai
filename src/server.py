"""Thread-safe HTTP server for NSM VB v1.4 (Android WebView + API + OpenAI compatible)."""

import json
import os
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from src import cortex_api, storage
from src.brain import Brain

STATIC_DIR = "static"
_CACHE_LOCK = threading.RLock()
_BRAIN_CACHE = {}
_BRAIN_LOCKS = {}


def _get_lock(user_id: str) -> threading.RLock:
    with _CACHE_LOCK:
        if user_id not in _BRAIN_LOCKS:
            _BRAIN_LOCKS[user_id] = threading.RLock()
        return _BRAIN_LOCKS[user_id]


def get_brain(user_id: str = "default") -> Brain:
    uid = storage.sanitize_user_id(user_id)
    with _CACHE_LOCK:
        if uid in _BRAIN_CACHE:
            return _BRAIN_CACHE[uid]

    # Load from SQLite (overlay public -> personal if present)
    public_state = storage.load_brain("public") if uid != "public" else None
    personal_state = storage.load_brain(uid)

    if public_state and personal_state:
        combined = storage.merge_brain_data(public_state, personal_state)
        brain = Brain.from_dict(combined)
    elif personal_state:
        brain = Brain.from_dict(personal_state)
    elif public_state:
        brain = Brain.from_dict(public_state)
    else:
        brain = Brain(seed_core=True)

    with _CACHE_LOCK:
        _BRAIN_CACHE[uid] = brain
    return brain


def _invalidate_brain(user_id: str) -> None:
    uid = storage.sanitize_user_id(user_id)
    with _CACHE_LOCK:
        _BRAIN_CACHE.pop(uid, None)


def _send_json(handler: BaseHTTPRequestHandler, status: int, data: dict) -> None:
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _send_html(handler: BaseHTTPRequestHandler, path: str) -> None:
    if not os.path.exists(path):
        handler.send_error(404, "index.html not found")
        return
    with open(path, "rb") as f:
        content = f.read()
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(content)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(content)


class NSMThreadingServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        user_id = qs.get("user_id", ["default"])[0]

        try:
            if parsed.path in ("/", "/index.html"):
                _send_html(self, os.path.join(STATIC_DIR, "index.html"))
            elif parsed.path == "/health":
                _send_json(self, 200, {
                    "ok": True,
                    "service": "NSM VB",
                    "version": Brain.VERSION,
                    "port": 8081,
                })
            elif parsed.path == "/state":
                brain = get_brain(user_id)
                _send_json(self, 200, brain.state())
            elif parsed.path == "/brains":
                brains = storage.list_brains()
                if "default" not in brains:
                    brains.insert(0, "default")
                _send_json(self, 200, {"brains": brains})
            elif parsed.path == "/debug":
                data_dir = storage.get_data_dir()
                db_path = storage.get_db_path()
                crash_log = ""
                crash_path = os.path.join(data_dir, "crash.log")
                if os.path.exists(crash_path):
                    try:
                        with open(crash_path, "r", encoding="utf-8", errors="replace") as f:
                            crash_log = f.read()[-1200:]
                    except Exception:
                        pass
                _send_json(self, 200, {
                    "version": Brain.VERSION,
                    "data_dir": data_dir,
                    "db_path": db_path,
                    "db_exists": os.path.exists(db_path),
                    "cached_brains": list(_BRAIN_CACHE.keys()),
                    "crash_log": crash_log or "No crash log",
                    "cwd": os.getcwd(),
                })
            else:
                _send_json(self, 404, {"error": "Endpoint not found"})
        except Exception as e:
            _send_json(self, 500, {"error": str(e)})

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length > 0 else b""
            data = json.loads(raw.decode("utf-8")) if raw else {}
            if not isinstance(data, dict):
                _send_json(self, 400, {"error": "JSON body must be an object"})
                return
        except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
            _send_json(self, 400, {"error": "Invalid JSON payload"})
            return

        try:
            if parsed.path == "/chat":
                text = (data.get("text") or "").strip()
                if not text:
                    _send_json(self, 400, {"error": "Empty text"})
                    return
                uid = storage.sanitize_user_id(data.get("user_id", "default"))
                with _get_lock(uid):
                    brain = get_brain(uid)
                    result = brain.observe_bulk(
                        text,
                        llm_url=data.get("llm_url"),
                        llm_model=data.get("llm_model"),
                        llm_key=data.get("llm_key"),
                    )
                    storage.save_brain(uid, brain.to_dict())
                _send_json(self, 200, result)

            elif parsed.path == "/v1/chat/completions":
                messages = data.get("messages") or []
                text = ""
                for msg in reversed(messages):
                    if isinstance(msg, dict) and msg.get("role") == "user":
                        text = str(msg.get("content") or "").strip()
                        break
                if not text:
                    _send_json(self, 400, {"error": "No user message found"})
                    return
                uid = storage.sanitize_user_id(data.get("user_id", "default"))
                with _get_lock(uid):
                    brain = get_brain(uid)
                    result = brain.observe_bulk(
                        text,
                        llm_url=data.get("llm_url"),
                        llm_model=data.get("llm_model"),
                        llm_key=data.get("llm_key"),
                    )
                    storage.save_brain(uid, brain.to_dict())
                response_text = result["response"]

                if data.get("stream", False):
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Cache-Control", "no-cache")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    words = response_text.split(" ")
                    for i, w in enumerate(words):
                        piece = w + (" " if i < len(words) - 1 else "")
                        chunk = {
                            "id": f"chatcmpl-nsm-{int(time.time())}",
                            "object": "chat.completion.chunk",
                            "model": "nsm-vb-1.4",
                            "choices": [{"index": 0, "delta": {"content": piece}, "finish_reason": None}],
                        }
                        self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode("utf-8"))
                        self.wfile.flush()
                        time.sleep(0.02)
                    self.wfile.write(b"data: [DONE]\n\n")
                    self.wfile.flush()
                    return

                _send_json(self, 200, {
                    "id": f"chatcmpl-nsm-{int(time.time())}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": "nsm-vb-1.4",
                    "choices": [{
                        "index": 0,
                        "message": {"role": "assistant", "content": response_text},
                        "finish_reason": "stop",
                    }],
                    "nsm_meta": {
                        "mode": result.get("mode"),
                        "confidence": result.get("confidence"),
                        "proof_steps": result.get("proof_steps", []),
                        "episode_id": result.get("episode_id"),
                    },
                })

            elif parsed.path == "/test_llm":
                res = cortex_api.test_connection(
                    llm_url=data.get("llm_url"),
                    llm_model=data.get("llm_model"),
                    llm_key=data.get("llm_key"),
                )
                _send_json(self, 200 if res.get("ok") else 400, res)

            elif parsed.path == "/feedback":
                uid = storage.sanitize_user_id(data.get("user_id", "default"))
                positive = bool(data.get("positive", True))
                episode_id = data.get("episode_id")
                with _get_lock(uid):
                    brain = get_brain(uid)
                    res = brain.apply_feedback(positive=positive, episode_id=episode_id)
                    storage.save_brain(uid, brain.to_dict())
                _send_json(self, 200, res)

            elif parsed.path == "/sleep":
                uid = storage.sanitize_user_id(data.get("user_id", "default"))
                with _get_lock(uid):
                    brain = get_brain(uid)
                    report = brain.run_sleep_consolidation(force=True)
                    storage.save_brain(uid, brain.to_dict())
                _send_json(self, 200, {"ok": True, **report})

            elif parsed.path == "/export":
                uid = storage.sanitize_user_id(data.get("user_id", "default"))
                with _get_lock(uid):
                    brain = get_brain(uid)
                    payload = brain.to_dict()
                _send_json(self, 200, payload)

            elif parsed.path == "/import":
                uid = storage.sanitize_user_id(data.get("user_id", "default"))
                import_data = data.get("brain_data")
                mode = data.get("mode", "merge")
                valid, reason = storage.validate_brain_file(import_data)
                if not valid:
                    _send_json(self, 400, {"error": f"Invalid NSM file: {reason}"})
                    return
                with _get_lock(uid):
                    # Convert incoming (v1.4 or legacy) into normalized v1.4 dict
                    incoming_brain = Brain.from_dict(import_data)
                    incoming_v14 = incoming_brain.to_dict()
                    current_state = storage.load_brain(uid)
                    if mode == "merge" and current_state:
                        current_v14 = Brain.from_dict(current_state).to_dict()
                        final_dict = storage.merge_brain_data(current_v14, incoming_v14)
                    else:
                        final_dict = incoming_v14
                    final_brain = Brain.from_dict(final_dict)
                    storage.save_brain(uid, final_brain.to_dict())
                    _invalidate_brain(uid)
                _send_json(self, 200, {
                    "ok": True,
                    "message": reason,
                    "stats": final_brain.state(),
                })

            elif parsed.path in ("/delete_brain", "/reset"):
                uid = storage.sanitize_user_id(data.get("user_id", "default"))
                with _get_lock(uid):
                    storage.delete_brain(uid)
                    _invalidate_brain(uid)
                _send_json(self, 200, {"ok": True, "message": f"Cleared brain: {uid}"})

            else:
                _send_json(self, 404, {"error": "Endpoint not found"})
        except Exception as e:
            print(f"[NSM Server Error] {traceback.format_exc()}")
            _send_json(self, 500, {"error": str(e)})


def run(host: str = "127.0.0.1", port: int = 8081) -> None:
    server = NSMThreadingServer((host, port), Handler)
    print(f"NSM VB v{Brain.VERSION} server running on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down NSM VB server...")
        server.shutdown()
    finally:
        server.server_close()


if __name__ == "__main__":
    run(host="0.0.0.0", port=8081)
