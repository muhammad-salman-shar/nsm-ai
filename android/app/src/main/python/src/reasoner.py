def infer_relation_full(relations_store, subject, rel_type, target):
    """
    Infers if subject has relation rel_type with target.
    Returns (is_true, message, confidence, mode).
    Modes: 'stored', 'derived', 'unknown'.
    """
    # 1. Direct check
    direct_rec = relations_store.get_rec(rel_type, subject, target)
    if direct_rec and not direct_rec.get("superseded"):
        verb = {"IS": "is", "CAN": "can", "HAS": "has"}.get(rel_type, rel_type.lower())
        conf = direct_rec.get("confidence", 0.9)
        return True, f"{subject} {verb} {target}.", conf, "stored"

    # 2. One-level transitive check via IS
    categories = relations_store.get("IS", subject)
    for category in categories:
        subj_rec = relations_store.get_rec("IS", subject, category)
        subj_conf = subj_rec.get("confidence", 0.9) if subj_rec else 0.9
        
        target_rec = relations_store.get_rec(rel_type, category, target)
        if target_rec and not target_rec.get("superseded"):
            verb = {"IS": "is", "CAN": "can", "HAS": "has"}.get(rel_type, rel_type.lower())
            conf = min(subj_conf, target_rec.get("confidence", 0.9))
            return True, f"{subject} is {category} and {category} {verb} {target}.", conf, "derived"

    return False, None, 0.0, "unknown"


def infer_relation(relations_store, subject, rel_type, target):
    """Backward-compatible 2-tuple wrapper (preserves old 'Yes, because' format)."""
    is_true, msg, _conf, mode = infer_relation_full(relations_store, subject, rel_type, target)
    if not is_true:
        return False, None
    if mode == "derived":
        return True, f"Yes, because {msg}"
    return True, msg
