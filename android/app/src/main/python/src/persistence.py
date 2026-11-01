import json
import os
import time


STATE_VERSION = 1
DEFAULT_PATH = "data/brain_state.json"


def _serialize_relations(relations):
    out = {}
    for (rel_type, subject), bucket in relations.relations.items():
        key = f"{rel_type}|{subject}"
        out[key] = {
            obj: {
                "count": rec.get("count", 1),
                "first_seen": rec["first_seen"],
                "last_seen": rec["last_seen"],
                "superseded": rec["superseded"],
                "source": rec.get("source", "user"),
            }
            for obj, rec in bucket.items()
        }
    return out


def _deserialize_relations(data, relations):
    import time
    for key, bucket in data.items():
        if "|" not in key: continue
        rel_type, subject = key.split("|", 1)
        store_key = (rel_type, subject)
        relations.relations[store_key] = {}
        for obj, rec in bucket.items():
            if not isinstance(rec, dict): rec = {}
            relations.relations[store_key][obj] = {
                "count": rec.get("count", 1),
                "first_seen": rec.get("first_seen", time.time()),
                "last_seen": rec.get("last_seen", time.time()),
                "superseded": rec.get("superseded", False),
                "source": rec.get("source", "user"),
            }


def _serialize_lexicon(lexicon):
    out = {}
    for word, data in lexicon.words.items():
        out[word] = {
            "count": data.get("count", 1),
            "contexts": sorted(data.get("contexts", set())),
        }
    return out


def _deserialize_lexicon(data, lexicon):
    for word, d in data.items():
        if not isinstance(d, dict): d = {}
        existing = lexicon.words.get(word)
        vec = existing["vec"] if existing and existing.get("vec") is not None else _safe_vec(word)
        lexicon.words[word] = {
            "vec": vec,
            "count": d.get("count", 1),
            "contexts": set(d.get("contexts", [])),
            "relations": {},
        }
    lexicon.count = sum(d.get("count", 1) for d in lexicon.words.values())


def _safe_vec(word):
    from src.memory import _vec
    return _vec(word)


def to_dict(brain):
    return {
        "version": STATE_VERSION,
        "saved_at": time.time(),
        "turn": brain.turn,
        "max_depth": brain.max_depth,
        "definitions": dict(brain.definitions),
        "facts": dict(brain.fact_store.facts),
        "relations": _serialize_relations(brain.relations),
        "lexicon": _serialize_lexicon(brain.lexicon),
        "episodes": [
            {k: v for k, v in ep.items() if k != "vec"}
            for ep in brain.episodic.episodes
        ],
        "affect": {
            "drives": dict(brain.affect.drives),
            "hormones": dict(brain.affect.hormones),
        },
    }


def from_dict(brain, data):
    if data.get("version") != STATE_VERSION:
        return False
    brain.turn = data.get("turn", 0)
    brain.definitions = dict(data.get("definitions", {}))
    for k, v in data.get("facts", {}).items():
        brain.fact_store.facts[k] = v
    _deserialize_relations(data.get("relations", {}), brain.relations)
    _deserialize_lexicon(data.get("lexicon", {}), brain.lexicon)

    brain.episodic.episodes = []
    for ep in data.get("episodes", []):
        ep = dict(ep)
        words = ep.get("words") or []
        from src.memory import bundle, _vec, DIM
        import numpy as np
        ep["vec"] = bundle([_vec(w) for w in words]) if words else np.zeros(DIM, dtype=np.uint8)
        brain.episodic.episodes.append(ep)

    aff = data.get("affect", {})
    for k, v in aff.get("drives", {}).items():
        if k in brain.affect.drives:
            brain.affect.drives[k] = float(v)
    for k, v in aff.get("hormones", {}).items():
        if k in brain.affect.hormones:
            brain.affect.hormones[k] = float(v)
    return True


def save(brain, path=DEFAULT_PATH):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(to_dict(brain), f, indent=2)
    os.replace(tmp, path)
    return path


def load(brain, path=DEFAULT_PATH):
    if not os.path.exists(path):
        return False
    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return False
    return from_dict(brain, data)


def reset(path=DEFAULT_PATH):
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def validate_brain_file(data):
    """Strictly validates if data is a valid NSM brain file."""
    if not isinstance(data, dict):
        return False, "File must be a JSON object"
    
    required = ["version", "definitions", "relations", "lexicon", "episodes"]
    for key in required:
        if key not in data:
            return False, f"Missing required key: '{key}'"
    
    if data.get("version") != STATE_VERSION:
        return False, f"Version mismatch. Expected {STATE_VERSION}, got {data.get('version')}"
    
    if not isinstance(data["definitions"], dict):
        return False, "'definitions' must be a dict"
    if not isinstance(data["relations"], dict):
        return False, "'relations' must be a dict"
    if not isinstance(data["lexicon"], dict):
        return False, "'lexicon' must be a dict"
    if not isinstance(data["episodes"], list):
        return False, "'episodes' must be a list"
    
    return True, "Valid NSM brain file"


def merge_brain_data(existing, new_data):
    """Merges new brain data into existing. No data is lost (except conflicts)."""
    if existing is None:
        return new_data
    
    merged = dict(existing)
    
    # Facts: new wins on conflict (latest is usually correct)
    merged["facts"] = dict(existing.get("facts", {}))
    merged["facts"].update(new_data.get("facts", {}))
    
    # Definitions: new wins on conflict
    merged["definitions"] = dict(existing.get("definitions", {}))
    merged["definitions"].update(new_data.get("definitions", {}))
    
    # Relations: union (both preserved)
    merged["relations"] = {}
    for key in set(list(existing.get("relations", {}).keys()) + list(new_data.get("relations", {}).keys())):
        old_vals = existing.get("relations", {}).get(key, {})
        new_vals = new_data.get("relations", {}).get(key, {})
        combined = dict(old_vals) if isinstance(old_vals, dict) else {}
        if isinstance(new_vals, dict):
            combined.update(new_vals)
        merged["relations"][key] = combined
    
    # Lexicon: union
    merged["lexicon"] = dict(existing.get("lexicon", {}))
    merged["lexicon"].update(new_data.get("lexicon", {}))
    
    # Episodes: append (chronological history)
    merged["episodes"] = list(existing.get("episodes", [])) + list(new_data.get("episodes", []))
    
    # Turn count: max
    merged["turn"] = max(existing.get("turn", 0), new_data.get("turn", 0))
    
    # Affect: keep existing (personal state)
    if "affect" in existing:
        merged["affect"] = existing["affect"]
    
    return merged
