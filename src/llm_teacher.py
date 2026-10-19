import urllib.request
import json
import os

# NSM Teacher Bridge
# By default, it uses Groq API (Free & Fast), but can work with any OpenAI-compatible endpoint.

API_KEY_ENV = "NSM_LLM_KEY"
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
    api_key = os.environ.get(API_KEY_ENV)
    if not api_key:
        # Fallback: No API key, return raw text
        return raw_text

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"User said: {user_input}\nMy raw thought: {raw_text}\nMy natural response:"}
    ]

    data = {
        "model": DEFAULT_MODEL,
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 100
    }

    req = urllib.request.Request(DEFAULT_URL, data=json.dumps(data).encode(), headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    })

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[LLM Teacher Error] {e}")
        return raw_text # Fallback to raw brain text if API fails
