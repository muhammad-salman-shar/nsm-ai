import re
from src.constructions import CONSTRUCTIONS
from src.patterns import get_base_verb

def detect_tense(verb):
    v = verb.lower()
    from src.patterns import IRREGULAR_PAST
    if v in IRREGULAR_PAST:
        return "past"
    if v in ("will", "shall"):
        return "future"
    if v.endswith("ed"):
        return "past"
    return "present"


def parse_to_meaning(text):
    words = re.findall(r"[a-zA-Z']+", text.lower())
    if not words: return None
    
    # 1. IS_A: [SUBJ] is a/an [OBJ]
    det = None
    if "a" in words: det = "a"
    elif "an" in words: det = "an"
    
    if "is" in words and det:
        idx_is = words.index("is")
        idx_det = words.index(det)
        if idx_is == 1 and idx_det == 2 and len(words) == 4:
            return ("IS_A", words[0], words[3])
            
    # Negation: [SUBJ] is not a [OBJ]
    if "is" in words and "not" in words and ("a" in words or "an" in words):
        det = "a" if "a" in words else "an"
        if len(words) >= 5:
            return ("NOT_IS_A", words[0], words[-1])
            
    # Question: Is [SUBJ] a [OBJ]?
    if words[0] == "is" and ("a" in words or "an" in words) and len(words) >= 4:
        return ("Q_IS_A", words[1], words[-1])

    # 2. IS_PROP: [SUBJ] is [ADJ]
    if "is" in words and len(words) == 3 and "a" not in words:
        return ("IS_PROP", words[0], words[2])
        
    # 3. SVO: [SUBJ] [VERB] [OBJ]
    if len(words) == 3:
        tense = detect_tense(words[1])
        return ("SVO", words[0], words[1], words[2], tense)
        
    # Future tense: [SUBJ] will [VERB] [OBJ] (4 words)
    if len(words) == 4 and words[1] in ("will", "shall"):
        return ("SVO", words[0], words[2], words[3], "future")

    return None
