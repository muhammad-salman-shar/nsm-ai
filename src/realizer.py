"""Natural Conversational Realizer for NSM VB v1.5 (English + Hinglish).

Converts verified symbolic hypergraph frames and reasoning traces into clean,
human-like responses tailored to all 16 question types — with zero robotic boilerplate.
"""

from typing import Any, Dict, List, Optional

ACRONYM_MAP: Dict[str, str] = {
    "cpu": "CPU",
    "ram": "RAM",
    "rom": "ROM",
    "gpu": "GPU",
    "ssd": "SSD",
    "hdd": "HDD",
    "api": "API",
    "mcp": "MCP",
    "sql": "SQL",
    "sqlite": "SQLite",
    "ai": "AI",
    "os": "OS",
    "nsm": "NSM",
    "nsm vb": "NSM VB",
    "neurasamu": "NeuraSaMu",
    "big o notation": "Big O notation",
}


def display_entity(name: str) -> str:
    low = (name or "").strip().lower()
    if not low:
        return ""
    if low in ACRONYM_MAP:
        return ACRONYM_MAP[low]
    words = low.split()
    return " ".join(ACRONYM_MAP.get(w, w.capitalize()) for w in words)


def frame_to_sentence(fr: Dict[str, Any], lang: str = "english") -> str:
    """Render any of the 14+ typed hypergraph relations into a clean sentence."""
    ag = display_entity(fr.get("agent", ""))
    pat = (fr.get("patient") or "").strip()
    rel = (fr.get("relation") or "").upper()
    pol = int(fr.get("polarity", 1))
    mod = (fr.get("modifier") or "").strip()

    if rel == "IS_A":
        if lang == "hinglish":
            return f"{ag} ek {pat} {'nahi ' if pol < 0 else ''}hai."
        return f"{ag} is {'not ' if pol < 0 else ''}a {pat}."

    if rel == "DEFINED_AS":
        if lang == "hinglish":
            return f"{ag} {pat} {'nahi ' if pol < 0 else ''}hota hai."
        return f"{ag} is {'not ' if pol < 0 else ''}{pat}."

    if rel == "ALSO_KNOWN_AS":
        if lang == "hinglish":
            return f"{ag} ko {display_entity(pat)} bhi kehte hain."
        return f"{ag} is also known as {display_entity(pat)}."

    if rel == "CAN":
        if lang == "hinglish":
            return f"{ag} {pat} {'kar sakta hai' if pol > 0 else 'nahi kar sakta'}."
        return f"{ag} {'can' if pol > 0 else 'cannot'} {pat}."

    if rel == "USED_FOR":
        if lang == "hinglish":
            return f"{ag} {pat} ke liye use hota hai."
        return f"{ag} is used for {pat}."

    if rel == "CAUSES":
        if lang == "hinglish":
            return f"{ag} ki wajah se {pat} hota hai."
        return f"{ag} causes {pat}."

    if rel == "WORKS_BY":
        if lang == "hinglish":
            return f"{ag} {pat} karke kaam karta hai."
        return f"{ag} works by {pat}."

    if rel == "IF_THEN":
        raw_ag = (fr.get("agent") or "").strip()
        if lang == "hinglish":
            return f"Agar {raw_ag}, toh {pat}."
        return f"If {raw_ag}, then {pat}."

    if rel == "HAS_PART":
        if lang == "hinglish":
            return f"{ag} {pat} se bana hota hai."
        return f"{ag} consists of {pat}."

    if rel == "HAS_BRANCHES":
        if lang == "hinglish":
            return f"{ag} ke main branches/types {pat} hain."
        return f"Major branches of {ag} include {pat}."

    if rel == "HAS_COUNT":
        if lang == "hinglish":
            return f"{ag} mein {pat} hote hain."
        return f"{ag} has {pat}."

    if rel == "HAS":
        if lang == "hinglish":
            return f"{ag} mein {pat} hota hai."
        return f"{ag} has {pat}."

    if rel == "HAS_AGE":
        if lang == "hinglish":
            return f"{ag} ki umar {pat} saal hai."
        return f"{ag} is {pat} years old."

    if rel == "LOCATED_IN":
        if lang == "hinglish":
            return f"{ag} {pat} mein located hai."
        return f"{ag} is located in {pat}."

    if rel == "CREATED":
        act = fr.get("action") or "created"
        if lang == "hinglish":
            return f"{ag} ne {display_entity(pat)} banaya tha."
        return f"{ag} {act} {display_entity(pat)}."

    if rel == "COMPARED_TO":
        comp_word = mod or "different from"
        pat_disp = display_entity(pat)
        if lang == "hinglish":
            return f"{ag}, {pat_disp} se {comp_word} hota hai."
        return f"{ag} is {comp_word} than {pat_disp}."

    if rel == "ACTION":
        act = mod or fr.get("action") or "acted on"
        return f"{ag} {act} {pat}."

    return f"{ag} {rel.lower().replace('_', ' ')} {pat}."


def realize_frames(frames: List[Dict[str, Any]], lang: str = "english", max_items: int = 4) -> str:
    seen = set()
    parts: List[str] = []
    for fr in frames[:max_items]:
        sent = frame_to_sentence(fr, lang=lang)
        if sent not in seen:
            seen.add(sent)
            parts.append(sent)
    return " ".join(parts)


def realize_verify(
    res: Dict[str, Any],
    subject: str,
    target: str,
    lang: str = "english",
) -> str:
    disp_s = display_entity(subject)
    mode = res.get("mode", "unknown")
    pol = int(res.get("polarity", 0))
    pct = round(float(res.get("confidence", 0.0)) * 100)
    frames = res.get("frames", [])

    if mode == "contradicted":
        if lang == "hinglish":
            return f"Meri memory mein {disp_s} aur '{target}' ko lekar do alag baatein hain. Sahi baat batao taaki main update kar doon."
        return f"My memory has conflicting evidence on whether {disp_s} matches '{target}'. Tell me which one is right so I can resolve it."

    if mode in {"stored", "derived"}:
        evidence = frame_to_sentence(frames[0], lang=lang) if frames else ""
        if pol > 0:
            if lang == "hinglish":
                return f"Haan, {evidence} (confidence {pct}%)."
            return f"Yes — {evidence} (confidence {pct}%)."
        if lang == "hinglish":
            return f"Nahi, {evidence} (confidence {pct}%)."
        return f"No — {evidence} (confidence {pct}%)."

    # Honest unknown with helpful context if subject is partially known
    if frames:
        known_txt = realize_frames(frames, lang=lang, max_items=2)
        if lang == "hinglish":
            return f"Mere paas pakka proof nahi hai ki {disp_s} '{target}' hai ya nahi. Itna zaroor pata hai: {known_txt}"
        return f"I do not have direct confirmation that {disp_s} is '{target}'. What I do know: {known_txt}"

    if lang == "hinglish":
        return f"Abhi mujhe {disp_s} ke baare mein itna nahi pata. Agar tum sikha do toh yaad rakh lunga."
    return f"I do not have stored evidence about whether {disp_s} is '{target}'. Teach me and I will remember it."


def realize_choice(
    subject: str,
    option_a: str,
    option_b: str,
    res_a: Dict[str, Any],
    res_b: Dict[str, Any],
    lang: str = "english",
) -> str:
    disp_s = display_entity(subject) if subject else "It"
    a_pos = res_a.get("mode") in {"stored", "derived"} and res_a.get("polarity", 0) > 0
    b_pos = res_b.get("mode") in {"stored", "derived"} and res_b.get("polarity", 0) > 0
    a_neg = res_a.get("mode") in {"stored", "derived"} and res_a.get("polarity", 0) < 0
    b_neg = res_b.get("mode") in {"stored", "derived"} and res_b.get("polarity", 0) < 0

    if a_pos and not b_pos:
        if lang == "hinglish":
            return f"Meri memory ke hisaab se {disp_s} ek {option_a} hai" + (f", {option_b} nahi." if b_neg else ".")
        return f"Based on my memory, {disp_s} is a {option_a}" + (f", not a {option_b}." if b_neg else ".")

    if b_pos and not a_pos:
        if lang == "hinglish":
            return f"Meri memory ke hisaab se {disp_s} ek {option_b} hai" + (f", {option_a} nahi." if a_neg else ".")
        return f"Based on my memory, {disp_s} is a {option_b}" + (f", not a {option_a}." if a_neg else ".")

    if a_pos and b_pos:
        if lang == "hinglish":
            return f"Dono sahi lag rahe hain: {disp_s} {option_a} bhi hai aur {option_b} bhi."
        return f"According to my memory, {disp_s} matches both {option_a} and {option_b}."

    if lang == "hinglish":
        return f"Mujhe abhi pakka nahi pata ki {disp_s} {option_a} hai ya {option_b}. Ek baar bata do, main save kar lunga."
    return f"I do not have enough stored facts yet to decide whether {disp_s} is {option_a} or {option_b}."


def realize_comparison(comp: Dict[str, Any], lang: str = "english") -> str:
    a = display_entity(comp.get("entity_a", ""))
    b = display_entity(comp.get("entity_b", ""))
    direct = comp.get("direct_comparisons", [])
    fa = comp.get("frames_a", [])
    fb = comp.get("frames_b", [])
    shared = comp.get("shared_categories", [])

    if comp.get("mode") == "unknown":
        if lang == "hinglish":
            return f"Abhi mere paas {a} aur {b} dono ke baare mein facts nahi hain compare karne ke liye. Inke baare mein thoda sikha do!"
        return f"I do not have stored facts on {a} and {b} yet to compare them. Teach me a fact about each and ask again."

    lines: List[str] = []
    if direct:
        lines.append(realize_frames(direct, lang=lang, max_items=2))
    if shared:
        cats = ", ".join(shared)
        if lang == "hinglish":
            lines.append(f"Dono {cats} ki category mein aate hain.")
        else:
            lines.append(f"Both belong to: {cats}.")
    if fa:
        lines.append(realize_frames(fa, lang=lang, max_items=2))
    elif lang == "hinglish":
        lines.append(f"({a} ke baare mein abhi koi detail stored nahi hai.)")
    else:
        lines.append(f"(I have no stored details on {a} yet.)")

    if fb:
        lines.append(realize_frames(fb, lang=lang, max_items=2))
    elif lang == "hinglish":
        lines.append(f"({b} ke baare mein abhi koi detail stored nahi hai.)")
    else:
        lines.append(f"(I have no stored details on {b} yet.)")

    return " ".join(lines)


def realize_examples(category: str, res: Dict[str, Any], lang: str = "english") -> str:
    disp_c = display_entity(category)
    examples = res.get("examples", [])
    frames = res.get("frames", [])

    if examples:
        nice_list = ", ".join(display_entity(e) for e in examples)
        if lang == "hinglish":
            return f"{disp_c} ke examples meri memory mein yeh hain: {nice_list}."
        return f"Examples of {disp_c} in my memory include: {nice_list}."

    if frames:
        return realize_frames(frames, lang=lang, max_items=3)

    if lang == "hinglish":
        return f"Abhi meri memory mein {disp_c} ka koi example stored nahi hai. Jaise 'X ek {category} hai' bol ke sikha sakte ho."
    return f"I do not have any examples of {disp_c} stored yet. You can teach me with 'X is a {category}'."


def realize_unknown(
    qtype: str = "",
    subject: str = "",
    lang: str = "english",
) -> str:
    """Context-aware, human-like fallback when memory does not hold the answer."""
    disp = display_entity(subject) if subject else ""

    if lang == "hinglish":
        if qtype == "QUERY_PURPOSE" and disp:
            return f"Mujhe abhi nahi pata ki {disp} kis kaam aata hai. Batao '{disp} ... ke liye use hota hai' aur main yaad rakh lunga."
        if qtype == "QUERY_HOW" and disp:
            return f"Mujhe abhi {disp} ke kaam karne ka tareeka nahi pata. Sikhao '{disp} ... karke kaam karta hai'."
        if qtype == "QUERY_CAUSE" and disp:
            return f"Mujhe abhi {disp} ki wajah nahi pata. Sikha sakte ho ki '... ki wajah se {subject} hota hai'."
        if qtype == "QUERY_IF_THEN" and subject:
            return f"Mujhe abhi nahi pata ki agar '{subject}' ho toh kya hoga. Sikhao: 'Agar {subject}, toh ...'."
        if qtype == "QUERY_PARTS" and disp:
            return f"Abhi {disp} ke hisse ya components mere paas stored nahi hain. Bata do, main memory mein lock kar dunga."
        if disp:
            return f"Mere paas abhi {disp} ke baare mein koi memory nahi hai. Ek chhoti si line mein sikha do, agli baar turant yaad rakhunga."
        return "Yeh baat abhi meri memory mein nahi hai. Simple English ya Hinglish mein sikha do, main samajh ke store kar lunga."

    # Natural English fallbacks
    if qtype == "QUERY_PURPOSE" and disp:
        return f"I have not learned what {disp} is used for yet. Tell me '{disp} is used for ...' and I will remember."
    if qtype == "QUERY_HOW" and disp:
        return f"I do not know how {disp} works yet. You can teach me: '{disp} works by ...'."
    if qtype == "QUERY_CAUSE" and disp:
        return f"I do not have a stored cause for {disp} yet. Tell me '... causes {subject}' to teach me."
    if qtype == "QUERY_IF_THEN" and subject:
        return f"I do not know what happens if {subject} yet. Teach me with: 'If {subject}, ...'."
    if qtype == "QUERY_PARTS" and disp:
        return f"I do not know the parts or branches of {disp} yet. Tell me '{disp} consists of ...' and I will bind it."
    if disp:
        return f"I do not have any stored knowledge about {disp} yet. Teach me a fact about it and I will reason with it right away."
    return "I do not have that in my memory yet. Teach me naturally in English or Hinglish and I will bind it into my hypergraph."
