# backend/utils/domain_utils.py

import re
from rapidfuzz.distance import Levenshtein

def extract_domain(url: str) -> str:
    url = re.sub(r"https?://", "", url.strip())
    url = re.sub(r"^www\.", "", url)
    domain = url.split("/")[0].split("?")[0]
    return domain.lower()


def extract_domain_base(domain: str) -> str:
    parts = domain.split(".")
    return parts[0].lower()


def extract_tld(domain: str) -> str:
    parts = domain.split(".")
    if len(parts) >= 3:
        return ".".join(parts[-2:])
    elif len(parts) == 2:
        return parts[-1]
    return ""


def get_shared_keywords(domain1: str, domain2: str) -> list:
    words1 = set(re.split(r"[-.]", domain1.lower()))
    words2 = set(re.split(r"[-.]", domain2.lower()))
    shared = [w for w in words1 & words2 if len(w) >= 4]
    return shared


def extract_all_words(domain: str) -> list:
    """
    Splits domain into all meaningful words.
    fees-nitbhopal-edu.in → ['fees', 'nitbhopal', 'edu']
    """
    base = extract_domain_base(domain)
    words = re.split(r"[-_]", base.lower())
    return [w for w in words if len(w) >= 3]


def is_valid_typosquat_match(
    suspicious_domain: str,
    legitimate_domain: str,
    distance: int
) -> bool:
    """
    Detects typosquatting using THREE strategies:

    Strategy 1 — Classic: Levenshtein distance ≤ 2 on base names
    (catches: nitbhopa.ac.in vs nitbhopal.ac.in)

    Strategy 2 — Keyword embedding: suspicious domain CONTAINS
    the legitimate domain name as a word
    (catches: fees-nitbhopal-edu.in vs nitbhopal.ac.in)

    Strategy 3 — Substring: legitimate base is a substring of
    suspicious base
    (catches: nitbhopal-fees.in vs nitbhopal.ac.in)
    """
    sus_base = extract_domain_base(suspicious_domain)
    leg_base = extract_domain_base(legitimate_domain)

    # Strategy 1 — classic Levenshtein on base names
    if distance <= 2 and sus_base != leg_base:
        sus_tld = extract_tld(suspicious_domain)
        leg_tld = extract_tld(legitimate_domain)
        indian_tlds = {"ac.in", "co.in", "in", "edu.in", "org.in"}
        both_indian = sus_tld in indian_tlds and leg_tld in indian_tlds
        same_tld    = sus_tld == leg_tld
        if both_indian or same_tld:
            return True

    # Strategy 2 — keyword embedding
    # check if legitimate base appears as a word in suspicious domain
    sus_words = extract_all_words(suspicious_domain)
    if leg_base in sus_words:
        return True

    # also check if any word in suspicious domain closely matches leg_base
    for word in sus_words:
        if len(word) >= 4 and Levenshtein.distance(word, leg_base) <= 1:
            return True

    # Strategy 3 — substring containment
    if leg_base in sus_base and len(leg_base) >= 4:
        return True

    return False
