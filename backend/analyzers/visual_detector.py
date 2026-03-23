# backend/analyzers/visual_detector.py

import os
import uuid
import imagehash
from PIL import Image
from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor
from utils.image_utils import (
    bytes_to_cv2, resize_to_standard,
    generate_heatmap, save_image, save_screenshot
)

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")
_executor     = ThreadPoolExecutor(max_workers=2)

# ── known brand templates ─────────────────────────────────────────────────────

BRAND_TEMPLATES = {
    "college": "college_real.png",
    "paytm":   "paytm_real.png",
}

SIMILARITY_THRESHOLD = 30

# ── screenshot capture ────────────────────────────────────────────────────────

def capture_screenshot(url: str) -> bytes | None:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )
            page = context.new_page()

            # hide dynamic elements before screenshotting
            page.add_init_script("""
                const style = document.createElement('style');
                style.textContent = `
                    #cookie-banner, .cookie-banner, .cookie-notice,
                    .chat-widget, .intercom-launcher, #intercom-container,
                    .popup, .modal-overlay, [class*="cookie"],
                    [class*="gdpr"], [id*="cookie"], [class*="chat-btn"],
                    .notification-bar, .alert-bar { display: none !important; }
                `;
                document.head.appendChild(style);
            """)

            try:
                page.goto(url, timeout=15000, wait_until="domcontentloaded")
                page.wait_for_timeout(2000)
            except Exception:
                page.wait_for_timeout(1000)

            screenshot_bytes = page.screenshot(full_page=False)
            browser.close()
            return screenshot_bytes

    except Exception as e:
        print(f"Screenshot capture failed: {e}")
        return None

# ── similarity comparison ─────────────────────────────────────────────────────

def compute_similarity(suspicious_bytes: bytes, template_path: str) -> int:
    try:
        from io import BytesIO
        suspicious_img = Image.open(BytesIO(suspicious_bytes)).convert("RGB")
        suspicious_img = suspicious_img.resize((1280, 720))

        template_img = Image.open(template_path).convert("RGB")
        template_img = template_img.resize((1280, 720))

        hash1 = imagehash.phash(suspicious_img, hash_size=16)
        hash2 = imagehash.phash(template_img,   hash_size=16)

        max_diff   = 16 * 16
        diff       = hash1 - hash2
        similarity = round((1 - diff / max_diff) * 100)
        return max(0, min(100, similarity))

    except Exception as e:
        print(f"Similarity computation failed: {e}")
        return 0

# ── main detector ─────────────────────────────────────────────────────────────

def run_visual_detector(url: str) -> dict:
    # capture screenshot of suspicious URL
    screenshot_bytes = capture_screenshot(url)

    if screenshot_bytes is None:
        return _unavailable("Could not capture screenshot of URL")

    # save suspicious screenshot for display
    sus_filename = f"suspicious_{uuid.uuid4().hex[:8]}.png"
    sus_cv2      = bytes_to_cv2(screenshot_bytes)
    sus_url      = save_screenshot(sus_cv2, sus_filename)

    # compare against all templates
    best_match      = None
    best_similarity = 0
    best_template   = None

    for brand, template_file in BRAND_TEMPLATES.items():
        template_path = os.path.join(TEMPLATES_DIR, template_file)

        if not os.path.exists(template_path):
            continue

        similarity = compute_similarity(screenshot_bytes, template_path)
        print(f"Similarity to {brand}: {similarity}%")

        if similarity > best_similarity:
            best_similarity = similarity
            best_match      = brand
            best_template   = template_path

    # no template matched above threshold
    if best_similarity < SIMILARITY_THRESHOLD or best_template is None:
        return {
            "visual_similarity": best_similarity,
            "detected_brand":    None,
            "heatmap_url":       sus_url,
            "risk":              "no visual match found",
            "available":         True,
            "reason":            f"No brand similarity above {SIMILARITY_THRESHOLD}%"
        }

    # generate OpenCV heatmap
    try:
        template_cv2 = bytes_to_cv2(
            open(best_template, "rb").read()
        )
        heatmap_cv2, diff_pct = generate_heatmap(sus_cv2, template_cv2)
        heatmap_url           = save_image(heatmap_cv2)

        # also save template screenshot for side-by-side display
        template_display_url = save_screenshot(
            resize_to_standard(template_cv2),
            f"template_{best_match}.png"
        )

        risk = (
            "high — likely impersonation" if best_similarity >= 80 else
            "medium — possible impersonation" if best_similarity >= 65 else
            "low — minor similarity"
        )

        return {
            "visual_similarity":   best_similarity,
            "detected_brand":      best_match,
            "heatmap_url":         heatmap_url,
            "suspicious_url":      sus_url,
            "template_url":        template_display_url,
            "diff_percentage":     round(diff_pct, 1),
            "risk":                risk,
            "available":           True,
            "reason":              None
        }

    except Exception as e:
        return _unavailable(f"Heatmap generation failed: {str(e)}")


def _unavailable(reason: str) -> dict:
    return {
        "visual_similarity": None,
        "detected_brand":    None,
        "heatmap_url":       None,
        "risk":              None,
        "available":         False,
        "reason":            reason
    }