"""Thread-safe SQLite persistence and v1.4/legacy brain import-export engine."""

import json
import os
import sqlite3
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

_DB_LOCK = threading.RLock()
DB_PATH = os.path.join(os.environ.get("NSM_DATA_DIR", "data"), "nsm_core.db")


def get_data_dir() -> str:
    data_dir = os.environ.get("NSM_DATA_DIR") or "data"
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_db_path() -> str:
    global DB_PATH
    DB_PATH = os.path.join(get_data_dir(), "nsm_core.db")
    return DB_PATH


def _connect() -> sqlite3.Connection:
    path = get_db_path()
    conn = sqlite3.connect(path, timeout=15.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=10000;")
    return conn


def init_db() -> None:
    with _DB_LOCK:
        conn = _connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS brains (
                    user_id TEXT PRIMARY KEY,
                    state_json TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()


def sanitize_user_id(user_id: Optional[str]) -> str:
    cleaned = (user_id or "default").strip()
    if not cleaned:
        return "default"
    return cleaned[:64]


def save_brain(user_id: str, state_dict: Dict[str, Any]) -> None:
    uid = sanitize_user_id(user_id)
    payload = json.dumps(state_dict, ensure_ascii=False)
    with _DB_LOCK:
        init_db()
        conn = _connect()
        try:
            conn.execute(
                """
                INSERT INTO brains (user_id, state_json)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET state_json = excluded.state_json
                """,
                (uid, payload),
            )
            conn.commit()
        finally:
            conn.close()


def load_brain(user_id: str) -> Optional[Dict[str, Any]]:
    uid = sanitize_user_id(user_id)
    with _DB_LOCK:
        init_db()
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT state_json FROM brains WHERE user_id = ?",
                (uid,),
            ).fetchone()
        finally:
            conn.close()
    if not row or not row[0]:
        return None
    try:
        parsed = json.loads(row[0])
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def delete_brain(user_id: str) -> bool:
    uid = sanitize_user_id(user_id)
    with _DB_LOCK:
        init_db()
        conn = _connect()
        try:
            cur = conn.execute("DELETE FROM brains WHERE user_id = ?", (uid,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()


def list_brains() -> List[str]:
    with _DB_LOCK:
        init_db()
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT user_id FROM brains ORDER BY user_id ASC"
            ).fetchall()
        finally:
            conn.close()
    return [row[0] for row in rows if row and row[0]]


def validate_brain_file(data: Any) -> Tuple[bool, str]:
    """Validate NSM v1.4 or legacy NSM brain JSON exports."""
    if not isinstance(data, dict):
        return False, "Brain file must be a JSON object."

    # Native v1.4 schema
    if data.get("nsm_version") == "1.4":
        if "hypergraph" not in data or not isinstance(data["hypergraph"], dict):
            return False, "Missing 'hypergraph' section in v1.4 brain file."
        return True, "Valid NSM v1.4 brain file."

    # Legacy NSM v1.x compatibility (facts / relations / memory)
    legacy_keys = {"facts", "relations", "memory", "concepts", "vocab"}
    if legacy_keys.intersection(data.keys()):
        return True, "Valid legacy NSM brain file (will auto-upgrade to v1.4)."

    return False, "Unrecognized brain format (missing v1.4 or legacy NSM fields)."


def merge_brain_data(
    current_state: Optional[Dict[str, Any]],
    incoming_state: Dict[str, Any],
) -> Dict[str, Any]:
    """Safely merge two v1.4 brain dictionaries without losing existing memory."""
    if not current_state or current_state.get("nsm_version") != "1.4":
        return incoming_state
    if incoming_state.get("nsm_version") != "1.4":
        return current_state

    merged = json.loads(json.dumps(current_state))

    # Merge hypergraph senses
    cur_hg = merged.setdefault("hypergraph", {})
    inc_hg = incoming_state.get("hypergraph", {})

    cur_senses = cur_hg.setdefault("senses", {})
    for sid, sdata in inc_hg.get("senses", {}).items():
        if sid not in cur_senses:
            cur_senses[sid] = sdata
        else:
            existing_ctx = set(cur_senses[sid].get("context_tokens", []))
            existing_ctx.update(sdata.get("context_tokens", []))
            cur_senses[sid]["context_tokens"] = sorted(existing_ctx)[:40]

    # Merge hypergraph frames by signature (prefer higher evidence or newer)
    cur_frames = cur_hg.setdefault("frames", {})
    for fid, fdata in inc_hg.get("frames", {}).items():
        if fid not in cur_frames:
            cur_frames[fid] = fdata
        else:
            cur_alpha = float(cur_frames[fid].get("alpha", 1.0))
            inc_alpha = float(fdata.get("alpha", 1.0))
            cur_beta = float(cur_frames[fid].get("beta", 1.0))
            inc_beta = float(fdata.get("beta", 1.0))
            cur_frames[fid]["alpha"] = max(cur_alpha, inc_alpha)
            cur_frames[fid]["beta"] = min(cur_beta, inc_beta)

    # Merge episodes by id
    cur_ep = merged.setdefault("episodic", {})
    inc_ep = incoming_state.get("episodic", {})
    existing_ids = {ep.get("id") for ep in cur_ep.get("episodes", [])}
    for ep in inc_ep.get("episodes", []):
        if ep.get("id") not in existing_ids:
            cur_ep.setdefault("episodes", []).append(ep)
            existing_ids.add(ep.get("id"))

    # Merge consolidated schemas
    cur_schemas = cur_ep.setdefault("schemas", {})
    for sch_id, sch in inc_ep.get("schemas", {}).items():
        if sch_id not in cur_schemas:
            cur_schemas[sch_id] = sch

    # Merge user profile attributes
    cur_profile = merged.setdefault("profile", {})
    for k, v in incoming_state.get("profile", {}).items():
        if v:
            cur_profile[k] = v

    merged["updated_at"] = time.time()
    return merged


init_db()
