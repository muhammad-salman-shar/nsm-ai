from src.patterns import conjugate, to_base_verb

VOWELS = "aeiou"

def get_article(word):
    return "an" if word[0].lower() in VOWELS else "a"

def realize(meaning):
    if not meaning: return ""
    
    m_type = meaning[0]
    
    if m_type == "IS_A":
        subj, obj = meaning[1], meaning[2]
        article = get_article(obj)
        return f"{subj.capitalize()} is {article} {obj}."
        
    elif m_type == "IS_PROP":
        subj, adj = meaning[1], meaning[2]
        return f"{subj.capitalize()} is {adj}."
        
    elif m_type == "SVO":
        subj, verb, obj = meaning[1], meaning[2], meaning[3]
        base_v = to_base_verb(verb) or verb
        v = conjugate(base_v, subj)
        return f"{subj.capitalize()} {v} {obj}."
        
    return ""
