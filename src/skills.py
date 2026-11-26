"""Portable Prompt-to-Skill Engine for NSM VB v1.5+.

Enables zero-API users to generate portable JSON Skill Packs using any external AI
(ChatGPT, Gemini, Claude) via a structured Master Prompt, import/export them offline,
toggle skills ON/OFF cleanly, and prepare MCP tool bindings for future execution.
"""

import re
import time
from typing import Any, Dict, List, Optional, Tuple

from src.hypergraph import normalize_entity, tokenize_content
from src.parser import clean_phrase

ALLOWED_RELATIONS = frozenset({
    "IS_A", "DEFINED_AS", "ALSO_KNOWN_AS",
    "CAN", "HAS", "HAS_PART", "HAS_BRANCHES", "HAS_COUNT", "HAS_AGE",
    "USED_FOR", "CAUSES", "WORKS_BY", "IF_THEN",
    "CREATED", "LOCATED_IN", "ACTION", "COMPARED_TO", "RELATED_TO",
})

ALLOWED_QTYPES = frozenset({
    "QUERY_DEFINE", "QUERY_CLASS", "QUERY_ALIAS", "QUERY_VERIFY",
    "QUERY_CAN", "QUERY_CHOICE", "QUERY_CAUSE", "QUERY_IF_THEN",
    "QUERY_HOW", "QUERY_PURPOSE", "QUERY_PARTS", "QUERY_COMPARE",
    "QUERY_EXAMPLES", "QUERY_ROLE", "QUERY_FACT_META", "QUERY_FOLLOWUP",
})

AI_SKILL_GENERATOR_PROMPT = """You are generating a portable JSON Skill Pack for **NSM VB v1.5** (a deterministic, offline Neuro-Symbolic Virtual Brain).
Output ONLY valid raw JSON (no markdown fences, no commentary) following this exact schema:

{
  "nsm_version": "1.5",
  "package_type": "skill_pack",
  "skill": {
    "id": "snake_case_unique_id",
    "name": "Human Readable Skill Title",
    "version": "1.0.0",
    "author": "AI Generated",
    "description": "One clear sentence explaining what this skill teaches NSM.",
    "enabled": true,
    "trigger_keywords": ["keyword1", "keyword2", "keyword3"],
    "facts": [
      {
        "relation": "IS_A | DEFINED_AS | ALSO_KNOWN_AS | CAN | HAS | HAS_PART | HAS_BRANCHES | USED_FOR | CAUSES | WORKS_BY | IF_THEN | COMPARED_TO",
        "agent": "subject entity in lowercase",
        "patient": "object, definition, or consequence",
        "polarity": 1
      }
    ],
    "patterns": [
      {
        "id": "unique_rule_id",
        "kind": "question",
        "qtype": "QUERY_DEFINE | QUERY_CAUSE | QUERY_HOW | QUERY_PURPOSE | QUERY_PARTS | QUERY_VERIFY | QUERY_CAN | QUERY_IF_THEN | QUERY_COMPARE | QUERY_EXAMPLES",
        "pattern": "^regex with (.+?) capture group$",
        "slots": { "subject": 1 },
        "meta": { "relation": "DEFINED_AS" }
      }
    ],
    "workflows": [
      {
        "id": "wf_unique_id",
        "trigger": "short trigger phrase like how to debug x",
        "steps": [
          "Step 1 clear actionable instruction.",
          "Step 2 clear actionable instruction.",
          "Step 3 clear actionable instruction."
        ]
      }
    ],
    "mcp_tools": []
  }
}

Rules for high accuracy:
1. Use concise, atomic facts (8 to 25 facts per skill) with exact typed relations:
   - Use CAUSES for cause -> effect ("overheating" CAUSES "cpu throttling").
   - Use IF_THEN for condition -> consequence ("power is lost" IF_THEN "unsaved ram data is erased").
   - Use WORKS_BY for mechanism ("compiler" WORKS_BY "translating source code into machine code").
   - Use USED_FOR for utility ("index" USED_FOR "speeding up database queries").
   - Use HAS_PART for components ("cpu" HAS_PART "alu, control unit, and registers").
   - Use CAN with polarity 1 or -1 for capabilities/limits.
2. Keep regex patterns simple, valid Python regexes using `^...$` and `(.+?)`.
3. Add 1 to 4 step-by-step `workflows` for multi-step procedures.
4. Output ONLY valid JSON.

Now build a complete NSM Skill Pack for the following topic/task:
[WRITE YOUR SKILL TOPIC HERE]"""


def slugify_skill_id(raw: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", (raw or "").strip().lower()).strip("_")
    return s[:48] or f"skill_{int(time.time())}"


def validate_skill_pack(payload: Any) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """Validate a single `skill_pack` or multi-skill `skill_bundle` JSON object."""
    if not isinstance(payload, dict):
        return False, "Skill file must be a JSON object.", []

    pkg_type = str(payload.get("package_type", "")).strip().lower()
    raw_skills: List[Any] = []

    if pkg_type == "skill_pack" and isinstance(payload.get("skill"), dict):
        raw_skills = [payload["skill"]]
    elif pkg_type == "skill_bundle" and isinstance(payload.get("skills"), list):
        raw_skills = payload["skills"]
    elif isinstance(payload.get("skill"), dict):
        raw_skills = [payload["skill"]]
    elif isinstance(payload.get("name"), str) and (
        isinstance(payload.get("facts"), list) or isinstance(payload.get("workflows"), list)
    ):
        raw_skills = [payload]
    else:
        return False, "Unrecognized Skill JSON format. Expected package_type 'skill_pack' or 'skill_bundle'.", []

    normalized_skills: List[Dict[str, Any]] = []
    for item in raw_skills:
        if not isinstance(item, dict):
            return False, "Each skill entry must be a JSON object.", []

        name = str(item.get("name") or item.get("id") or "").strip()
        if not name:
            return False, "Skill is missing a 'name' field.", []

        sid = slugify_skill_id(str(item.get("id") or name))
        desc = str(item.get("description") or "").strip()
        version = str(item.get("version") or "1.0.0").strip()
        author = str(item.get("author") or "Community / AI").strip()
        enabled = bool(item.get("enabled", True))

        triggers = [
            normalize_entity(str(t))
            for t in (item.get("trigger_keywords") or [])
            if isinstance(t, str) and t.strip()
        ][:20]

        clean_facts: List[Dict[str, Any]] = []
        for fc in (item.get("facts") or [])[:150]:
            if not isinstance(fc, dict):
                continue
            rel = str(fc.get("relation") or "DEFINED_AS").strip().upper()
            if rel not in ALLOWED_RELATIONS:
                rel = "RELATED_TO"
            ag = clean_phrase(str(fc.get("agent") or ""))
            pat = clean_phrase(str(fc.get("patient") or ""))
            if not ag or not pat:
                continue
            pol = -1 if int(fc.get("polarity", 1)) < 0 else 1
            clean_facts.append({
                "relation": rel,
                "agent": ag.lower(),
                "patient": pat.lower(),
                "action": clean_phrase(str(fc.get("action") or "")).lower(),
                "modifier": clean_phrase(str(fc.get("modifier") or "")).lower(),
                "polarity": pol,
            })

        clean_patterns: List[Dict[str, Any]] = []
        for idx, pt in enumerate((item.get("patterns") or [])[:40]):
            if not isinstance(pt, dict) or not pt.get("pattern"):
                continue
            rx_str = str(pt["pattern"]).strip()
            try:
                re.compile(rx_str, re.IGNORECASE)
            except re.error:
                continue
            kind = str(pt.get("kind") or "question").strip().lower()
            qtype = str(pt.get("qtype") or "QUERY_DEFINE").strip().upper()
            rel = str(pt.get("relation") or "DEFINED_AS").strip().upper()
            if kind == "question" and qtype not in ALLOWED_QTYPES:
                continue
            if kind == "statement" and rel not in ALLOWED_RELATIONS:
                rel = "RELATED_TO"
            clean_patterns.append({
                "id": f"{sid}_{slugify_skill_id(str(pt.get('id') or f'pat_{idx}'))}",
                "skill_id": sid,
                "kind": kind,
                "qtype": qtype,
                "relation": rel,
                "pattern": rx_str,
                "slots": pt.get("slots") if isinstance(pt.get("slots"), dict) else {"subject": 1},
                "meta": pt.get("meta") if isinstance(pt.get("meta"), dict) else {},
            })

        clean_workflows: List[Dict[str, Any]] = []
        for idx, wf in enumerate((item.get("workflows") or [])[:25]):
            if not isinstance(wf, dict):
                continue
            trig = clean_phrase(str(wf.get("trigger") or wf.get("title") or "")).lower()
            steps = [str(s).strip() for s in (wf.get("steps") or []) if isinstance(s, str) and s.strip()][:15]
            if trig and steps:
                clean_workflows.append({
                    "id": f"{sid}_{slugify_skill_id(str(wf.get('id') or f'wf_{idx}'))}",
                    "trigger": trig,
                    "steps": steps,
                })

        mcp_tools = [
            t for t in (item.get("mcp_tools") or [])[:20]
            if isinstance(t, dict) and t.get("tool")
        ]

        if not clean_facts and not clean_patterns and not clean_workflows and not mcp_tools:
            return False, f"Skill '{name}' has no valid facts, patterns, workflows, or MCP tools.", []

        normalized_skills.append({
            "id": sid,
            "name": name,
            "version": version,
            "author": author,
            "description": desc,
            "enabled": enabled,
            "trigger_keywords": triggers,
            "facts": clean_facts,
            "patterns": clean_patterns,
            "workflows": clean_workflows,
            "mcp_tools": mcp_tools,
            "installed_at": float(item.get("installed_at") or time.time()),
        })

    return True, "Valid skill package.", normalized_skills


def _skill_source_tag(skill_id: str) -> str:
    return f"skill:{skill_id}"


def activate_skill_in_brain(brain: Any, skill: Dict[str, Any]) -> Dict[str, int]:
    """Bind an enabled skill's facts and custom patterns into the active brain."""
    sid = skill["id"]
    src_tag = _skill_source_tag(sid)
    facts_added = 0
    for fc in skill.get("facts", []):
        try:
            brain.hypergraph.add_frame(
                relation=fc["relation"],
                agent=fc["agent"],
                patient=fc["patient"],
                action=fc.get("action", ""),
                modifier=fc.get("modifier", ""),
                polarity=int(fc.get("polarity", 1)),
                source=src_tag,
                raw_text=f"[{skill['name']}] {fc['agent']} {fc['relation']} {fc['patient']}",
            )
            facts_added += 1
        except ValueError:
            pass

    pats = skill.get("patterns", [])
    pats_loaded = 0
    if pats:
        existing_ids = {p.get("id") for p in brain.language_extensions.get("custom_patterns", [])}
        new_pats = [p for p in pats if p.get("id") not in existing_ids]
        if new_pats:
            brain.language_extensions.setdefault("custom_patterns", []).extend(new_pats)
            pats_loaded = brain.parser.load_custom_patterns(new_pats)

    return {"facts_bound": facts_added, "patterns_loaded": pats_loaded}


def deactivate_skill_in_brain(brain: Any, skill_id: str) -> int:
    """Remove a skill's active frames and regex rules while keeping its definition saved."""
    src_tag = _skill_source_tag(skill_id)
    to_remove = [
        fid for fid, fr in brain.hypergraph.frames.items()
        if fr.get("source") == src_tag
    ]
    for fid in to_remove:
        fr = brain.hypergraph.frames.pop(fid, None)
        if fr:
            ag = fr.get("agent", "")
            pat = fr.get("patient", "")
            rel = fr.get("relation", "")
            if ag in brain.hypergraph._by_agent:
                brain.hypergraph._by_agent[ag].discard(fid)
                if not brain.hypergraph._by_agent[ag]:
                    del brain.hypergraph._by_agent[ag]
            if pat in brain.hypergraph._by_patient:
                brain.hypergraph._by_patient[pat].discard(fid)
                if not brain.hypergraph._by_patient[pat]:
                    del brain.hypergraph._by_patient[pat]
            if rel in brain.hypergraph._by_relation:
                brain.hypergraph._by_relation[rel].discard(fid)

    # Rebuild parser rules without this skill's patterns
    kept_pats = [
        p for p in brain.language_extensions.get("custom_patterns", [])
        if p.get("skill_id") != skill_id
    ]
    brain.language_extensions["custom_patterns"] = kept_pats
    brain.parser._compile_default_rules()
    if kept_pats:
        brain.parser.load_custom_patterns(kept_pats)
    return len(to_remove)


def install_skill_package(brain: Any, payload: Any) -> Dict[str, Any]:
    """Validate and install one or more portable skills into `brain`."""
    ok, msg, skills_list = validate_skill_pack(payload)
    if not ok:
        return {"ok": False, "error": msg}

    installed_summary: List[Dict[str, Any]] = []
    for sk in skills_list:
        sid = sk["id"]
        if sid in brain.skills.get("installed", {}):
            deactivate_skill_in_brain(brain, sid)
        brain.skills.setdefault("installed", {})[sid] = sk
        counts = {"facts_bound": 0, "patterns_loaded": 0}
        if sk.get("enabled", True):
            counts = activate_skill_in_brain(brain, sk)
        installed_summary.append({
            "id": sid,
            "name": sk["name"],
            "enabled": sk.get("enabled", True),
            "facts": counts["facts_bound"],
            "patterns": counts["patterns_loaded"],
            "workflows": len(sk.get("workflows", [])),
        })

    brain.updated_at = time.time()
    return {
        "ok": True,
        "installed": installed_summary,
        "message": f"Installed {len(installed_summary)} skill(s) successfully.",
    }


def toggle_skill(brain: Any, skill_id: str, enabled: bool) -> Dict[str, Any]:
    installed = brain.skills.get("installed", {})
    if skill_id not in installed:
        return {"ok": False, "error": f"Skill '{skill_id}' not found."}
    sk = installed[skill_id]
    sk["enabled"] = bool(enabled)
    if enabled:
        deactivate_skill_in_brain(brain, skill_id)
        counts = activate_skill_in_brain(brain, sk)
        brain.updated_at = time.time()
        return {"ok": True, "id": skill_id, "enabled": True, **counts}
    removed = deactivate_skill_in_brain(brain, skill_id)
    brain.updated_at = time.time()
    return {"ok": True, "id": skill_id, "enabled": False, "frames_deactivated": removed}


def delete_skill(brain: Any, skill_id: str) -> Dict[str, Any]:
    installed = brain.skills.get("installed", {})
    if skill_id not in installed:
        return {"ok": False, "error": f"Skill '{skill_id}' not found."}
    removed = deactivate_skill_in_brain(brain, skill_id)
    del installed[skill_id]
    brain.updated_at = time.time()
    return {"ok": True, "id": skill_id, "frames_removed": removed}


def export_skills_package(brain: Any, skill_id: Optional[str] = None) -> Dict[str, Any]:
    """Export either a single `skill_pack` or a full `skill_bundle`."""
    installed = brain.skills.get("installed", {})
    if skill_id:
        if skill_id not in installed:
            return {"ok": False, "error": f"Skill '{skill_id}' not found."}
        return {
            "ok": True,
            "filename": f"nsm_skill_{skill_id}.json",
            "package": {
                "nsm_version": brain.VERSION,
                "package_type": "skill_pack",
                "skill": installed[skill_id],
            },
        }
    return {
        "ok": True,
        "filename": "nsm_skills_bundle.json",
        "package": {
            "nsm_version": brain.VERSION,
            "package_type": "skill_bundle",
            "skills": list(installed.values()),
        },
    }


def list_skills_summary(brain: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for sid, sk in brain.skills.get("installed", {}).items():
        out.append({
            "id": sid,
            "name": sk.get("name", sid),
            "version": sk.get("version", "1.0.0"),
            "author": sk.get("author", "Community"),
            "description": sk.get("description", ""),
            "enabled": bool(sk.get("enabled", True)),
            "facts_count": len(sk.get("facts", [])),
            "patterns_count": len(sk.get("patterns", [])),
            "workflows_count": len(sk.get("workflows", [])),
            "mcp_tools_count": len(sk.get("mcp_tools", [])),
        })
    return out


def match_skill_workflow(brain: Any, query: str) -> Optional[Dict[str, Any]]:
    """Match an enabled skill's multi-step workflow if the user asks for a procedure."""
    q_norm = clean_phrase(query).lower()
    if not q_norm:
        return None
    q_tokens = set(tokenize_content(q_norm))

    best_match: Optional[Tuple[float, Dict[str, Any], Dict[str, Any]]] = None
    for sk in brain.skills.get("installed", {}).values():
        if not sk.get("enabled", True):
            continue
        for wf in sk.get("workflows", []):
            trig = wf.get("trigger", "")
            if not trig:
                continue
            if trig in q_norm or q_norm in trig:
                score = 1.0
            else:
                t_tokens = set(tokenize_content(trig))
                if not t_tokens or not q_tokens:
                    continue
                overlap = len(q_tokens.intersection(t_tokens))
                score = overlap / len(t_tokens)
            if score >= 0.72:
                if best_match is None or score > best_match[0]:
                    best_match = (score, sk, wf)

    if not best_match:
        return None

    score, sk, wf = best_match
    steps = wf.get("steps", [])
    formatted_steps = " ".join(f"Step {i+1}: {st}" for i, st in enumerate(steps))
    return {
        "skill_id": sk["id"],
        "skill_name": sk["name"],
        "workflow_id": wf["id"],
        "trigger": wf["trigger"],
        "confidence": round(min(0.96, 0.75 + score * 0.2), 3),
        "response": f"[{sk['name']}] {formatted_steps}",
        "proof_steps": [
            f"Matched enabled skill '{sk['name']}' workflow '{wf['trigger']}' ({len(steps)} steps)."
        ],
    }
