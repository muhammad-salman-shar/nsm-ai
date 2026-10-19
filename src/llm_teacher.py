import urllib.request
import json
import os

# NSM Teacher Bridge - Supports Local LLMs (Ollama, LM Studio, etc.)
# Env Vars:
# NSM_LLM_URL: e.g. http://127.0.0.1:1234/v1/chat/completions
# NSM_LLM_MODEL: e.g. llama3, mistral
# NSM_LLM_KEY: Optional. Leave blank for local.

DEFAULT_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama3-8b-8192"

SYSTEM_PROMPT = """You are NSM VB, a 10-year-old virtual kid. 
I will give you my internal raw thought or response. 
Your job is to rewrite it into natural, conversational English, exactly like a smart 10-year-old kid would speak.
RULES:
1. Keep the EXACT same meaning and facts.
2. Do NOT add any new information.
3. Do NOT hallucinate.
4. Just make it sound natural, warm, and human-like."""

def improve_language(raw_text, user_input=""):
    # Read config from environment
    url = os.environ.get("NSM_LLM_URL", DEFAULT_URL)
    model = os.environ.get("NSM_LLM_MODEL", DEFAULT_MODEL)
    api_key = os.environ.get("NSM_LLM_KEY", "")

    # If using default Groq URL and no key is provided, skip API call
    if url == DEFAULT_URL and not api_key:
        return raw_text

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"User said: {user_input}\nMy raw thought: {raw_text}\nMy natural response:"}
    ]

    data = {
        "model": model,
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 100,
        "stream": False
    }

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode())
            return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[LLM Teacher Error] {e}")
        return raw_text # Fallback
