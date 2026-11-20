"""Samu Lab & OpenAI-compatible Language Cortex Bridge (strictly non-crashing)."""

import json
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional


def normalize_chat_url(url: Optional[str]) -> str:
    cleaned = (url or "").strip()
    if not cleaned:
        return ""
    if cleaned.endswith("/chat/completions"):
        return cleaned
    if cleaned.endswith("/v1") or cleaned.endswith("/v1/"):
        return cleaned.rstrip("/") + "/chat/completions"
    return cleaned.rstrip("/") + "/chat/completions"


def _post_json(
    url: str,
    payload: Dict[str, Any],
    api_key: Optional[str] = None,
    timeout: float = 20.0,
) -> Dict[str, Any]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "NSM-VB/1.4",
    }
    if api_key and api_key.strip():
        headers["Authorization"] = f"Bearer {api_key.strip()}"

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
        return {
            "status_code": getattr(resp, "status", 200),
            "data": json.loads(raw),
        }


def test_connection(
    llm_url: Optional[str],
    llm_model: Optional[str],
    llm_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Verify Samu Lab / custom API endpoint with latency and error details."""
    url = normalize_chat_url(llm_url)
    model = (llm_model or "").strip()
    if not url:
        return {"ok": False, "error": "API URL is empty."}
    if not model:
        return {"ok": False, "error": "Model name is empty."}

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Reply with OK only."},
            {"role": "user", "content": "Ping"},
        ],
        "temperature": 0.0,
        "max_tokens": 12,
        "stream": False,
    }
    t0 = time.time()
    try:
        res = _post_json(url, payload, api_key=llm_key, timeout=18.0)
        latency_ms = int((time.time() - t0) * 1000)
        choices = res["data"].get("choices", [])
        reply = ""
        if choices and isinstance(choices[0], dict):
            reply = (choices[0].get("message", {}).get("content") or "").strip()
        return {
            "ok": True,
            "status_code": res["status_code"],
            "latency_ms": latency_ms,
            "response": reply or "OK",
            "resolved_url": url,
        }
    except urllib.error.HTTPError as e:
        details = ""
        try:
            details = e.read().decode("utf-8", errors="replace")[:260]
        except Exception:
            pass
        return {
            "ok": False,
            "error": f"HTTP {e.code}: {e.reason}",
            "details": details,
            "resolved_url": url,
        }
    except urllib.error.URLError as e:
        return {
            "ok": False,
            "error": f"Connection failed: {e.reason}",
            "resolved_url": url,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": f"{type(e).__name__}: {e}",
            "resolved_url": url,
        }


def analyze_with_cortex(
    user_text: str,
    llm_url: Optional[str],
    llm_model: Optional[str],
    llm_key: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Optional API Cortex pass: detect sarcasm/feedback and extract typed triples."""
    url = normalize_chat_url(llm_url)
    model = (llm_model or "").strip()
    if not url or not model or not user_text.strip():
        return None

    system_prompt = (
        "You are the Language Cortex parser for NSM VB (a neuro-symbolic brain). "
        "Return ONLY valid compact JSON with keys:\n"
        '{"sentiment":"positive|negative|neutral","is_sarcastic":false,'
        '"facts":[{"agent":"","relation":"IS_A|CAN|HAS|LOCATED_IN|CREATED|PREFERS|ACTION","action":"","patient":"","polarity":1}]}\n'
        "Rules: Extract only facts explicitly stated by the user. Never invent facts. "
        "If user is sarcastically criticizing a previous answer, set sentiment='negative' and is_sarcastic=true."
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text[:600]},
        ],
        "temperature": 0.0,
        "max_tokens": 220,
        "stream": False,
    }
    try:
        res = _post_json(url, payload, api_key=llm_key, timeout=14.0)
        choices = res["data"].get("choices", [])
        if not choices:
            return None
        content = (choices[0].get("message", {}).get("content") or "").strip()
        # Strip optional markdown code fences
        if content.startswith("```"):
            content = content.strip("`")
            if content.lower().startswith("json"):
                content = content[4:].strip()
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        parsed = json.loads(content[start : end + 1])
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def realize_with_cortex(
    user_text: str,
    symbolic_answer: str,
    proof_steps: List[str],
    recalled_context: List[str],
    mode: str,
    llm_url: Optional[str],
    llm_model: Optional[str],
    llm_key: Optional[str] = None,
) -> Optional[str]:
    """Use Samu Lab / custom API as NSM's mouthpiece without hallucinating facts."""
    url = normalize_chat_url(llm_url)
    model = (llm_model or "").strip()
    if not url or not model:
        return None

    if mode == "unknown":
        system_prompt = (
            "You are NSM VB v1.4, a neuro-symbolic AI built by Muhammad Salman Shar at NeuraSaMu. "
            "Your symbolic memory did not find a stored answer for this user query. "
            "Respond helpfully and concisely in natural English using the recalled context if relevant, "
            "or politely explain what you can help with and invite the user to teach you. "
            "Keep your reply under 3 short sentences. Never claim to be ChatGPT or OpenAI."
        )
    else:
        system_prompt = (
            "You are the natural-language voice of NSM VB v1.4 (built by Muhammad Salman Shar at NeuraSaMu). "
            "Rewrite the verified symbolic brain answer into crisp, intelligent, natural English (1-3 sentences). "
            "STRICT RULES:\n"
            "1. Stay 100% faithful to the symbolic answer and proof trace.\n"
            "2. Never contradict the symbolic answer or invent unsupported facts.\n"
            "3. Never confuse user identity with your own identity.\n"
            "4. Output ONLY the final reply."
        )

    context_lines = []
    if symbolic_answer:
        context_lines.append(f"Symbolic Brain Answer: {symbolic_answer}")
    if proof_steps:
        context_lines.append("Proof Trace: " + " | ".join(proof_steps[:4]))
    if recalled_context:
        context_lines.append("Recalled Memory: " + " ; ".join(recalled_context[:4]))
    context_lines.append(f"User Message: {user_text[:400]}")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "\n".join(context_lines)},
        ],
        "temperature": 0.25 if mode != "unknown" else 0.45,
        "max_tokens": 140,
        "stream": False,
    }
    try:
        res = _post_json(url, payload, api_key=llm_key, timeout=20.0)
        choices = res["data"].get("choices", [])
        if not choices:
            return None
        out = (choices[0].get("message", {}).get("content") or "").strip().strip('"\'')
        if not out:
            return None
        leaks = ("symbolic brain answer", "proof trace:", "recalled memory:")
        if any(lk in out.lower() for lk in leaks):
            return None
        return out
    except Exception:
        return None
