# backend/routes/scan_routes.py

from fastapi import APIRouter, HTTPException
from models.scan_result_model import ScanRequest
from config import RISK_HIGH, RISK_MEDIUM
import httpx
import asyncio

router = APIRouter()

# ── helpers ───────────────────────────────────────────────────────────────────

def calculate_verdict(score: int) -> str:
    if score >= RISK_HIGH:
        return "HIGH RISK"
    elif score >= RISK_MEDIUM:
        return "MEDIUM RISK"
    else:
        return "SAFE"


def calculate_overall_risk(
    url_score:     int | None,
    visual_score:  int | None,
    payment_score: int | None
) -> int:
    scores  = []
    weights = []

    if url_score is not None:
        scores.append(url_score)
        weights.append(0.25)

    if visual_score is not None:
        scores.append(visual_score)
        weights.append(0.35)

    if payment_score is not None:
        scores.append(payment_score)
        weights.append(0.40)

    if not scores:
        return 0

    total_weight = sum(weights)
    weighted_sum = sum(
        s * (w / total_weight)
        for s, w in zip(scores, weights)
    )

    return round(weighted_sum)


# ── unified scan endpoint ─────────────────────────────────────────────────────

@router.post("/scan")
async def full_scan(request: ScanRequest):
    url = request.url.strip()

    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")

    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    # step 1 — run URL scan first
    async with httpx.AsyncClient(timeout=60.0) as client:
        url_result = await _run_url_scan(client, url)

    # step 2 — check if typosquatting detected OR demo localhost URL
    typosquat_match = None
    if url_result:
        typosquat_match = (
            url_result.get("signals", {})
                      .get("typosquatting", {})
                      .get("matched_domain")
        )

    is_demo_url     = "localhost" in url or "127.0.0.1" in url
    run_visual      = typosquat_match is not None or is_demo_url

    # step 3 — run visual and payment in parallel
    async with httpx.AsyncClient(timeout=120.0) as client:
        if run_visual:
            visual_task, payment_task = await asyncio.gather(
                _run_visual_scan(client, url),
                _run_payment_scan(client, url),
                return_exceptions=True
            )
            visual_result  = visual_task  if not isinstance(visual_task,  Exception) else None
            payment_result = payment_task if not isinstance(payment_task, Exception) else None
        else:
            payment_tasks  = await asyncio.gather(
                _run_payment_scan(client, url),
                return_exceptions=True
            )
            visual_result  = None
            payment_result = payment_tasks[0] if not isinstance(payment_tasks[0], Exception) else None

    # extract scores safely
    url_score = (
        url_result.get("risk_score") or
        url_result.get("final_score") or
        0
    ) if url_result else None

    visual_score = None
    if visual_result and visual_result.get("available"):
        sim = visual_result.get("visual_similarity")
        if sim is not None and sim > 0:
            visual_score = sim

    payment_score = None
    if payment_result and payment_result.get("available"):
        pr = payment_result.get("payment_risk")
        if pr is not None and pr > 0:
            payment_score = pr

    overall_risk = calculate_overall_risk(url_score, visual_score, payment_score)
    verdict      = calculate_verdict(overall_risk)

    # pull explanation fields from url_result
    explanation             = url_result.get("explanation")             if url_result else None
    impersonation_statement = url_result.get("impersonation_statement") if url_result else None
    attack_type             = url_result.get("attack_type")             if url_result else None

    # upgrade explanation if payment found high risk
    payment_has_high_risk = (
        payment_result and
        payment_result.get("available") and
        payment_result.get("payment_risk", 0) >= 70
    )

    if payment_has_high_risk:
        from services.ai_explainer_service import generate_explanation
        combined_signals = {
            "url_signals":     url_result.get("signals", {}) if url_result else {},
            "payment_signals": payment_result.get("upi_signals", []),
            "payment_risk":    payment_result.get("payment_risk", 0),
            "url_risk":        url_score or 0,
            "overall_risk":    overall_risk
        }
        upgraded = generate_explanation(
            signals    = combined_signals,
            risk_score = overall_risk,
            url        = url
        )
        explanation             = upgraded.get("explanation")
        impersonation_statement = upgraded.get("impersonation_statement")
        attack_type             = upgraded.get("attack_type")

    return {
        "url":                     url,
        "overall_risk":            overall_risk,
        "verdict":                 verdict,
        "url_scan":                url_result,
        "visual_scan":             visual_result or {
            "visual_similarity": None,
            "detected_brand":    None,
            "heatmap_url":       None,
            "risk":              None,
            "available":         False,
            "reason":            "Visual scan not triggered — no typosquatting detected"
        },
        "payment_scan":            payment_result or {
            "payment_risk":        0,
            "reasons":             ["Payment scan unavailable"],
            "upi_signals":         [],
            "deep_scan_triggered": False,
            "deep_scan_note":      None,
            "available":           False
        },
        "explanation":             explanation,
        "impersonation_statement": impersonation_statement,
        "attack_type":             attack_type,
    }


# ── internal helpers ──────────────────────────────────────────────────────────

async def _run_url_scan(client: httpx.AsyncClient, url: str) -> dict:
    try:
        response = await client.post(
            "http://localhost:8000/api/analyze-url",
            json={"url": url},
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"URL scan failed: {e}")
        return None


async def _run_visual_scan(client: httpx.AsyncClient, url: str) -> dict:
    try:
        response = await client.post(
            "http://localhost:8000/api/analyze-visual",
            json={"url": url},
            timeout=60.0
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Visual scan failed: {e}")
        return None


async def _run_payment_scan(client: httpx.AsyncClient, url: str) -> dict:
    try:
        response = await client.post(
            "http://localhost:8000/api/analyze-payment",
            json={"url": url},
            timeout=90.0
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Payment scan failed: {e}")
        return None


# -------------------------------------------------------------------------------------

# # backend/routes/scan_routes.py

# from fastapi import APIRouter, HTTPException
# from models.scan_result_model import ScanRequest
# from config import RISK_HIGH, RISK_MEDIUM
# import httpx
# import asyncio

# router = APIRouter()

# # ── helpers ───────────────────────────────────────────────────────────────────

# def calculate_verdict(score: int) -> str:
#     if score >= RISK_HIGH:
#         return "HIGH RISK"
#     elif score >= RISK_MEDIUM:
#         return "MEDIUM RISK"
#     else:
#         return "SAFE"


# def calculate_overall_risk(
#     url_score:     int | None,
#     visual_score:  int | None,
#     payment_score: int | None
# ) -> int:
#     scores  = []
#     weights = []

#     if url_score is not None:
#         scores.append(url_score)
#         weights.append(0.25)

#     if visual_score is not None:
#         scores.append(visual_score)
#         weights.append(0.35)

#     if payment_score is not None:
#         scores.append(payment_score)
#         weights.append(0.40)

#     if not scores:
#         return 0

#     total_weight = sum(weights)
#     weighted_sum = sum(
#         s * (w / total_weight)
#         for s, w in zip(scores, weights)
#     )

#     return round(weighted_sum)


# # ── unified scan endpoint ─────────────────────────────────────────────────────

# @router.post("/scan")
# async def full_scan(request: ScanRequest):
#     url = request.url.strip()

#     if not url:
#         raise HTTPException(status_code=400, detail="URL cannot be empty")

#     if not url.startswith("http://") and not url.startswith("https://"):
#         url = "https://" + url

#     # step 1 — run URL scan first
#     async with httpx.AsyncClient(timeout=30.0) as client:
#         url_result = await _run_url_scan(client, url)

#     # step 2 — check if typosquatting detected OR demo localhost URL
#     typosquat_match = None
#     if url_result:
#         typosquat_match = (
#             url_result.get("signals", {})
#                       .get("typosquatting", {})
#                       .get("matched_domain")
#         )

#     is_demo_url      = "localhost" in url or "127.0.0.1" in url
#     run_visual_scan  = typosquat_match is not None or is_demo_url

#     # step 3 — run visual and payment in parallel
#     async with httpx.AsyncClient(timeout=30.0) as client:
#         if run_visual_scan:
#             visual_task, payment_task = await asyncio.gather(
#                 _run_visual_scan(client, url),
#                 _run_payment_scan(client, url),
#                 return_exceptions=True
#             )
#             visual_result  = visual_task  if not isinstance(visual_task,  Exception) else None
#             payment_result = payment_task if not isinstance(payment_task, Exception) else None
#         else:
#             payment_task   = await asyncio.gather(
#                 _run_payment_scan(client, url),
#                 return_exceptions=True
#             )
#             visual_result  = None
#             payment_result = payment_task[0] if not isinstance(payment_task[0], Exception) else None

#     # extract scores safely
#     url_score = (
#         url_result.get("risk_score") or
#         url_result.get("final_score") or
#         0
#     ) if url_result else None

#     visual_score = None
#     if visual_result and visual_result.get("available"):
#         sim = visual_result.get("visual_similarity")
#         if sim is not None and sim > 0:
#             visual_score = sim

#     payment_score = None
#     if payment_result and payment_result.get("available"):
#         pr = payment_result.get("payment_risk")
#         if pr is not None and pr > 0:
#             payment_score = pr

#     overall_risk = calculate_overall_risk(url_score, visual_score, payment_score)
#     verdict      = calculate_verdict(overall_risk)

#     # pull explanation fields from url_result
#     explanation             = url_result.get("explanation")             if url_result else None
#     impersonation_statement = url_result.get("impersonation_statement") if url_result else None
#     attack_type             = url_result.get("attack_type")             if url_result else None

#     # upgrade explanation if payment found high risk
#     payment_has_high_risk = (
#         payment_result and
#         payment_result.get("available") and
#         payment_result.get("payment_risk", 0) >= 70
#     )

#     if payment_has_high_risk:
#         from services.ai_explainer_service import generate_explanation
#         combined_signals = {
#             "url_signals":     url_result.get("signals", {}) if url_result else {},
#             "payment_signals": payment_result.get("upi_signals", []),
#             "payment_risk":    payment_result.get("payment_risk", 0),
#             "url_risk":        url_score or 0,
#             "overall_risk":    overall_risk
#         }
#         upgraded = generate_explanation(
#             signals    = combined_signals,
#             risk_score = overall_risk,
#             url        = url
#         )
#         explanation             = upgraded.get("explanation")
#         impersonation_statement = upgraded.get("impersonation_statement")
#         attack_type             = upgraded.get("attack_type")

#     return {
#         "url":                     url,
#         "overall_risk":            overall_risk,
#         "verdict":                 verdict,
#         "url_scan":                url_result,
#         "visual_scan":             visual_result or {
#             "visual_similarity": None,
#             "detected_brand":    None,
#             "heatmap_url":       None,
#             "risk":              None,
#             "available":         False,
#             "reason":            "Visual scan not triggered — no typosquatting detected"
#         },
#         "payment_scan":            payment_result or {
#             "payment_risk":        0,
#             "reasons":             ["Payment scan unavailable"],
#             "upi_signals":         [],
#             "deep_scan_triggered": False,
#             "deep_scan_note":      None,
#             "available":           False
#         },
#         "explanation":             explanation,
#         "impersonation_statement": impersonation_statement,
#         "attack_type":             attack_type,
#     }


# # ── internal helpers ──────────────────────────────────────────────────────────

# async def _run_url_scan(client: httpx.AsyncClient, url: str) -> dict:
#     try:
#         response = await client.post(
#             "http://localhost:8000/api/analyze-url",
#             json={"url": url},
#             timeout=20.0
#         )
#         response.raise_for_status()
#         return response.json()
#     except Exception as e:
#         print(f"URL scan failed: {e}")
#         return None


# async def _run_visual_scan(client: httpx.AsyncClient, url: str) -> dict:
#     try:
#         response = await client.post(
#             "http://localhost:8000/api/analyze-visual",
#             json={"url": url},
#             timeout=25.0
#         )
#         response.raise_for_status()
#         return response.json()
#     except Exception as e:
#         print(f"Visual scan failed: {e}")
#         return None


# async def _run_payment_scan(client: httpx.AsyncClient, url: str) -> dict:
#     try:
#         response = await client.post(
#             "http://localhost:8000/api/analyze-payment",
#             json={"url": url},
#             # timeout=20.0
#             timeout=60.0
#         )
#         response.raise_for_status()
#         return response.json()
#     except Exception as e:
#         print(f"Payment scan failed: {e}")
#         return None



# ====================================================
# # backend/routes/scan_routes.py

# from fastapi import APIRouter, HTTPException
# from models.scan_result_model import ScanRequest
# from config import RISK_HIGH, RISK_MEDIUM
# import httpx
# import asyncio

# router = APIRouter()

# # ── helpers ───────────────────────────────────────────────────────────────────

# def calculate_verdict(score: int) -> str:
#     if score >= RISK_HIGH:
#         return "HIGH RISK"
#     elif score >= RISK_MEDIUM:
#         return "MEDIUM RISK"
#     else:
#         return "SAFE"


# def calculate_overall_risk(
#     url_score:     int | None,
#     visual_score:  int | None,
#     payment_score: int | None
# ) -> int:
#     scores  = []
#     weights = []

#     if url_score is not None:
#         scores.append(url_score)
#         weights.append(0.25)

#     if visual_score is not None:
#         scores.append(visual_score)
#         weights.append(0.35)

#     if payment_score is not None:
#         scores.append(payment_score)
#         weights.append(0.40)

#     if not scores:
#         return 0

#     total_weight = sum(weights)
#     weighted_sum = sum(
#         s * (w / total_weight)
#         for s, w in zip(scores, weights)
#     )

#     return round(weighted_sum)
# # def calculate_overall_risk(
# #     url_score:     int | None,
# #     visual_score:  int | None,
# #     payment_score: int | None
# # ) -> int:
# #     scores  = []
# #     weights = []

# #     if url_score is not None:
# #         scores.append(url_score)
# #         weights.append(0.30)

# #     if visual_score is not None and visual_score > 0:
# #         scores.append(visual_score)
# #         weights.append(0.30)

# #     if payment_score is not None and payment_score > 0:
# #         scores.append(payment_score)
# #         weights.append(0.40)

# #     if not scores:
# #         return 0

# #     total_weight = sum(weights)
# #     weighted_sum = sum(
# #         s * (w / total_weight)
# #         for s, w in zip(scores, weights)
# #     )

# #     return round(weighted_sum)

# # ── unified scan endpoint ─────────────────────────────────────────────────────
# @router.post("/scan")
# async def full_scan(request: ScanRequest):
#     url = request.url.strip()

#     if not url:
#         raise HTTPException(status_code=400, detail="URL cannot be empty")

#     if not url.startswith("http://") and not url.startswith("https://"):
#         url = "https://" + url

#     # step 1 — run URL scan first to check for typosquatting
#     async with httpx.AsyncClient(timeout=30.0) as client:
#         url_result = await _run_url_scan(client, url)

#     # step 2 — check if typosquatting was detected
#     typosquat_match = None
#     if url_result:
#         typosquat_match = (
#             url_result.get("signals", {})
#                       .get("typosquatting", {})
#                       .get("matched_domain")
#         )

#     # step 3 — run visual and payment in parallel
#     # only run visual if typosquatting detected
#     async with httpx.AsyncClient(timeout=30.0) as client:
#         if typosquat_match:
#             visual_task, payment_task = await asyncio.gather(
#                 _run_visual_scan(client, url),
#                 _run_payment_scan(client, url),
#                 return_exceptions=True
#             )
#             visual_result  = visual_task  if not isinstance(visual_task,  Exception) else None
#             payment_result = payment_task if not isinstance(payment_task, Exception) else None
#         else:
#             payment_task = await asyncio.gather(
#                 _run_payment_scan(client, url),
#                 return_exceptions=True
#             )
#             visual_result  = None
#             payment_result = payment_task[0] if not isinstance(payment_task[0], Exception) else None

#     # extract scores safely
#     url_score = (
#         url_result.get("risk_score") or
#         url_result.get("final_score") or
#         0
#     ) if url_result else None

#     visual_score = None
#     if visual_result and visual_result.get("available"):
#         sim = visual_result.get("visual_similarity")
#         if sim is not None and sim > 0:
#             visual_score = sim

#     payment_score = None
#     if payment_result and payment_result.get("available"):
#         pr = payment_result.get("payment_risk")
#         if pr is not None and pr > 0:
#             payment_score = pr

#     overall_risk = calculate_overall_risk(url_score, visual_score, payment_score)
#     verdict      = calculate_verdict(overall_risk)

#     # pull explanation fields
#     explanation             = url_result.get("explanation")             if url_result else None
#     impersonation_statement = url_result.get("impersonation_statement") if url_result else None
#     attack_type             = url_result.get("attack_type")             if url_result else None

#     # upgrade explanation if payment found high risk
#     payment_has_high_risk = (
#         payment_result and
#         payment_result.get("available") and
#         payment_result.get("payment_risk", 0) >= 70
#     )

#     if payment_has_high_risk:
#         from services.ai_explainer_service import generate_explanation
#         combined_signals = {
#             "url_signals":     url_result.get("signals", {}) if url_result else {},
#             "payment_signals": payment_result.get("upi_signals", []),
#             "payment_risk":    payment_result.get("payment_risk", 0),
#             "url_risk":        url_score or 0,
#             "overall_risk":    overall_risk
#         }
#         upgraded = generate_explanation(
#             signals    = combined_signals,
#             risk_score = overall_risk,
#             url        = url
#         )
#         explanation             = upgraded.get("explanation")
#         impersonation_statement = upgraded.get("impersonation_statement")
#         attack_type             = upgraded.get("attack_type")

#     return {
#         "url":                     url,
#         "overall_risk":            overall_risk,
#         "verdict":                 verdict,
#         "url_scan":                url_result,
#         "visual_scan":             visual_result or {
#             "visual_similarity": None,
#             "detected_brand":    None,
#             "heatmap_url":       None,
#             "risk":              None,
#             "available":         False,
#             "reason":            "Visual scan not triggered — no typosquatting detected"
#         },
#         "payment_scan":            payment_result or {
#             "payment_risk":        0,
#             "reasons":             ["Payment scan unavailable"],
#             "upi_signals":         [],
#             "deep_scan_triggered": False,
#             "deep_scan_note":      None,
#             "available":           False
#         },
#         "explanation":             explanation,
#         "impersonation_statement": impersonation_statement,
#         "attack_type":             attack_type,
#     }
# # @router.post("/scan")
# # async def full_scan(request: ScanRequest):
# #     url = request.url.strip()

# #     if not url:
# #         raise HTTPException(status_code=400, detail="URL cannot be empty")

# #     if not url.startswith("http://") and not url.startswith("https://"):
# #         url = "https://" + url

# #     async with httpx.AsyncClient(timeout=30.0) as client:
# #         tasks = await asyncio.gather(
# #             _run_url_scan(client, url),
# #             _run_visual_scan(client, url),
# #             _run_payment_scan(client, url),
# #             return_exceptions=True
# #         )

# #     url_result     = tasks[0] if not isinstance(tasks[0], Exception) else None
# #     visual_result  = tasks[1] if not isinstance(tasks[1], Exception) else None
# #     payment_result = tasks[2] if not isinstance(tasks[2], Exception) else None

# #     # extract scores
# #     url_score = (
# #         url_result.get("risk_score") or
# #         url_result.get("final_score") or
# #         0
# #     ) if url_result else None

# #     visual_score = None
# #     if visual_result and visual_result.get("available"):
# #         sim = visual_result.get("visual_similarity")
# #     if sim is not None and sim > 0:
# #         visual_score = sim
# #     # visual_score = (
# #     #     visual_result.get("visual_similarity") or 0
# #     # ) if visual_result else None

# #     payment_score = None
# #     if payment_result and payment_result.get("available"):
# #         payment_score = payment_result.get("payment_risk") or None
# #     if payment_score == 0:
# #         payment_score = None
# #     # payment_score = (
# #     #     payment_result.get("payment_risk") or 0
# #     # ) if payment_result else None

# #     overall_risk = calculate_overall_risk(url_score, visual_score, payment_score)
# #     verdict      = calculate_verdict(overall_risk)

# #     # decide explanation source
# #     payment_has_high_risk = (
# #         payment_result and
# #         payment_result.get("available") and
# #         payment_result.get("payment_risk", 0) >= 70
# #     )

# #     if payment_has_high_risk:
# #         # regenerate explanation with full combined context including payment signals
# #         from services.ai_explainer_service import generate_explanation

# #         combined_signals = {
# #             "url_signals":     url_result.get("signals", {}) if url_result else {},
# #             "payment_signals": payment_result.get("upi_signals", []),
# #             "payment_risk":    payment_result.get("payment_risk", 0),
# #             "url_risk":        url_score or 0,
# #             "overall_risk":    overall_risk
# #         }

# #         upgraded = generate_explanation(
# #             signals    = combined_signals,
# #             risk_score = overall_risk,
# #             url        = url
# #         )

# #         explanation             = upgraded.get("explanation")
# #         impersonation_statement = upgraded.get("impersonation_statement")
# #         attack_type             = upgraded.get("attack_type")

# #     else:
# #         # use explanation already generated by url_routes
# #         explanation             = url_result.get("explanation")             if url_result else None
# #         impersonation_statement = url_result.get("impersonation_statement") if url_result else None
# #         attack_type             = url_result.get("attack_type")             if url_result else None

# #     return {
# #         "url":                     url,
# #         "overall_risk":            overall_risk,
# #         "verdict":                 verdict,
# #         "url_scan":                url_result,
# #         "visual_scan":             visual_result or {
# #             "visual_similarity": None,
# #             "detected_brand":    None,
# #             "heatmap_url":       None,
# #             "risk":              None,
# #             "available":         False,
# #             "reason":            "Visual scan unavailable"
# #         },
# #         "payment_scan":            payment_result or {
# #             "payment_risk":        0,
# #             "reasons":             ["Payment scan unavailable"],
# #             "upi_signals":         [],
# #             "deep_scan_triggered": False,
# #             "deep_scan_note":      None,
# #             "available":           False
# #         },
# #         "explanation":             explanation,
# #         "impersonation_statement": impersonation_statement,
# #         "attack_type":             attack_type,
# #     }

# # ── internal helpers ──────────────────────────────────────────────────────────

# async def _run_url_scan(client: httpx.AsyncClient, url: str) -> dict:
#     try:
#         response = await client.post(
#             "http://localhost:8000/api/analyze-url",
#             json={"url": url},
#             timeout=20.0
#         )
#         response.raise_for_status()
#         return response.json()
#     except Exception as e:
#         print(f"URL scan failed: {e}")
#         return None

# async def _run_visual_scan(client: httpx.AsyncClient, url: str) -> dict:
#     try:
#         response = await client.post(
#             "http://localhost:8000/api/analyze-visual",
#             json={"url": url},
#             timeout=25.0
#         )
#         response.raise_for_status()
#         return response.json()
#     except Exception as e:
#         print(f"Visual scan failed: {e}")
#         return None

# async def _run_payment_scan(client: httpx.AsyncClient, url: str) -> dict:
#     try:
#         response = await client.post(
#             "http://localhost:8000/api/analyze-payment",
#             json={"url": url},
#             timeout=20.0
#         )
#         response.raise_for_status()
#         return response.json()
#     except Exception as e:
#         print(f"Payment scan failed: {e}")
#         return None
