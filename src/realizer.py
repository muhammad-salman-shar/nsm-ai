from src.patterns import conjugate, to_base_verb
from src.morphology import get_article, conjugate_verb

def realize(meaning):
    if not meaning: return ""
    
    m_type = meaning[0]
    
    if m_type == "IS_A":
        subj, obj = meaning[1], meaning[2]
        article = get_article(obj)
        return f"{subj.capitalize()} is {article} {obj}."
        
    elif m_type == "NOT_IS_A":
        subj, obj = meaning[1], meaning[2]
        article = get_article(obj)
        return f"{subj.capitalize()} is not {article} {obj}."
        
    elif m_type == "Q_IS_A":
        subj, obj = meaning[1], meaning[2]
        article = get_article(obj)
        return f"Is {subj.lower()} {article} {obj}?"

    elif m_type == "IS_PROP":
        subj, adj = meaning[1], meaning[2]
        return f"{subj.capitalize()} is {adj}."
        
    elif m_type == "SVO":
        subj, verb, obj = meaning[1], meaning[2], meaning[3]
        tense = meaning[4] if len(meaning) > 4 else "present"
        base_v = to_base_verb(verb) or verb
        if tense == "past":
            v = conjugate_verb(base_v, tense="past", subject=subj)
            return f"{subj.capitalize()} {v} {obj}."
        elif tense == "future":
            v = conjugate_verb(base_v, tense="future", subject=subj)
            return f"{subj.capitalize()} {v} {obj}."
        else:
            v = conjugate_verb(base_v, tense="present", subject=subj)
            return f"{subj.capitalize()} {v} {obj}."
        
    return ""
