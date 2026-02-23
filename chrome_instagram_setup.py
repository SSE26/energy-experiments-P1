from playwright.sync_api import sync_playwright
import time
import os

# ── Experiment constants ──────────────────────────────────────────────────────
DURATION = 60           # must match chrome_measure.py
WARMUP_TIME = 5
SCROLL_INTERVAL = 10    # seconds spent on each reel before scrolling to the next

DEVICE_SCALE_FACTOR = 1

LOCALE = "en-US"
TIMEZONE = "Europe/Amsterdam"
COLOR_SCHEME = "dark"

URL = "https://www.instagram.com/reels/DVEG4s9CLSX/"
OUTPUT_DIR = "SSE_P1/measurements"

READY_SIGNAL = ".measurement_ready"  # flag file watched by chrome_measure.py

# Remove any stale signal from a previous crashed run
if os.path.exists(READY_SIGNAL):
    os.remove(READY_SIGNAL)

os.makedirs(OUTPUT_DIR, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=[
            "--disable-extensions",
        ],
    )

    context = browser.new_context(
        viewport=None,  # matches actual screen resolution in fullscreen
        device_scale_factor=DEVICE_SCALE_FACTOR,
        locale=LOCALE,
        timezone_id=TIMEZONE,
        color_scheme=COLOR_SCHEME,
    )
    page = context.new_page()

    print("Navigating...")
    page.goto(URL, wait_until="networkidle")
    page.keyboard.press("F11")  # enter fullscreen

    # Decline cookies — longer timeout so the banner has time to appear
    try:
        page.click("button:has-text('Decline')", timeout=5000)
        print("Cookie banner declined.")
        time.sleep(1)  # let the banner animate away
    except:
        print("No cookie banner, continuing.")

    # Unmute video
    try:
        page.click("div[role='button'][tabindex='0'] svg[aria-label*='ute']", timeout=3000)
        print("Video unmuted.")
    except:
        print("Unmute button not found, continuing.")

    print(f"Warming up for {WARMUP_TIME} s...")
    time.sleep(WARMUP_TIME)

    # ── Write signal: setup is done, browser is in steady state ──────────────
    open(READY_SIGNAL, "w").close()
    print("Ready. Doomscrolling starting now...")

    # Scroll every SCROLL_INTERVAL seconds for DURATION seconds
    for i in range(DURATION // SCROLL_INTERVAL):
        time.sleep(SCROLL_INTERVAL)

        # Dismiss login popup if it appears
        try:
            page.click("svg[aria-label='Close']", timeout=500)
            print("  ✕ Login popup dismissed.")
        except:
            pass

        page.keyboard.press("ArrowDown")
        print(f"  → Reel {i + 2} at t={SCROLL_INTERVAL * (i + 1)} s")

    os.remove(READY_SIGNAL)
    browser.close()
    print("Browser closed. Experiment complete.")

