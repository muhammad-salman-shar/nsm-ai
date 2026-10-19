def infer_relation(relations_store, subject, rel_type, target):
    """
    Infers if subject has relation rel_type with target.
    Handles:
    - Direct: subject -> rel_type -> target
    - Transitive via IS: subject -> IS -> category -> rel_type -> target
    """
    # 1. Direct check
    direct = relations_store.get(rel_type, subject)
    if target in direct:
        verb = {"IS": "is", "CAN": "can", "HAS": "has"}.get(rel_type, rel_type.lower())
        return True, f"{subject} {verb} {target}."

    # 2. One-level transitive check via IS
    categories = relations_store.get("IS", subject)
    for category in categories:
        cat_rels = relations_store.get(rel_type, category)
        if target in cat_rels:
            verb = {"IS": "is", "CAN": "can", "HAS": "has"}.get(rel_type, rel_type.lower())
            return True, f"Yes, because {subject} is {category} and {category} {verb} {target}."

    return False, None
