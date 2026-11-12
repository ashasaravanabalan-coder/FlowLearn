"""Generative-AI layer: structured prompts for Groq, Gemini or Anthropic."""
import json, os, re
import requests

API_URL = "https://api.anthropic.com/v1/messages"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class LLMError(Exception):
    pass


MERMAID_RULES = (
    "Mermaid rules: start with 'flowchart TD'; give every node a short id (A, B, C...); "
    "terminals as A([Start]); process as B[\"text\"]; decisions as C{\"cond?\"} with edges labelled |Yes| and |No|; "
    "input/output as D[/\"text\"/]; always double-quote labels; never use markdown fences."
)

CODE_TO_FLOW = (
    "You are a programming tutor. Convert the user's code into a flowchart and explain it. "
    "Reply with ONLY a JSON object: {\"mermaid\": string, \"explanation\": [string, ...], \"summary\": string}. "
    "'explanation' is a list of short step-by-step descriptions; 'summary' is 1-2 sentences describing the algorithm "
    "(e.g. 'This program first accepts user input, checks whether the number is positive or negative...'). "
    "Use the ML analysis supplied as context to decide how much detail the flowchart needs. " + MERMAID_RULES
)

FLOW_TO_CODE = (
    "You are a programming tutor. Convert the user's flowchart (Mermaid syntax or plain-language steps) into working code "
    "in the requested language. Reply with ONLY a JSON object: {\"code\": string, \"explanation\": [string, ...], \"summary\": string, "
    "\"mermaid\": string}. 'mermaid' is a cleaned, valid version of the flowchart. " + MERMAID_RULES
)


def _parse(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
        raise LLMError("The AI returned an unreadable response. Try again.")


def _provider() -> str:
    """LLM_PROVIDER if set, else whichever API key is available (Groq, Gemini, Anthropic)."""
    p = os.getenv("LLM_PROVIDER", "").lower()
    if p in ("groq", "gemini", "anthropic"):
        return p
    if os.getenv("GROQ_API_KEY"):
        return "groq"
    if os.getenv("GEMINI_API_KEY"):
        return "gemini"
    return "anthropic"


def _call_groq(system: str, user: str) -> str:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise LLMError("GROQ_API_KEY is not set. Add it to your environment and restart the server.")
    r = requests.post(GROQ_URL, timeout=40,
                      headers={"Authorization": f"Bearer {key}", "content-type": "application/json"},
                      json={"model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                            "messages": [{"role": "system", "content": system},
                                         {"role": "user", "content": user}],
                            "response_format": {"type": "json_object"},
                            "temperature": 0.2, "max_tokens": 2000})
    if r.status_code != 200:
        raise LLMError(f"Groq API error {r.status_code}: {r.text[:200]}")
    try:
        return r.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise LLMError("Groq returned an empty response. Try again.")


def _call_gemini(system: str, user: str) -> str:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise LLMError("GEMINI_API_KEY is not set. Add it to your environment and restart the server.")
    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    r = requests.post(f"{GEMINI_URL}/{model}:generateContent", timeout=40,
                      headers={"x-goog-api-key": key, "content-type": "application/json"},
                      json={"systemInstruction": {"parts": [{"text": system}]},
                            "contents": [{"role": "user", "parts": [{"text": user}]}],
                            "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 4000}})
    if r.status_code != 200:
        raise LLMError(f"Gemini API error {r.status_code}: {r.text[:200]}")
    try:
        return "".join(p.get("text", "") for p in r.json()["candidates"][0]["content"]["parts"])
    except (KeyError, IndexError):
        raise LLMError("Gemini returned an empty response. Try again.")


def _call_anthropic(system: str, user: str) -> str:
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise LLMError("ANTHROPIC_API_KEY is not set. Add it to your environment and restart the server.")
    r = requests.post(API_URL, timeout=60, headers={
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5"), "max_tokens": 2000,
              "system": system, "messages": [{"role": "user", "content": user}]})
    if r.status_code != 200:
        raise LLMError(f"LLM API error {r.status_code}: {r.text[:200]}")
    return "".join(b.get("text", "") for b in r.json()["content"])


_CALLERS = {"groq": _call_groq, "gemini": _call_gemini, "anthropic": _call_anthropic}


def _ask(system: str, user: str) -> dict:
    try:
        return _parse(_CALLERS[_provider()](system, user))
    except requests.exceptions.RequestException:
        raise LLMError("Could not reach the AI service. Check your internet connection and try again.")


def code_to_flowchart(code: str, language: str, analysis: dict) -> dict:
    ctx = f"Language: {language}\nML analysis: {json.dumps(analysis)}\n\nCode:\n{code}"
    return _ask(CODE_TO_FLOW, ctx)


def flowchart_to_code(flow: str, language: str) -> dict:
    return _ask(FLOW_TO_CODE, f"Target language: {language}\n\nFlowchart:\n{flow}")