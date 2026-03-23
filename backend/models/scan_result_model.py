# backend/models/scan_result_model.py

from pydantic import BaseModel
from typing import Optional, List

# ── URL Analyzer Models ───────────────────────────────────────────────────────

class URLSignals(BaseModel):
    domain_age_days:              Optional[int]   = None
    legitimate_domain:            Optional[str]   = None
    legitimate_domain_age_years:  Optional[float] = None
    typosquatting_match:          Optional[str]   = None
    typosquatting_distance:       Optional[int]   = None
    phishtank_listed:             Optional[bool]  = False
    phishtank_available:          Optional[bool]  = True
    keywords_found:               Optional[List[str]] = []

class URLScanResponse(BaseModel):
    risk_score:             int
    reasons:                List[str]
    signals:                URLSignals
    explanation:            Optional[str] = None
    impersonation_statement:Optional[str] = None
    attack_type:            Optional[str] = None

# ── Visual Detector Models ────────────────────────────────────────────────────

class VisualScanResponse(BaseModel):
    visual_similarity:  Optional[int]  = None
    detected_brand:     Optional[str]  = None
    heatmap_url:        Optional[str]  = None
    risk:               Optional[str]  = None
    available:          bool           = True
    reason:             Optional[str]  = None

# ── Payment Analyzer Models ───────────────────────────────────────────────────

class UPISignal(BaseModel):
    signal:   str
    severity: str
    detail:   str

class PaymentScanResponse(BaseModel):
    payment_risk:       int
    reasons:            List[str]
    upi_signals:        List[UPISignal]   = []
    deep_scan_triggered:bool              = False
    deep_scan_note:     Optional[str]     = None
    available:          bool              = True

# ── Unified Full Scan Model ───────────────────────────────────────────────────

class FullScanResponse(BaseModel):
    url:                str
    overall_risk:       int
    verdict:            str
    url_scan:           Optional[URLScanResponse]     = None
    visual_scan:        Optional[VisualScanResponse]  = None
    payment_scan:       Optional[PaymentScanResponse] = None
    explanation:        Optional[str]  = None
    impersonation_statement: Optional[str] = None
    attack_type:        Optional[str]  = None

# ── Request Models ────────────────────────────────────────────────────────────

class ScanRequest(BaseModel):
    url: str