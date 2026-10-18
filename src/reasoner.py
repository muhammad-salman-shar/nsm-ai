def transitive_inference(relations_store, subject, target_property):
    """
    Checks if subject -> target_property can be inferred through a chain.
    Example: 
    Subject: salman
    Relations: salman IS human, human IS mortal
    Query: is salman mortal?
    """
    # 1. Direct check
    direct = relations_store.get("IS", subject)
    if target_property in direct:
        return True, f"{subject} is {target_property}."

    # 2. One-level transitive check (A -> B -> C)
    for intermediate in direct:
        # Skip generic objects if they don't have further relations
        indirect = relations_store.get("IS", intermediate)
        if target_property in indirect:
            return True, f"Yes, because {subject} is {intermediate} and {intermediate} is {target_property}."
            
    return False, None
