# backend/analyzers/payment_analyzer.py

import re
import sys
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from services.whois_service import get_domain_age_days

# ── local helper ──────────────────────────────────────────────────────────────

def extract_domain(url: str) -> str:
    url = url.replace("https://", "").replace("http://", "")
    url = url.split("/")[0]
    url = url.split("?")[0]
    url = url.split("#")[0]
    return url.lower().strip()

# ── known safe domains — skip Playwright for these ───────────────────────────

KNOWN_SAFE_DOMAINS = [
    "google.com", "youtube.com", "yahoo.com", "outlook.com",
    "microsoft.com", "github.com", "stackoverflow.com",
    "nitbhopal.ac.in", "skitm.in", "iitbombay.ac.in",
    "iitdelhi.ac.in", "iitk.ac.in", "iitm.ac.in",
    "du.ac.in", "vtu.ac.in", "amity.edu",
    "sbi.co.in", "hdfcbank.com", "icicibank.com",
    "axisbank.com", "kotak.com", "pnbindia.in",
    "npci.org.in", "upi.org.in",
    "irctc.co.in", "indianrailways.gov.in",
    "uidai.gov.in", "incometax.gov.in", "mca.gov.in",
]

def is_known_safe(url: str) -> bool:
    domain = extract_domain(url)
    for safe in KNOWN_SAFE_DOMAINS:
        if domain == safe or domain.endswith("." + safe):
            return True
    return False

def is_suspicious_url(url: str) -> bool:
    """
    Quick pre-check before launching Playwright.
    Returns True if URL has any suspicious characteristics
    that warrant a full browser scan.
    """
    url_lower = url.lower()
    domain    = extract_domain(url)

    # always scan localhost demo pages
    if "localhost" in url or "127.0.0.1" in url:
        return True

    # suspicious keywords in URL path
    suspicious_path_keywords = [
        "pay", "payment", "fees", "fee", "upi", "collect",
        "refund", "cashback", "scholarship", "verify", "login",
        "signin", "secure", "account", "pin", "otp", "reward",
        "prize", "claim", "wallet", "recharge", "topup"
    ]
    path = url_lower.replace("https://", "").replace("http://", "")
    path = "/".join(path.split("/")[1:])  # strip domain, keep path
    if any(kw in path for kw in suspicious_path_keywords):
        return True

    # suspicious TLDs or domain patterns
    suspicious_patterns = [
        r"\d{4,}",           # long numbers in domain
        r"-edu\.",           # -edu. pattern
        r"-ac\.",            # -ac. pattern
        r"-gov\.",           # -gov. pattern
        r"\.xyz$",
        r"\.top$",
        r"\.club$",
        r"\.online$",
        r"\.site$",
        r"\.icu$",
    ]
    for pattern in suspicious_patterns:
        if re.search(pattern, domain):
            return True

    # hyphens in domain (common in phishing)
    if domain.count("-") >= 2:
        return True

    return False

# ── trusted payment gateways ──────────────────────────────────────────────────

TRUSTED_GATEWAYS = [
    "razorpay", "payu", "cashfree", "ccavenue",
    "paytm", "phonepe", "googlepay", "billdesk",
    "instamojo", "stripe", "paypal"
]

# ── suspicious UPI patterns ───────────────────────────────────────────────────

SUSPICIOUS_UPI_PATTERNS = [
    r"[a-z0-9]{8,}@ybl",
    r"[a-z0-9]{8,}@ibl",
    r"refund[._-]?[a-z0-9]*@",
    r"cashback[._-]?[a-z0-9]*@",
    r"prize[._-]?[a-z0-9]*@",
    r"lucky[._-]?[a-z0-9]*@",
    r"support[._-]?[a-z0-9]*@",
    r"help[._-]?[a-z0-9]*@",
]

# ── payment keywords ──────────────────────────────────────────────────────────

PAYMENT_KEYWORDS = [
    "pay now", "make payment", "complete payment",
    "enter card", "card number", "cvv", "expiry",
    "upi id", "upi pin", "mpin", "enter pin",
    "net banking", "wallet", "proceed to pay"
]

# ── collect fraud phrases ─────────────────────────────────────────────────────

COLLECT_FRAUD_PHRASES = [
    "collect request", "money request", "payment request",
    "refund initiated", "cashback pending", "prize money",
    "lottery", "winner", "congratulations", "claim now",
    "verify to receive", "accept payment", "claim your cashback"
]

# ── PIN harvest keywords ──────────────────────────────────────────────────────

PIN_KEYWORDS = [
    "upi pin", "mpin", "enter your pin",
    "re-enter pin", "confirm pin", "atm pin",
    "transaction pin", "verify pin",
    "enter upi pin", "upi pin to verify"
]

# ─────────────────────────────────────────────────────────────────────────────

def analyze_page_content(page_html: str, page_url: str) -> dict:
    soup      = BeautifulSoup(page_html, "html.parser")
    text      = soup.get_text(separator=" ").lower()
    full_html = page_html.lower()

    signals = []
    score   = 0

    # Signal 1 — PIN harvest detection
    pin_found = [kw for kw in PIN_KEYWORDS if kw in text]
    if pin_found:
        signals.append({
            "signal":   "UPI PIN requested on webpage",
            "severity": "HIGH",
            "detail":   f"Legitimate apps never ask for PIN on a webpage. Found: {', '.join(pin_found)}"
        })
        score += 40

    # Signal 2 — collect fraud language
    collect_found = [p for p in COLLECT_FRAUD_PHRASES if p in text]
    if collect_found:
        signals.append({
            "signal":   "Collect request fraud language detected",
            "severity": "HIGH",
            "detail":   f"Scammers disguise collect requests as refunds or prizes. Found: {', '.join(collect_found[:3])}"
        })
        score += 30

    # Signal 3 — suspicious UPI ID pattern
    upi_ids        = re.findall(r"[a-zA-Z0-9._-]+@[a-zA-Z]+", text)
    suspicious_upi = []
    for uid in upi_ids:
        for pattern in SUSPICIOUS_UPI_PATTERNS:
            if re.search(pattern, uid.lower()):
                suspicious_upi.append(uid)
                break
    if suspicious_upi:
        signals.append({
            "signal":   "Suspicious UPI ID pattern detected",
            "severity": "HIGH",
            "detail":   f"UPI ID matches known scam format: {', '.join(suspicious_upi[:2])}"
        })
        score += 25

    # Signal 4 — untrusted payment gateway
    gateway_found = any(gw in full_html for gw in TRUSTED_GATEWAYS)
    has_payment   = any(kw in text for kw in PAYMENT_KEYWORDS)
    if has_payment and not gateway_found:
        signals.append({
            "signal":   "Payment form on unrecognised gateway",
            "severity": "HIGH",
            "detail":   "Payment fields detected but no trusted gateway found (Razorpay, PayU, Cashfree etc.)"
        })
        score += 30

    # Signal 5 — domain age check
    domain   = extract_domain(page_url)
    age_days = get_domain_age_days(domain)
    if age_days is not None and age_days < 30:
        signals.append({
            "signal":   "Very new domain with payment page",
            "severity": "MEDIUM",
            "detail":   f"Domain '{domain}' is only {age_days} days old."
        })
        score += 20

    return {
        "score":   min(score, 100),
        "signals": signals,
        "url":     page_url
    }


def get_linked_urls(page, base_url: str) -> list:
    try:
        links = page.eval_on_selector_all(
            "a[href]",
            "elements => elements.map(el => el.href).filter(Boolean)"
        )
        base_domain = extract_domain(base_url)
        filtered    = []
        for link in links:
            if not link or link == base_url:
                continue
            if link.startswith("javascript:") or link.startswith("mailto:"):
                continue
            if link.startswith("#"):
                continue
            if base_domain in link:
                filtered.append(link)
        return filtered[:5]
    except Exception:
        return []


def run_payment_analyzer(url: str) -> dict:

    # ── Step 1 — skip known safe domains immediately ──────────────────────────
    if is_known_safe(url):
        return {
            "payment_risk":        0,
            "reasons":             ["Trusted domain — payment scan skipped"],
            "upi_signals":         [],
            "deep_scan_triggered": False,
            "deep_scan_note":      None,
            "available":           True
        }

    # ── Step 2 — skip Playwright if URL has no suspicious signals ─────────────
    if not is_suspicious_url(url):
        return {
            "payment_risk":        0,
            "reasons":             ["No suspicious URL patterns — payment scan skipped"],
            "upi_signals":         [],
            "deep_scan_triggered": False,
            "deep_scan_note":      None,
            "available":           True
        }

    # ── Step 3 — full Playwright scan for suspicious URLs ─────────────────────
    all_results         = []
    deep_scan_note      = None
    deep_scan_triggered = False

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36"
                )
            )
            page = context.new_page()

            # scan landing page
            try:
                page.goto(url, timeout=15000, wait_until="domcontentloaded")
                page.wait_for_timeout(2000)
                landing_html   = page.content()
                landing_result = analyze_page_content(landing_html, url)
                all_results.append(landing_result)
            except Exception as e:
                browser.close()
                return _unavailable_response(f"Could not load page: {str(e)}")

            # one level deep scan
            linked_urls = get_linked_urls(page, url)
            for linked_url in linked_urls[:5]:
                try:
                    linked_page = context.new_page()
                    linked_page.goto(
                        linked_url, timeout=10000,
                        wait_until="domcontentloaded"
                    )
                    linked_page.wait_for_timeout(1000)
                    linked_html   = linked_page.content()
                    linked_result = analyze_page_content(
                        linked_html, linked_url
                    )
                    all_results.append(linked_result)
                    linked_page.close()
                except Exception:
                    continue

            browser.close()

    except Exception as e:
        return _unavailable_response(f"Browser error: {str(e)}")

    if not all_results:
        return _unavailable_response("No pages could be analyzed")

    highest       = max(all_results, key=lambda r: r["score"])
    landing_score = all_results[0]["score"]

    if highest["score"] > landing_score and highest["url"] != url:
        deep_scan_triggered = True
        deep_scan_note      = (
            f"Danger found 1 click deep — safe landing page "
            f"concealing payment trap at: {highest['url']}"
        )

    all_signals = []
    seen        = set()
    for result in all_results:
        for sig in result["signals"]:
            key = sig["signal"]
            if key not in seen:
                seen.add(key)
                all_signals.append(sig)

    reasons = [s["detail"] for s in all_signals]

    return {
        "payment_risk":         highest["score"],
        "reasons":              reasons,
        "upi_signals":          all_signals,
        "deep_scan_triggered":  deep_scan_triggered,
        "deep_scan_note":       deep_scan_note,
        "available":            True
    }


def _unavailable_response(reason: str) -> dict:
    return {
        "payment_risk":         0,
        "reasons":              [reason],
        "upi_signals":          [],
        "deep_scan_triggered":  False,
        "deep_scan_note":       None,
        "available":            False
    }
# # backend/analyzers/payment_analyzer.py

# import re
# import sys
# from bs4 import BeautifulSoup
# from playwright.sync_api import sync_playwright
# from services.whois_service import get_domain_age_days

# # ── local helper ──────────────────────────────────────────────────────────────

# def extract_domain(url: str) -> str:
#     url = url.replace("https://", "").replace("http://", "")
#     url = url.split("/")[0]
#     url = url.split("?")[0]
#     url = url.split("#")[0]
#     return url.lower().strip()

# # ── trusted payment gateways ──────────────────────────────────────────────────

# TRUSTED_GATEWAYS = [
#     "razorpay", "payu", "cashfree", "ccavenue",
#     "paytm", "phonepe", "googlepay", "billdesk",
#     "instamojo", "stripe", "paypal"
# ]

# # ── suspicious UPI patterns ───────────────────────────────────────────────────

# SUSPICIOUS_UPI_PATTERNS = [
#     r"[a-z0-9]{8,}@ybl",
#     r"[a-z0-9]{8,}@ibl",
#     r"refund[._-]?[a-z0-9]*@",
#     r"cashback[._-]?[a-z0-9]*@",
#     r"prize[._-]?[a-z0-9]*@",
#     r"lucky[._-]?[a-z0-9]*@",
#     r"support[._-]?[a-z0-9]*@",
#     r"help[._-]?[a-z0-9]*@",
# ]

# # ── payment keywords ──────────────────────────────────────────────────────────

# PAYMENT_KEYWORDS = [
#     "pay now", "make payment", "complete payment",
#     "enter card", "card number", "cvv", "expiry",
#     "upi id", "upi pin", "mpin", "enter pin",
#     "net banking", "wallet", "proceed to pay"
# ]

# # ── collect fraud phrases ─────────────────────────────────────────────────────

# COLLECT_FRAUD_PHRASES = [
#     "collect request", "money request", "payment request",
#     "refund initiated", "cashback pending", "prize money",
#     "lottery", "winner", "congratulations", "claim now",
#     "verify to receive", "accept payment", "claim your cashback"
# ]

# # ── PIN harvest keywords ──────────────────────────────────────────────────────

# PIN_KEYWORDS = [
#     "upi pin", "mpin", "enter your pin",
#     "re-enter pin", "confirm pin", "atm pin",
#     "transaction pin", "verify pin",
#     "enter upi pin", "upi pin to verify"
# ]

# # ─────────────────────────────────────────────────────────────────────────────

# def analyze_page_content(page_html: str, page_url: str) -> dict:
#     soup      = BeautifulSoup(page_html, "html.parser")
#     text      = soup.get_text(separator=" ").lower()
#     full_html = page_html.lower()

#     signals = []
#     score   = 0

#     # Signal 1 — PIN harvest detection
#     pin_found = [kw for kw in PIN_KEYWORDS if kw in text]
#     if pin_found:
#         signals.append({
#             "signal":   "UPI PIN requested on webpage",
#             "severity": "HIGH",
#             "detail":   f"Legitimate apps never ask for PIN on a webpage. Found: {', '.join(pin_found)}"
#         })
#         score += 40

#     # Signal 2 — collect fraud language
#     collect_found = [p for p in COLLECT_FRAUD_PHRASES if p in text]
#     if collect_found:
#         signals.append({
#             "signal":   "Collect request fraud language detected",
#             "severity": "HIGH",
#             "detail":   f"Scammers disguise collect requests as refunds or prizes. Found: {', '.join(collect_found[:3])}"
#         })
#         score += 30

#     # Signal 3 — suspicious UPI ID pattern
#     upi_ids        = re.findall(r"[a-zA-Z0-9._-]+@[a-zA-Z]+", text)
#     suspicious_upi = []
#     for uid in upi_ids:
#         for pattern in SUSPICIOUS_UPI_PATTERNS:
#             if re.search(pattern, uid.lower()):
#                 suspicious_upi.append(uid)
#                 break
#     if suspicious_upi:
#         signals.append({
#             "signal":   "Suspicious UPI ID pattern detected",
#             "severity": "HIGH",
#             "detail":   f"UPI ID matches known scam format: {', '.join(suspicious_upi[:2])}"
#         })
#         score += 25

#     # Signal 4 — untrusted payment gateway
#     gateway_found = any(gw in full_html for gw in TRUSTED_GATEWAYS)
#     has_payment   = any(kw in text for kw in PAYMENT_KEYWORDS)
#     if has_payment and not gateway_found:
#         signals.append({
#             "signal":   "Payment form on unrecognised gateway",
#             "severity": "HIGH",
#             "detail":   "Payment fields detected but no trusted gateway found (Razorpay, PayU, Cashfree etc.)"
#         })
#         score += 30

#     # Signal 5 — domain age check
#     domain   = extract_domain(page_url)
#     age_days = get_domain_age_days(domain)
#     if age_days is not None and age_days < 30:
#         signals.append({
#             "signal":   "Very new domain with payment page",
#             "severity": "MEDIUM",
#             "detail":   f"Domain '{domain}' is only {age_days} days old."
#         })
#         score += 20

#     return {
#         "score":   min(score, 100),
#         "signals": signals,
#         "url":     page_url
#     }


# def get_linked_urls(page, base_url: str) -> list:
#     try:
#         links = page.eval_on_selector_all(
#             "a[href]",
#             "elements => elements.map(el => el.href).filter(Boolean)"
#         )
#         base_domain = extract_domain(base_url)
#         filtered    = []
#         for link in links:
#             if not link or link == base_url:
#                 continue
#             if link.startswith("javascript:") or link.startswith("mailto:"):
#                 continue
#             if link.startswith("#"):
#                 continue
#             if base_domain in link:
#                 filtered.append(link)
#         return filtered[:5]
#     except Exception:
#         return []


# def run_payment_analyzer(url: str) -> dict:
#     all_results         = []
#     deep_scan_note      = None
#     deep_scan_triggered = False

#     try:
#         with sync_playwright() as p:
#             browser = p.chromium.launch(headless=True)
#             context = browser.new_context(
#                 viewport={"width": 1280, "height": 720},
#                 user_agent=(
#                     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#                     "AppleWebKit/537.36"
#                 )
#             )
#             page = context.new_page()

#             # ── scan landing page ─────────────────────────────────────
#             try:
#                 page.goto(url, timeout=15000, wait_until="domcontentloaded")
#                 page.wait_for_timeout(2000)
#                 landing_html   = page.content()
#                 landing_result = analyze_page_content(landing_html, url)
#                 all_results.append(landing_result)
#             except Exception as e:
#                 browser.close()
#                 return _unavailable_response(f"Could not load page: {str(e)}")

#             # ── one level deep scan ───────────────────────────────────
#             linked_urls = get_linked_urls(page, url)

#             for linked_url in linked_urls[:5]:
#                 try:
#                     linked_page = context.new_page()
#                     linked_page.goto(
#                         linked_url, timeout=10000,
#                         wait_until="domcontentloaded"
#                     )
#                     linked_page.wait_for_timeout(1000)
#                     linked_html   = linked_page.content()
#                     linked_result = analyze_page_content(
#                         linked_html, linked_url
#                     )
#                     all_results.append(linked_result)
#                     linked_page.close()
#                 except Exception:
#                     continue

#             browser.close()

#     except Exception as e:
#         return _unavailable_response(f"Browser error: {str(e)}")

#     if not all_results:
#         return _unavailable_response("No pages could be analyzed")

#     highest       = max(all_results, key=lambda r: r["score"])
#     landing_score = all_results[0]["score"]

#     if highest["score"] > landing_score and highest["url"] != url:
#         deep_scan_triggered = True
#         deep_scan_note      = (
#             f"Danger found 1 click deep — safe landing page "
#             f"concealing payment trap at: {highest['url']}"
#         )

#     all_signals = []
#     seen        = set()
#     for result in all_results:
#         for sig in result["signals"]:
#             key = sig["signal"]
#             if key not in seen:
#                 seen.add(key)
#                 all_signals.append(sig)

#     reasons = [s["detail"] for s in all_signals]

#     return {
#         "payment_risk":         highest["score"],
#         "reasons":              reasons,
#         "upi_signals":          all_signals,
#         "deep_scan_triggered":  deep_scan_triggered,
#         "deep_scan_note":       deep_scan_note,
#         "available":            True
#     }


# def _unavailable_response(reason: str) -> dict:
#     return {
#         "payment_risk":         0,
#         "reasons":              [reason],
#         "upi_signals":          [],
#         "deep_scan_triggered":  False,
#         "deep_scan_note":       None,
#         "available":            False
#     }

# # backend/analyzers/payment_analyzer.py

# import re
# import asyncio
# from bs4 import BeautifulSoup
# from playwright.async_api import async_playwright
# from services.whois_service import get_domain_age_days

# # ── local helper ──────────────────────────────────────────────────────────────

# def extract_domain(url: str) -> str:
#     url = url.replace("https://", "").replace("http://", "")
#     url = url.split("/")[0]
#     url = url.split("?")[0]
#     url = url.split("#")[0]
#     return url.lower().strip()

# # ── trusted payment gateways ──────────────────────────────────────────────────

# TRUSTED_GATEWAYS = [
#     "razorpay", "payu", "cashfree", "ccavenue",
#     "paytm", "phonepe", "googlepay", "billdesk",
#     "instamojo", "stripe", "paypal"
# ]

# # ── suspicious UPI patterns ───────────────────────────────────────────────────

# SUSPICIOUS_UPI_PATTERNS = [
#     r"[a-z0-9]{8,}@ybl",
#     r"[a-z0-9]{8,}@ibl",
#     r"refund[._-]?[a-z0-9]*@",
#     r"cashback[._-]?[a-z0-9]*@",
#     r"prize[._-]?[a-z0-9]*@",
#     r"lucky[._-]?[a-z0-9]*@",
#     r"support[._-]?[a-z0-9]*@",
#     r"help[._-]?[a-z0-9]*@",
# ]

# # ── payment keywords ──────────────────────────────────────────────────────────

# PAYMENT_KEYWORDS = [
#     "pay now", "make payment", "complete payment",
#     "enter card", "card number", "cvv", "expiry",
#     "upi id", "upi pin", "mpin", "enter pin",
#     "net banking", "wallet", "proceed to pay"
# ]

# # ── collect fraud phrases ─────────────────────────────────────────────────────

# COLLECT_FRAUD_PHRASES = [
#     "collect request", "money request", "payment request",
#     "refund initiated", "cashback pending", "prize money",
#     "lottery", "winner", "congratulations", "claim now",
#     "verify to receive", "accept payment"
# ]

# # ── PIN harvest keywords ──────────────────────────────────────────────────────

# PIN_KEYWORDS = [
#     "upi pin", "mpin", "enter your pin",
#     "re-enter pin", "confirm pin", "atm pin",
#     "transaction pin", "verify pin"
# ]

# # ─────────────────────────────────────────────────────────────────────────────

# async def analyze_page_content(page_html: str, page_url: str) -> dict:
#     soup      = BeautifulSoup(page_html, "html.parser")
#     text      = soup.get_text(separator=" ").lower()
#     full_html = page_html.lower()

#     signals = []
#     score   = 0

#     # Signal 1 — PIN harvest detection (most dangerous)
#     pin_found = [kw for kw in PIN_KEYWORDS if kw in text]
#     if pin_found:
#         signals.append({
#             "signal":   "UPI PIN requested on webpage",
#             "severity": "HIGH",
#             "detail":   f"Legitimate apps never ask for PIN on a webpage. Found: {', '.join(pin_found)}"
#         })
#         score += 40

#     # Signal 2 — collect fraud language
#     collect_found = [p for p in COLLECT_FRAUD_PHRASES if p in text]
#     if collect_found:
#         signals.append({
#             "signal":   "Collect request fraud language detected",
#             "severity": "HIGH",
#             "detail":   f"Scammers disguise collect requests as refunds or prizes. Found: {', '.join(collect_found[:3])}"
#         })
#         score += 30

#     # Signal 3 — suspicious UPI ID pattern
#     upi_ids          = re.findall(r"[a-zA-Z0-9._-]+@[a-zA-Z]+", text)
#     suspicious_upi   = []
#     for uid in upi_ids:
#         for pattern in SUSPICIOUS_UPI_PATTERNS:
#             if re.search(pattern, uid.lower()):
#                 suspicious_upi.append(uid)
#                 break
#     if suspicious_upi:
#         signals.append({
#             "signal":   "Suspicious UPI ID pattern detected",
#             "severity": "HIGH",
#             "detail":   f"UPI ID matches known scam format: {', '.join(suspicious_upi[:2])}"
#         })
#         score += 25

#     # Signal 4 — untrusted payment gateway
#     gateway_found = any(gw in full_html for gw in TRUSTED_GATEWAYS)
#     has_payment   = any(kw in text for kw in PAYMENT_KEYWORDS)
#     if has_payment and not gateway_found:
#         signals.append({
#             "signal":   "Payment form on unrecognised gateway",
#             "severity": "HIGH",
#             "detail":   "Payment fields detected but no trusted gateway found (Razorpay, PayU, Cashfree etc.)"
#         })
#         score += 30

#     # Signal 5 — domain age check
#     domain   = extract_domain(page_url)
#     age_days = get_domain_age_days(domain)
#     if age_days is not None and age_days < 30:
#         signals.append({
#             "signal":   "Very new domain with payment page",
#             "severity": "MEDIUM",
#             "detail":   f"Domain '{domain}' is only {age_days} days old. Legitimate payment portals are established."
#         })
#         score += 20

#     return {
#         "score":   min(score, 100),
#         "signals": signals,
#         "url":     page_url
#     }


# async def get_linked_urls(page, base_url: str) -> list:
#     try:
#         links = await page.eval_on_selector_all(
#             "a[href], button[onclick], form[action]",
#             """elements => elements.map(el => {
#                 if (el.tagName === 'A') return el.href
#                 if (el.tagName === 'FORM') return el.action
#                 return null
#             }).filter(Boolean)"""
#         )
#         base_domain = extract_domain(base_url)
#         filtered    = []
#         for link in links:
#             if not link or link == base_url:
#                 continue
#             if link.startswith("javascript:") or link.startswith("mailto:"):
#                 continue
#             if link.startswith("#"):
#                 continue
#             if base_domain in link:
#                 filtered.append(link)
#         return filtered[:5]
#     except Exception:
#         return []


# async def run_payment_analyzer(url: str) -> dict:
#     all_results         = []
#     deep_scan_note      = None
#     deep_scan_triggered = False

#     try:
#         async with async_playwright() as p:
#             browser = await p.chromium.launch(headless=True)
#             context = await browser.new_context(
#                 viewport={"width": 1280, "height": 720},
#                 user_agent=(
#                     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#                     "AppleWebKit/537.36"
#                 )
#             )
#             page = await context.new_page()

#             # ── scan landing page ─────────────────────────────────────
#             try:
#                 await page.goto(
#                     url, timeout=15000,
#                     wait_until="domcontentloaded"
#                 )
#                 await page.wait_for_timeout(2000)
#                 landing_html   = await page.content()
#                 landing_result = await analyze_page_content(
#                     landing_html, url
#                 )
#                 all_results.append(landing_result)
#             except Exception as e:
#                 await browser.close()
#                 return _unavailable_response(
#                     f"Could not load page: {str(e)}"
#                 )

#             # ── one level deep scan ───────────────────────────────────
#             linked_urls = await get_linked_urls(page, url)

#             for linked_url in linked_urls[:5]:
#                 try:
#                     linked_page = await context.new_page()
#                     await linked_page.goto(
#                         linked_url, timeout=10000,
#                         wait_until="domcontentloaded"
#                     )
#                     await linked_page.wait_for_timeout(1000)
#                     linked_html   = await linked_page.content()
#                     linked_result = await analyze_page_content(
#                         linked_html, linked_url
#                     )
#                     all_results.append(linked_result)
#                     await linked_page.close()
#                 except Exception:
#                     continue

#             await browser.close()

#     except Exception as e:
#         return _unavailable_response(f"Browser error: {str(e)}")

#     if not all_results:
#         return _unavailable_response("No pages could be analyzed")

#     # find highest risk result across all pages
#     highest = max(all_results, key=lambda r: r["score"])

#     # check if danger found on linked page not landing page
#     landing_score = all_results[0]["score"]
#     if highest["score"] > landing_score and highest["url"] != url:
#         deep_scan_triggered = True
#         deep_scan_note      = (
#             f"Danger found 1 click deep — safe landing page "
#             f"concealing payment trap at: {highest['url']}"
#         )

#     # compile all unique signals across all pages
#     all_signals = []
#     seen        = set()
#     for result in all_results:
#         for sig in result["signals"]:
#             key = sig["signal"]
#             if key not in seen:
#                 seen.add(key)
#                 all_signals.append(sig)

#     reasons = [s["detail"] for s in all_signals]

#     return {
#         "payment_risk":         highest["score"],
#         "reasons":              reasons,
#         "upi_signals":          all_signals,
#         "deep_scan_triggered":  deep_scan_triggered,
#         "deep_scan_note":       deep_scan_note,
#         "available":            True
#     }


# def _unavailable_response(reason: str) -> dict:
#     return {
#         "payment_risk":         0,
#         "reasons":              [reason],
#         "upi_signals":          [],
#         "deep_scan_triggered":  False,
#         "deep_scan_note":       None,
#         "available":            False
#     }