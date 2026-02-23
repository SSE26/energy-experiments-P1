from playwright.sync_api import sync_playwright
import time

DURATION = 10

with sync_playwright() as p:
    browser = p.firefox.launch(
        headless=False,
        args=["--disable-extensions"]
    )

    context = browser.new_context()
    page = context.new_page()

    page.goto("https://google.com", wait_until="networkidle")

    print(f"Idle browser for {DURATION} seconds...")
    time.sleep(DURATION)

    browser.close()
