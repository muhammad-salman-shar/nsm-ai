import re
from src.constructions import CONSTRUCTIONS
from src.patterns import get_base_verb
from src.morphology import normalize_pronoun

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
    
    # 1. IS_A: [SUBJ] is a/an [OBJ] OR [SUBJ] are [OBJ]
    det = None
    if "a" in words: det = "a"
    elif "an" in words: det = "an"
    
    if "is" in words and det:
        idx_is = words.index("is")
        idx_det = words.index(det)
        if idx_is == 1 and idx_det == 2 and len(words) == 4:
            return ("IS_A", normalize_pronoun(words[0]), words[3])
            
    # Plural handling: dogs are animals
    if "are" in words and len(words) == 3:
        return ("IS_A", normalize_pronoun(words[0]), words[2], "plural")
            
    # Negation: [SUBJ] is not a [OBJ]
    if "is" in words and "not" in words and ("a" in words or "an" in words):
        det = "a" if "a" in words else "an"
        if len(words) >= 5:
            return ("NOT_IS_A", words[0], words[-1])
            
    # Question: Is [SUBJ] a [OBJ]?
    if words[0] == "is" and ("a" in words or "an" in words) and len(words) >= 4:
        return ("Q_IS_A", normalize_pronoun(words[1]), words[-1])

    # 2. IS_PROP: [SUBJ] is [ADJ]
    if "is" in words and len(words) == 3 and "a" not in words:
        return ("IS_PROP", normalize_pronoun(words[0]), words[2])
        
    # 3. SVO: [SUBJ] [VERB] [OBJ]
    if len(words) == 3:
        tense = detect_tense(words[1])
        return ("SVO", normalize_pronoun(words[0]), words[1], words[2], tense)
        
    # Future tense: [SUBJ] will [VERB] [OBJ] (4 words)
    if len(words) == 4 and words[1] in ("will", "shall"):
        return ("SVO", words[0], words[2], words[3], "future")

    # 1. Negation: [SUBJ] do/does/did not [VERB] [OBJ]
    if "not" in words and any(w in ("do", "does", "did") for w in words):
        try:
            aux_idx = next(i for i, w in enumerate(words) if w in ("do", "does", "did"))
            subj = words[aux_idx - 1] if aux_idx > 0 else "i"
            verb = words[aux_idx + 2] if len(words) > aux_idx + 2 else "do"
            obj = words[aux_idx + 3] if len(words) > aux_idx + 3 else None
            return ("NOT_SVO", normalize_pronoun(subj), verb, obj)
        except IndexError:
            pass

    # 2. WH-Question: What does [SUBJ] [VERB]?
    if words[0] == "what" and len(words) >= 4 and words[1] in ("do", "does", "did"):
        subj = words[2]
        verb = words[3]
        return ("SVO_QUERY", normalize_pronoun(subj), verb)

    # 3. Yes/No Question: Does [SUBJ] [VERB] [OBJ]?
    if words[0] in ("do", "does", "did") and len(words) >= 3:
        subj = words[1]
        verb = words[2]
        obj = words[3] if len(words) > 3 else None
        return ("SVO_YESNO", normalize_pronoun(subj), verb, obj)

    return None
