# backend/services/whois_service.py

import whois
from datetime import datetime, timezone


def get_domain_age_days(domain: str) -> int | None:
    """
    Looks up domain registration date via WHOIS.
    Returns age in days, or None if lookup fails.
    """
    try:
        w = whois.whois(domain)
        creation = w.creation_date

        # Some WHOIS responses return a list of dates — take the first
        if isinstance(creation, list):
            creation = creation[0]

        if creation is None:
            return None

        # Handle timezone-aware vs timezone-naive datetime
        if creation.tzinfo is not None:
            now = datetime.now(timezone.utc)
        else:
            now = datetime.now()

        return (now - creation).days

    except Exception:
        return None


def score_from_age(age_days: int | None) -> int:
    """
    Converts domain age in days to a risk score (0-100).
    Newer domain = higher risk.
    """
    if age_days is None:
        return 75  # unknown age = moderate risk

    if age_days < 30:
        return 90  # very new = very suspicious
    elif age_days < 180:
        return 40  # fairly new = moderate suspicion
    else:
        return 5   # established domain = safe


def get_whois_result(suspicious_domain: str, legitimate_domain: str = None) -> dict:
    """
    Main function called by url_analyzer.py.
    
    Returns age and score for the suspicious domain.
    If a legitimate domain is provided (from typosquat match),
    also returns its age for the Upgrade 1 visual timeline.
    """
    sus_age = get_domain_age_days(suspicious_domain)
    score   = score_from_age(sus_age)

    result = {
        "score": score,
        "suspicious_domain": suspicious_domain,
        "suspicious_age_days": sus_age,
        "detail": _age_detail(suspicious_domain, sus_age),
        # Upgrade 1 fields — None if no legitimate domain provided
        "legitimate_domain": legitimate_domain,
        "legitimate_age_days": None,
    }

    # Upgrade 1 — also look up the legitimate domain age
    if legitimate_domain:
        result["legitimate_age_days"] = get_domain_age_days(legitimate_domain)

    return result


def _age_detail(domain: str, age_days: int | None) -> str:
    """Builds the human-readable detail string for the signal card."""
    if age_days is None:
        return f"Domain age unknown — could not retrieve WHOIS record"
    if age_days < 30:
        return f"Domain is only {age_days} days old — very new, high risk"
    if age_days < 180:
        return f"Domain is {age_days} days old — relatively new"
    return f"Domain is {age_days} days old — established"
