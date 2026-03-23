# backend/capture_templates.py

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from playwright.sync_api import sync_playwright

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(TEMPLATES_DIR, exist_ok=True)

def capture(url: str, filename: str):
    print(f"Capturing {url} → {filename}")
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
        page.add_init_script("""
            const style = document.createElement('style');
            style.textContent = `
                #cookie-banner, .cookie-banner, .cookie-notice,
                .chat-widget, .popup, [class*='cookie'],
                [class*='gdpr'] { display: none !important; }
            `;
            document.head.appendChild(style);
        """)
        try:
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
        except Exception as e:
            print(f"Warning: {e}")
            page.wait_for_timeout(1000)

        path = os.path.join(TEMPLATES_DIR, filename)
        page.screenshot(path=path, full_page=False)
        browser.close()
        print(f"Saved: {path}")

if __name__ == "__main__":
    # ── College templates ─────────────────────────────────────────────────────
    capture(
        "http://localhost:8080/fake_college_page.html",
        "college_real.png"
    )
    capture(
        "http://localhost:8080/fake_college_modified.html",
        "college_fake.png"
    )

    # ── Paytm templates ───────────────────────────────────────────────────────
    # real template = actual paytm.com
    capture(
        "https://paytm.com",
        "paytm_real.png"
    )

    # suspicious = our fake Paytm scholarship fraud page
    capture(
        "http://localhost:8080/scholarship-refund-paytm.html",
        "paytm_fake.png"
    )

    print("\nAll templates captured successfully.")
    print("College real:   college_real.png")
    print("College fake:   college_fake.png")
    print("Paytm real:     paytm_real.png")
    print("Paytm fake:     paytm_fake.png")
    
# # backend/capture_templates.py
# # run once: python capture_templates.py

# import os
# import sys
# sys.path.insert(0, os.path.dirname(__file__))

# from playwright.sync_api import sync_playwright

# TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
# os.makedirs(TEMPLATES_DIR, exist_ok=True)

# def capture(url: str, filename: str):
#     print(f"Capturing {url} → {filename}")
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=True)
#         context = browser.new_context(
#             viewport={"width": 1280, "height": 720},
#             user_agent=(
#                 "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#                 "AppleWebKit/537.36"
#             )
#         )
#         page = context.new_page()
#         page.add_init_script("""
#             const style = document.createElement('style');
#             style.textContent = `
#                 #cookie-banner, .cookie-banner, .cookie-notice,
#                 .chat-widget, .intercom-launcher, .popup,
#                 [class*='cookie'], [class*='gdpr'] {
#                     display: none !important;
#                 }
#             `;
#             document.head.appendChild(style);
#         """)
#         try:
#             page.goto(url, timeout=20000, wait_until="domcontentloaded")
#             page.wait_for_timeout(3000)
#         except Exception as e:
#             print(f"Warning: {e}")
#             page.wait_for_timeout(1000)

#         path = os.path.join(TEMPLATES_DIR, filename)
#         page.screenshot(path=path, full_page=False)
#         browser.close()
#         print(f"Saved: {path}")

# if __name__ == "__main__":
#     # real college page template
#     capture("https://www.skitm.in", "college_real.png")

#     # fake college page template — make sure fake page server is running:
#     # python -m http.server 8080 (from demo folder)
#     capture("http://localhost:8080/fake_college_page.html", "college_fake.png")

#     print("\nAll templates captured successfully.")
#     print("Templates saved to:", TEMPLATES_DIR)