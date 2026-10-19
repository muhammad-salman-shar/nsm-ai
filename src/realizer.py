from src.patterns import conjugate, to_base_verb

def conjugate_past(verb):
    v = verb.lower()
    irregulars = {"eat":"ate","go":"went","see":"saw","run":"ran","make":"made",
                  "take":"took","give":"gave","know":"knew","think":"thought",
                  "feel":"felt","find":"found","drink":"drank","write":"wrote",
                  "swim":"swam","fly":"flew","drive":"drove","ride":"rode",
                  "buy":"bought","bring":"brought","build":"built","break":"broke",
                  "say":"said","tell":"told","read":"read"}
    if v in irregulars: return irregulars[v]
    if v.endswith("e"): return v + "d"
    if v.endswith("y") and v[-2] not in "aeiou": return v[:-1] + "ied"
    return v + "ed"

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
            v = conjugate_past(base_v)
            return f"{subj.capitalize()} {v} {obj}."
        elif tense == "future":
            return f"{subj.capitalize()} will {base_v} {obj}."
        else:
            v = conjugate(base_v, subj)
            return f"{subj.capitalize()} {v} {obj}."
        
    return ""
