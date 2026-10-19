import urllib.request
import json
import os

DEFAULT_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama3-8b-8192"

# Strict prompt to stop hallucinations
SYSTEM_PROMPT = """You are NSM VB, a 10-year-old kid. 
You are talking to the USER. Rewrite the raw thought into ONE short, natural sentence. 
RULES:
1. Do NOT add new facts. Do NOT invent stories. Do NOT make up names.
2. NEVER pretend to be the user. If the user says "I am Salman", your response should be about THEM, not you.
3. If raw thought says "I don't know", just say it in a friendly way.
Output ONLY the rewritten sentence, nothing else."""

def improve_language(raw_text, user_input=""):
    url = os.environ.get("NSM_LLM_URL", DEFAULT_URL)
    model = os.environ.get("NSM_LLM_MODEL", DEFAULT_MODEL)
    api_key = os.environ.get("NSM_LLM_KEY", "")

    if url == DEFAULT_URL and not api_key:
        return raw_text

    # Pass ONLY the raw thought, not the user input (to avoid LLM getting confused)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Raw thought: {raw_text}"}
    ]

    data = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,  # Very low temperature (less creative, more strict)
        "max_tokens": 50,
        "stream": False
    }

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            out_text = result["choices"][0]["message"]["content"].strip()
            
            # 1. Remove quotes if LLM added them
            out_text = out_text.strip('"\'')
            
            # 2. HALLUCINATION FILTER: If output is way too long, it means LLM invented a story
            if len(out_text) > (len(raw_text) * 2.5) + 30:
                return raw_text
                
            # 3. LEAK FILTER: If LLM outputs prompt words
            bad_words = ["raw thought", "natural response", "user said", "rewrite"]
            if any(w in out_text.lower() for w in bad_words):
                return raw_text
                
            return out_text
    except Exception as e:
        print(f"[LLM Teacher Error] {e}")
        return raw_text
