from playwright.sync_api import sync_playwright
import time

DURATION = 10  # seconds
URL = "https://music.youtube.com/watch?v=GJY8OMJXRAk&list=RDAMVMGJY8OMJXRAk"

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=["--disable-extensions"]
    )

    context = browser.new_context()
    page = context.new_page()

    page.goto(URL, wait_until="networkidle")

    print("Log in manually if needed. Start playback.")
    time.sleep(15)  # give time to log in and press play

    print(f"Measuring playback for {DURATION} seconds...")
    time.sleep(DURATION)

    browser.close()
