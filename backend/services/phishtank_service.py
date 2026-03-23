# backend/services/phishtank_service.py

import requests

PHISHTANK_URL = "https://checkurl.phishtank.com/checkurl/"

def check_phishtank(url: str) -> dict:
    try:
        response = requests.post(
            PHISHTANK_URL,
            data={"url": url, "format": "json"},
            headers={"User-Agent": "CampusShield/1.0"},
            timeout=5
        )

        # Guard against empty or non-JSON response
        if not response.content or not response.text.strip():
            raise ValueError("Empty response")

        data = response.json()
        results = data.get("results", {})

        if results.get("in_database") and results.get("valid"):
            return {
                "score": 100,
                "detail": "URL is listed in PhishTank as a confirmed phishing site",
                "listed": True,
                "available": True
            }
        return {
            "score": 0,
            "detail": "URL not found in PhishTank database",
            "listed": False,
            "available": True
        }

    except Exception:
        return {
            "score": 0,
            "detail": "PhishTank check unavailable — skipped",
            "listed": False,
            "available": False
        }