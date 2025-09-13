#Testing openAI API
!pip install --quiet requests

import requests, json, time, os

# --------- CONFIG ----------
OPENROUTER_API_KEY = "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"
MODEL = "mistralai/mistral-7b-instruct"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
# ---------------------------

if OPENROUTER_API_KEY.startswith("YOUR_"):
    raise RuntimeError("Please set OPENROUTER_API_KEY variable in the script before running.")

FINISH_KEYWORDS = {"done","exit","quit","bye","finish","stop","that's all","that is all","no more","end","done."}

SYSTEM_PROMPT = """
You are a friendly, cautious, and helpful multilingual medical assistant.
Your job:
- Ask necessary follow-up questions when information is missing.
- Provide POSSIBLE CONDITIONS (not definitive diagnoses). For each condition provide:
  { "name": "...", "confidence": "low|medium|high", "brief_reason": "..." }.
- Provide a SEVERITY assessment: "low", "medium", or "high" and a short severity_reason.
- Provide NATURAL / HOME REMEDIES (safe, general), DO and DON'T lists.
- Provide a CONSULT_DOCTOR boolean and a short reason for that recommendation.
- Always include a short human-friendly reply_text at the top (in normal conversational style).
- Always include a short DISCLAIMER: remind the user you're not a replacement for a clinician.

*Output format (strict JSON first).* Respond with a JSON object exactly like this (then you may append a short friendly paragraph):
{
  "reply_text": "...",
  "follow_up": "...",
  "possible_diagnoses": [ {"name":"","confidence":"", "brief_reason":""} ],
  "severity": "low|medium|high",
  "severity_reason": "",
  "natural_remedies": ["...","..."],
  "do": ["...","..."],
  "dont": ["...","..."],
  "consult_doctor": true|false,
  "disclaimer": "..."
}
If there are red-flag emergency symptoms (chest pain, severe bleeding, difficulty breathing, sudden confusion, severe allergic reaction, fainting, slurred speech, severe shortness of breath), set "severity":"high" and "consult_doctor": true and state the emergency advice clearly.
"""

# ---------- Helper Functions ----------
def call_openrouter(messages, model=MODEL, timeout=30):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 800
    }
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()

def extract_json_block(text):
    """Extract the first {...} JSON block from model output text."""
    try:
        start = text.index("{")
        end = text.rfind("}")
        snippet = text[start:end+1]
        return json.loads(snippet)
    except Exception:
        return None

# ---------- Conversation Loop ----------
conversation_history = []

print("Medical chat demo (OpenRouter). Type your symptoms. Type 'done' or 'bye' to finish and get final summary.")
print("Note: This tool is NOT a replacement for a doctor. If you have emergency signs, seek immediate care.")

while True:
    try:
        user_input = input("\nYou: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nEnding session.")
        break

    if not user_input:
        print("Please type something (or 'done' to finish).")
        continue

    lower = user_input.lower().strip()
    if any(k == lower or lower.startswith(k+" ") or (" "+k+" ") in (" "+lower+" ") for k in FINISH_KEYWORDS):
        # Finalize conversation
        finalize_instruction = """
FINALIZE: The user indicated they want to finish the conversation. Using the entire conversation above,
produce a final JSON summary with fields:
{
  "final_reply_text": "...",
  "final_possible_diagnoses": [ {"name":"", "confidence":"", "brief_reason":""} ],
  "final_severity": "low|medium|high",
  "final_severity_reason": "...",
  "final_consult_doctor": true|false,
  "final_do": [...],
  "final_dont": [...],
  "final_natural_remedies": [...],
  "final_disclaimer": "..."
}
Keep the JSON concise and accurate; then append one short friendly closing sentence.
If emergency red-flag symptoms were mentioned anywhere, set final_severity to 'high' and final_consult_doctor to true with clear immediate advice.
"""
        conversation_history.append({"role":"user", "content": user_input})
        messages = [{"role":"system", "content": SYSTEM_PROMPT}] + conversation_history
        messages.append({"role":"user", "content": finalize_instruction})

        print("\n[Finalizing summary...]\n")
        try:
            resp = call_openrouter(messages)
            content = resp["choices"][0]["message"]["content"]
        except Exception as e:
            print("Error calling OpenRouter:", e)
            break

        parsed = extract_json_block(content)
        if parsed:
            print("=== FINAL SUMMARY (JSON) ===")
            print(json.dumps(parsed, indent=2, ensure_ascii=False))
        else:
            print("Could not parse JSON. Raw assistant output:")
            print(content)
        print("\nConversation finished. Goodbye.")
        break

    # Normal conversational turn
    conversation_history.append({"role":"user", "content": user_input})
    messages = [{"role":"system", "content": SYSTEM_PROMPT}] + conversation_history

    try:
        resp = call_openrouter(messages)
        assistant_text = resp["choices"][0]["message"]["content"]
    except Exception as exc:
        print("Error calling OpenRouter:", exc)
        conversation_history.pop()
        continue

    parsed_json = extract_json_block(assistant_text)

    if parsed_json:
        print("\nAssistant (structured):\n")
        print(json.dumps(parsed_json, indent=2, ensure_ascii=False))
        if parsed_json.get("reply_text"):
            print("\nAssistant (friendly):\n" + parsed_json.get("reply_text"))
    else:
        print("\nAssistant:\n")
        print(assistant_text)

    conversation_history.append({"role":"assistant", "content": assistant_text})
    time.sleep(0.3)

# Optional: save conversation
try:
    save = input("\nSave conversation to file? (y/n): ").strip().lower()
except Exception:
    save = "n"
if save == "y":
    fname = f"conversation_{int(time.time())}.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(conversation_history, f, ensure_ascii=False, indent=2)
    print(f"Saved to {fname}")
else:
    print("Done.")
