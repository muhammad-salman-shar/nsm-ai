"""Natural Conversational English Realizer for NSM VB v1.5.

Converts verified symbolic hypergraph frames and reasoning traces into clean,
natural English responses tailored to all 16 question types.
"""

from typing import Any, Dict, List

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
    """Render any of the 14+ typed hypergraph relations into a clean English sentence."""
    ag = display_entity(fr.get("agent", ""))
    pat = (fr.get("patient") or "").strip()
    rel = (fr.get("relation") or "").upper()
    pol = int(fr.get("polarity", 1))
    mod = (fr.get("modifier") or "").strip()

    if rel == "IS_A":
        return f"{ag} is {'not ' if pol < 0 else ''}a {pat}."
    if rel == "DEFINED_AS":
        return f"{ag} is {'not ' if pol < 0 else ''}{pat}."
    if rel == "ALSO_KNOWN_AS":
        return f"{ag} is also known as {display_entity(pat)}."
    if rel == "CAN":
        return f"{ag} {'can' if pol > 0 else 'cannot'} {pat}."
    if rel == "USED_FOR":
        return f"{ag} is used for {pat}."
    if rel == "CAUSES":
        return f"{ag} causes {pat}."
    if rel == "WORKS_BY":
        return f"{ag} works by {pat}."
    if rel == "IF_THEN":
        raw_ag = (fr.get("agent") or "").strip()
        return f"If {raw_ag}, then {pat}."
    if rel == "HAS_PART":
        return f"{ag} consists of {pat}."
    if rel == "HAS_BRANCHES":
        return f"Major branches of {ag} include {pat}."
    if rel == "HAS_COUNT":
        return f"{ag} has {pat}."
    if rel == "HAS":
        return f"{ag} has {pat}."
    if rel == "HAS_AGE":
        return f"{ag} is {pat} years old."
    if rel == "LOCATED_IN":
        return f"{ag} is located in {pat}."
    if rel == "CREATED":
        act = fr.get("action") or "created"
        return f"{ag} {act} {display_entity(pat)}."
    if rel == "COMPARED_TO":
        if mod:
            return f"{ag} is {mod} than {display_entity(pat)}."
        return f"{ag} is compared to {display_entity(pat)}."
    if rel == "ACTION":
        act = mod or fr.get("action") or "acted on"
        return f"{ag} {act} {pat}."
    return f"{ag} {rel.lower().replace('_', ' ')} {pat}."


def realize_frames(frames: List[Dict[str, Any]], lang: str = "english", max_items: int = 4) -> str:
    seen = set()
    parts: List[str] = []
    for fr in frames[:max_items]:
        sent = frame_to_sentence(fr)
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
        return (
            f"My memory has conflicting evidence on whether {disp_s} matches '{target}'. "
            "Tell me which one is right so I can resolve it."
        )
    if mode in {"stored", "derived"}:
        evidence = frame_to_sentence(frames[0]) if frames else ""
        if pol > 0:
            return f"Yes — {evidence} (confidence {pct}%)."
        return f"No — {evidence} (confidence {pct}%)."
    if frames:
        known_txt = realize_frames(frames, max_items=2)
        return f"I do not have direct confirmation that {disp_s} is '{target}'. What I do know: {known_txt}"
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
        return f"Based on my memory, {disp_s} is a {option_a}" + (f", not a {option_b}." if b_neg else ".")
    if b_pos and not a_pos:
        return f"Based on my memory, {disp_s} is a {option_b}" + (f", not a {option_a}." if a_neg else ".")
    if a_pos and b_pos:
        return f"According to my memory, {disp_s} matches both {option_a} and {option_b}."
    return f"I do not have enough stored facts yet to decide whether {disp_s} is {option_a} or {option_b}."


def realize_comparison(comp: Dict[str, Any], lang: str = "english") -> str:
    a = display_entity(comp.get("entity_a", ""))
    b = display_entity(comp.get("entity_b", ""))
    direct = comp.get("direct_comparisons", [])
    fa = comp.get("frames_a", [])
    fb = comp.get("frames_b", [])
    shared = comp.get("shared_categories", [])

    if comp.get("mode") == "unknown":
        return f"I do not have stored facts on {a} and {b} yet to compare them. Teach me a fact about each and ask again."

    lines: List[str] = []
    seen = set()

    def _add(text: str) -> None:
        if text and text not in seen:
            seen.add(text)
            lines.append(text)

    for fr in direct[:2]:
        _add(frame_to_sentence(fr))
    if shared:
        _add(f"Both belong to: {', '.join(shared)}.")
    for fr in fa[:2]:
        _add(frame_to_sentence(fr))
    for fr in fb[:2]:
        _add(frame_to_sentence(fr))

    # Only mention missing details if an entity has zero facts AND no direct comparison exists
    if not direct:
        if not fa:
            _add(f"(I have no stored details on {a} yet.)")
        if not fb:
            _add(f"(I have no stored details on {b} yet.)")

    return " ".join(lines)


def realize_examples(category: str, res: Dict[str, Any], lang: str = "english") -> str:
    disp_c = display_entity(category)
    examples = res.get("examples", [])
    frames = res.get("frames", [])

    if examples:
        nice_list = ", ".join(display_entity(e) for e in examples)
        return f"Examples of {disp_c} in my memory include: {nice_list}."
    if frames:
        return realize_frames(frames, max_items=3)
    return f"I do not have any examples of {disp_c} stored yet. You can teach me with 'X is a {category}'."


def realize_unknown(
    qtype: str = "",
    subject: str = "",
    lang: str = "english",
) -> str:
    """Context-aware, natural English fallback when memory does not hold the answer."""
    disp = display_entity(subject) if subject else ""
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
    return "I do not have that in my memory yet. Teach me in natural English and I will bind it into my hypergraph."
