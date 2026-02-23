from playwright.sync_api import sync_playwright
import time
import os

DURATION = 10  # seconds
URL = "https://www.instagram.com/reels/DVEG4s9CLSX/" # example reel URL to start doomscrolling
# URL1 = "https://www.instagram.com/reels/"
AUTH_FILE = "auth_state.json"
OUTPUT_DIR = "measurements"

# def save_auth_state(browser, context, auth_file):
#     """Save authentication state for reuse"""
#     context.storage_state(path=auth_file)

# def load_auth_state(browser, auth_file):
#     """Load saved authentication state if it exists"""
#     if os.path.exists(auth_file):
#         return browser.new_context(storage_state=auth_file)
#     return browser.new_context()

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=["--disable-extensions"])
    
    # context = load_auth_state(browser, AUTH_FILE)
    context = browser.new_context()
    page = context.new_page()
    
    page.goto(URL, wait_until="networkidle")
    
    # if "login" in page.url.lower():
    #     print("Not authenticated. Please log in manually, then press Enter...")
    #     input()
    #     save_auth_state(browser, context, AUTH_FILE)

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
    time.sleep(5)
    
    print(f"Measuring energy for {DURATION} seconds...")
    time.sleep(DURATION)
    
    browser.close()