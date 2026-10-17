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
                "count": rec["count"],
                "first_seen": rec["first_seen"],
                "last_seen": rec["last_seen"],
                "superseded": rec["superseded"],
                "source": rec.get("source", "user"),
            }
            for obj, rec in bucket.items()
        }
    return out


def _deserialize_relations(data, relations):
    for key, bucket in data.items():
        rel_type, subject = key.split("|", 1)
        store_key = (rel_type, subject)
        relations.relations[store_key] = {}
        for obj, rec in bucket.items():
            relations.relations[store_key][obj] = {
                "count": rec["count"],
                "first_seen": rec["first_seen"],
                "last_seen": rec["last_seen"],
                "superseded": rec["superseded"],
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
        existing = lexicon.words.get(word)
        vec = existing["vec"] if existing and existing.get("vec") is not None else _safe_vec(word)
        lexicon.words[word] = {
            "vec": vec,
            "count": d.get("count", 1),
            "contexts": set(d.get("contexts", [])),
            "relations": {},
        }
    lexicon.count = sum(d["count"] for d in lexicon.words.values())


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
