# backend/config.py

import os
from dotenv import load_dotenv

load_dotenv()

# AI keys
GEMINI_API_KEY           = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY             = os.getenv("GROQ_API_KEY", "")

# external API keys
PHISHTANK_API_KEY        = os.getenv("PHISHTANK_API_KEY", "")
GOOGLE_SAFE_BROWSING_KEY = os.getenv("GOOGLE_SAFE_BROWSING_KEY", "")

# app settings
BACKEND_URL  = os.getenv("BACKEND_URL",  "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# risk score thresholds
RISK_HIGH   = 70
RISK_MEDIUM = 40

# typosquatting settings
TYPOSQUAT_MAX_DISTANCE    = 2
TYPOSQUAT_MIN_KEYWORD_LEN = 4

# domain age settings
DOMAIN_AGE_SUSPICIOUS_DAYS = 30



