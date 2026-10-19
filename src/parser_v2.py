import re
from src.constructions import CONSTRUCTIONS

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
            
    # 2. IS_PROP: [SUBJ] is [ADJ]
    if "is" in words and len(words) == 3 and "a" not in words:
        return ("IS_PROP", words[0], words[2])
        
    # 3. SVO: [SUBJ] [VERB] [OBJ]
    if len(words) == 3:
        return ("SVO", words[0], words[1], words[2])

    return None
