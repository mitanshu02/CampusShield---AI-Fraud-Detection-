# backend/routes/url_routes.py

from fastapi import APIRouter
from pydantic import BaseModel
from analyzers.url_analyzer import analyze_url
from services.ai_explainer_service import generate_explanation

router = APIRouter()

class URLRequest(BaseModel):
    url: str

@router.post("/analyze-url")
def analyze_url_endpoint(body: URLRequest):

    # Step 1 — run all 4 signal checks
    result = analyze_url(body.url)

    # Step 2 — add risk_score alias so scan_routes can find it
    result["risk_score"] = result.get("final_score", 0)

    # Step 3 — generate plain-English explanation via Groq/Gemini
    explanation = generate_explanation(
        signals    = result.get("signals", {}),
        risk_score = result.get("final_score", 0),
        url        = body.url
    )

    # Step 4 — attach explanation fields
    result["explanation"]             = explanation.get("explanation")
    result["impersonation_statement"] = explanation.get("impersonation_statement")
    result["attack_type"]             = explanation.get("attack_type")

    return result
