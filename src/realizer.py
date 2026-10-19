from src.patterns import conjugate, to_base_verb
from src.morphology import get_article, conjugate_verb

def realize(meaning):
    if not meaning: return ""
    
    m_type = meaning[0]
    
    if m_type == "IS_A":
        subj, obj = meaning[1], meaning[2]
        is_plural = (len(meaning) > 3 and meaning[3] == "plural") or subj.endswith("s")
        be_verb = "are" if is_plural else conjugate_verb("be", "present", subj)
        
        if is_plural:
            return f"{subj.capitalize()} {be_verb} {obj}."
        else:
            article = get_article(obj)
            return f"{subj.capitalize()} {be_verb} {article} {obj}."
        
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
        be_verb = conjugate_verb("be", "present", subj)
        return f"{subj.capitalize()} {be_verb} {adj}."
        
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
            
    elif m_type == "NOT_SVO":
        subj, verb, obj = meaning[1], meaning[2], meaning[3]
        aux = conjugate_verb("do", "present", subj)
        base_v = to_base_verb(verb) or verb
        obj_str = f" {obj}" if obj else ""
        return f"{subj.capitalize()} {aux} not {base_v}{obj_str}."
        
    elif m_type == "SVO_QUERY":
        subj, verb = meaning[1], meaning[2]
        aux = conjugate_verb("do", "present", subj)
        base_v = to_base_verb(verb) or verb
        return f"What {aux} {subj} {base_v}?"
        
    elif m_type == "SVO_YESNO":
        subj, verb = meaning[1], meaning[2]
        obj = meaning[3] if len(meaning) > 3 and meaning[3] else None
        aux = conjugate_verb("do", "present", subj)
        base_v = to_base_verb(verb) or verb
        obj_str = f" {obj}" if obj else ""
        return f"{aux.capitalize()} {subj} {base_v}{obj_str}?"
        
    return ""
