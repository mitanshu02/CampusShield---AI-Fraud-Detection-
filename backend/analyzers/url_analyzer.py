# backend/analyzers/url_analyzer.py

import re
from rapidfuzz.distance import Levenshtein
from services.whois_service import get_whois_result
from services.phishtank_service import check_phishtank
from utils.domain_utils import extract_domain, extract_domain_base
from utils.scoring_utils import combine_url_scores, get_risk_label, get_risk_colour

# Known legitimate domains to compare against for typosquatting
KNOWN_DOMAINS = [
    "nitbhopal.ac.in", "iitbombay.ac.in", "iitdelhi.ac.in",
    "du.ac.in", "vtu.ac.in", "amity.edu",
    "sbi.co.in", "hdfcbank.com", "icicibank.com",
    "phonepe.com", "paytm.com", "npci.org.in",
    "google.com", "yahoo.com", "outlook.com"
]

KNOWN_DOMAIN_AGES = {
    "nitbhopal.ac.in":  5840,   # ~16 years
    "iitbombay.ac.in":  7300,   # ~20 years
    "iitdelhi.ac.in":   7300,   # ~20 years
    "du.ac.in":         8760,   # ~24 years
    "vtu.ac.in":        6570,   # ~18 years
    "amity.edu":        7300,   # ~20 years
    "sbi.co.in":        9125,   # ~25 years
    "hdfcbank.com":     9125,   # ~25 years
    "icicibank.com":    9125,   # ~25 years
    "phonepe.com":      3650,   # ~10 years
    "paytm.com":        5475,   # ~15 years
    "npci.org.in":      5475,   # ~15 years
    "google.com":       9855,   # ~27 years
    "yahoo.com":        10220,  # ~28 years
    "outlook.com":      7300,   # ~20 years
}

# Keywords that appear in phishing URLs
PHISHING_KEYWORDS = [
    "verify", "fees", "scholarship", "urgent", "confirm",
    "update", "login", "signin", "secure", "account",
    "pin", "otp", "reward", "cashback", "prize",
    "free", "claim", "refund", "payment", "pay"
]

def check_typosquatting(domain: str) -> dict:
    """
    Compares domain against known legitimate domains using Levenshtein distance.
    Uses strict 3-condition validation to prevent false positives.
    """
    from utils.domain_utils import is_valid_typosquat_match

    base = extract_domain_base(domain)

    closest_match = None
    closest_full_domain = None
    min_dist = 999

    for known in KNOWN_DOMAINS:
        known_base = extract_domain_base(known)
        dist = Levenshtein.distance(base, known_base)
        if dist < min_dist:
            min_dist = dist
            closest_match = known_base
            closest_full_domain = known

    # Exact match — this is the real domain
    if min_dist == 0:
        return {
            "score": 0,
            "detail": f"Exact match to known domain: {closest_full_domain}",
            "matched_domain": closest_full_domain,
            "distance": min_dist
        }

    # check all known domains for keyword embedding — not just closest by distance
    for known in KNOWN_DOMAINS:
        known_base = extract_domain_base(known)
        dist = Levenshtein.distance(extract_domain_base(domain), known_base)
        if is_valid_typosquat_match(domain, known, dist):
            return {
                "score": 95,
                "detail": f"Domain contains '{known_base}' — impersonating {known}",
                "matched_domain": known,
                "distance": dist
            }

    # No valid typosquatting match found
    return {
        "score": 0,
        "detail": "No typosquatting detected",
        "matched_domain": None,
        "distance": min_dist
    }
  


   
def check_keywords(url: str) -> dict:
    """
    Scans the full URL for phishing-related keywords.
    """
    url_lower = url.lower()
    found = [kw for kw in PHISHING_KEYWORDS if kw in url_lower]

    if len(found) >= 3:
        return {
            "score": 85,
            "detail": f"Multiple suspicious keywords found: {', '.join(found)}"
        }
    elif len(found) >= 1:
        return {
            "score": 40,
            "detail": f"Suspicious keywords detected: {', '.join(found)}"
        }
    else:
        return {
            "score": 5,
            "detail": "No suspicious keywords found in URL"
        }


def analyze_url(url: str) -> dict:
    """
    Main function — runs all 4 checks and returns combined result.
    Called by url_routes.py
    """
    domain = extract_domain(url)

    # Step 1 — typosquat check first so we get the legitimate domain
    typo_result = check_typosquatting(domain)
    legitimate_domain = typo_result.get("matched_domain")

    # Step 2 — WHOIS on suspicious domain + legitimate domain (Upgrade 1)
    # use known age fallback if legitimate domain WHOIS fails
    legitimate_domain_age_override = KNOWN_DOMAIN_AGES.get(legitimate_domain)
    whois_result = get_whois_result(domain, legitimate_domain)

    # if WHOIS returned null for legitimate domain, use our known age
    if (whois_result.get("legitimate_age_days") is None and
            legitimate_domain_age_override is not None):
        whois_result["legitimate_age_days"] = legitimate_domain_age_override

    # Step 3 — PhishTank check
    phishtank_result = check_phishtank(url)

    # Step 4 — Keyword scan
    keyword_result = check_keywords(url)

    # Step 5 — Combine scores
    if not phishtank_result.get("available", True):
        final_score = round(min(
            whois_result["score"]   * 0.35 +
            typo_result["score"]    * 0.45 +
            keyword_result["score"] * 0.20,
            100
        ))
    else:
        final_score = combine_url_scores(
            whois_score     = whois_result["score"],
            typosquat_score = typo_result["score"],
            phishtank_score = phishtank_result["score"],
            keyword_score   = keyword_result["score"]
    )

    return {
        "url": url,
        "domain": domain,
        "final_score": final_score,
        "risk_label": get_risk_label(final_score),
        "risk_colour": get_risk_colour(final_score),
        "signals": {
            "domain_age": {
                "name": "Domain Age",
                "weight": "25%",
                "score": whois_result["score"],
                "detail": whois_result["detail"],
                # Upgrade 1 — both ages for DomainTimeline.jsx
                "suspicious_domain": whois_result["suspicious_domain"],
                "suspicious_age_days": whois_result["suspicious_age_days"],
                "legitimate_domain": whois_result["legitimate_domain"],
                "legitimate_age_days": whois_result["legitimate_age_days"],
            },
            "typosquatting": {
                "name": "Typosquatting Check",
                "weight": "30%",
                "score": typo_result["score"],
                "detail": typo_result["detail"],
                "matched_domain": typo_result["matched_domain"],
                "distance": typo_result["distance"],
            },
            "phishtank": {
                "name": "PhishTank Lookup",
                "weight": "30%",
                "score": phishtank_result["score"],
                "detail": phishtank_result["detail"],
                "listed": phishtank_result["listed"],
                "available": phishtank_result.get("available", True),
            },
            "keywords": {
                "name": "Keyword Scan",
                "weight": "15%",
                "score": keyword_result["score"],
                "detail": keyword_result["detail"],
            }
        }
    }