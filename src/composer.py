def compose_object(subject, rel_type, relations_store):
    """
    Takes a subject (e.g. salman) and relation (like) 
    and returns an enriched object (e.g. sweet mangoes).
    """
    objects = relations_store.get(rel_type.upper(), subject)
    if not objects:
        return None
        
    base_obj = objects[0]
    
    # Check for properties of the object (e.g. mangoes are sweet)
    properties = relations_store.get("IS", base_obj)
    
    # Simple rule: if it has an adjective property, prefix it.
    if properties:
        adj = properties[0]
        # Basic check to avoid "fruit mangoes" or "animal dog"
        if adj not in ("fruit", "animal", "human", "person", "thing", "object"):
            return f"{adj} {base_obj}"
            
    return base_obj
