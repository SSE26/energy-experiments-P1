from playwright.sync_api import sync_playwright
import time
import os

DURATION = 10           # seconds of energy measurement
WARMUP_TIME = 5         # seconds to let the page settle before measuring

WINDOW_WIDTH = 1280     # browser window width in pixels
WINDOW_HEIGHT = 720     # browser window height in pixels
DEVICE_SCALE_FACTOR = 1 # pixel ratio (1 = no HiDPI scaling); affects GPU rendering load

LOCALE = "en-US"        # browser locale (affects served content / UI language)
TIMEZONE = "Europe/Amsterdam"  # timezone (affects content and timestamps)
COLOR_SCHEME = "dark"  # "light" or "dark"; dark mode can reduce energy on OLED

URL = "https://www.instagram.com/reels/DVEG4s9CLSX/" # example reel URL to start doomscrolling
# URL1 = "https://www.instagram.com/reels/"
AUTH_FILE = "auth_state.json"
OUTPUT_DIR = "measurements"

def save_auth_state(browser, context, auth_file):
    """Save authentication state for reuse"""
    context.storage_state(path=auth_file)

def load_auth_state(browser, auth_file):
    """Load saved authentication state if it exists"""
    if os.path.exists(auth_file):
        return browser.new_context(storage_state=auth_file)
    return browser.new_context()

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=[
            "--disable-extensions",
            f"--window-size={WINDOW_WIDTH},{WINDOW_HEIGHT}",
        ],
    )

    context = browser.new_context(
        viewport={"width": WINDOW_WIDTH, "height": WINDOW_HEIGHT},
        device_scale_factor=DEVICE_SCALE_FACTOR,
        locale=LOCALE,
        timezone_id=TIMEZONE,
        color_scheme=COLOR_SCHEME,
    )
    page = context.new_page()

    page.goto(URL, wait_until="networkidle")

    # Decline cookies if cookie banner appears
    try:
        page.click("button:has-text('Decline')", timeout=1000)
    except:
        pass

    # Unmute video - click the speaker icon in top-right corner
    try:
        page.click("div[role='button'][tabindex='0'] svg[aria-label*='ute']", timeout=1000)
    except:
        pass

    print("Waiting for video to play...")
    time.sleep(WARMUP_TIME)
    
    print(f"Measuring energy for {DURATION} seconds...")
    time.sleep(DURATION)
    
    browser.close()