# ai_explainer_service.py

import json
import re
from groq import Groq
from config import GROQ_API_KEY

groq_client = Groq(api_key=GROQ_API_KEY)

SAFE_FALLBACK = {
    "explanation": "This URL appears to be legitimate. Our scan found no signs of phishing, typosquatting, or suspicious activity. You can visit this website safely.",
    "impersonation_statement": "No specific impersonation target identified.",
    "attack_type": "No threat detected"
}

THREAT_FALLBACK = {
    "explanation": "This URL shows signs of being a phishing attempt targeting college students. Attackers create fake versions of trusted websites to steal payment details or login credentials. If you had visited this page and entered your information, it would have gone directly to a scammer.",
    "impersonation_statement": "No specific impersonation target identified.",
    "attack_type": "Phishing Attempt"
}

UPI_FALLBACK = {
    "explanation": "This page is designed to steal your UPI payment credentials. It asks for your UPI PIN directly on a webpage — something no legitimate payment app ever does. If you had entered your PIN here, a scammer would have instant access to your bank account.",
    "impersonation_statement": "No specific impersonation target identified.",
    "attack_type": "UPI Collect Fraud"
}
def build_prompt(signals: dict, risk_score: int, url: str) -> str:
    if risk_score < 40:
        tone = "SAFE — confirm the URL is legitimate and explain what was checked"
    elif risk_score < 70:
        tone = "CAUTIOUS — explain mild concern without alarming"
    else:
        tone = "THREAT — explain the danger clearly and specifically"

    # simplify signals to avoid Groq JSON overflow
    url_signals = signals.get("url_signals", signals)
    simple_signals = {}

    # extract only the key fields Groq needs
    if isinstance(url_signals, dict):
        for key, val in url_signals.items():
            if isinstance(val, dict):
                simple_signals[key] = {
                    "score":  val.get("score", 0),
                    "detail": val.get("detail", "")[:120]
                }

    payment_signals = signals.get("payment_signals", [])
    payment_risk    = signals.get("payment_risk", 0)
    payment_context = ""

    if payment_signals:
        signal_names    = [s.get("signal", "") for s in payment_signals]
        payment_context = f"""
Payment fraud signals (risk: {payment_risk}/100): {', '.join(signal_names)}
IMPORTANT: explanation MUST mention UPI PIN fraud. attack_type MUST be: UPI Collect Fraud
"""

    return f"""You are a cybersecurity educator for college students.

URL: {url}
Risk score: {risk_score}/100
Tone: {tone}
Signals: {json.dumps(simple_signals)}
{payment_context}
Rules:
- risk below 40 = attack_type must be: No threat detected
- risk below 40 = reassuring explanation only
- exactly 3 sentences in explanation
- no markdown, no code fences, pure JSON only

Respond with ONLY this JSON:
{{"explanation": "3 sentences.", "impersonation_statement": "One sentence or: No specific impersonation target identified.", "attack_type": "3 words max"}}"""

def call_groq(signals: dict, risk_score: int, url: str) -> dict | None:
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": build_prompt(signals, risk_score, url)
            }],
            max_tokens=400,
            temperature=0.2,
        )
        text = response.choices[0].message.content.strip()

        # aggressive cleaning
        text = text.replace("```json", "").replace("```", "").strip()

        # extract JSON block only
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start != -1 and end > start:
            text = text[start:end]

        # fix common Groq JSON issues
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
        text = text.replace('\u201c', '"').replace('\u201d', '"')
        text = text.replace('\u2018', "'").replace('\u2019', "'")

        result = json.loads(text)

        # safety override
        if risk_score < 40:
            result["attack_type"] = "No threat detected"

        return result
    except Exception as e:
        print(f"Groq failed: {e}")
        return None


def generate_explanation(
    signals:    dict,
    risk_score: int = 0,
    url:        str = ""
) -> dict:
    # Groq only — no Gemini
    result = call_groq(signals, risk_score, url)
    if result:
        return result

    # smart fallback
    if signals.get("payment_signals") and risk_score >= 40:
        return UPI_FALLBACK

    return SAFE_FALLBACK if risk_score < 40 else THREAT_FALLBACK
