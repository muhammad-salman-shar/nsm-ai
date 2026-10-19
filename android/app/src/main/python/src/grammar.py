import re

QUESTION_WORDS = {"what", "who", "where", "when", "why", "how", "which", "whose"}
BE_VERBS = {"am", "is", "are", "was", "were"}
DO_VERBS = {"do", "does", "did"}
MODALS = {"can", "could", "will", "would", "shall", "should", "may", "might", "must"}
COMMON_VERBS = {"like", "love", "hate", "eat", "drink", "run", "walk", "play", "see", "look", "go", "come", "make", "do", "have", "want", "need", "know", "think", "feel", "tell", "say", "find", "give", "take"}
ALL_VERBS = BE_VERBS | DO_VERBS | MODALS | COMMON_VERBS | {"have", "has", "had"}

def tokenize(text):
    return re.findall(r"[a-zA-Z']+", text.lower())

def parse(text):
    words = tokenize(text)
    if not words:
        return {"type": "empty", "words": []}
    
    is_question = text.strip().endswith("?")
    qword = words[0] if words[0] in QUESTION_WORDS else None
    if qword:
        is_question = True
        
    structure = {
        "type": "question" if is_question else "statement",
        "words": words,
        "qword": qword,
        "subject": [],
        "verb": [],
        "object": [],
        "aux": None
    }

    if qword:
        rest = words[1:]
        verb_idx = -1
        for i, w in enumerate(rest):
            if w in ALL_VERBS:
                verb_idx = i
                break
        if verb_idx != -1:
            structure["verb"] = [rest[verb_idx]]
            structure["subject"] = rest[:verb_idx]
            structure["object"] = rest[verb_idx+1:]
        else:
            structure["object"] = rest
        return structure

    # find first verb
    verb_idx = -1
    for i, w in enumerate(words):
        if w in ALL_VERBS:
            verb_idx = i
            break
            
    if verb_idx != -1:
        structure["verb"] = [words[verb_idx]]
        
        # Yes/No question handling (e.g., "Is Salman a human?")
        if verb_idx == 0 and is_question:
            structure["aux"] = words[0]
            structure["subject"] = [words[1]] if len(words) > 1 else []
            # find main verb after subject
            main_verb_idx = -1
            for i, w in enumerate(words[2:], start=2):
                if w in ALL_VERBS:
                    main_verb_idx = i
                    break
            if main_verb_idx != -1:
                structure["verb"] = [words[main_verb_idx]]
                structure["object"] = words[main_verb_idx+1:]
            else:
                structure["verb"] = [words[0]]
                structure["object"] = words[2:]
        else:
            structure["subject"] = words[:verb_idx]
            structure["object"] = words[verb_idx+1:]
    else:
        structure["subject"] = words
        
    return structure
