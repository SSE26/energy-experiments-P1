from playwright.sync_api import sync_playwright
import time

URL = "https://storage.googleapis.com/tfjs-models/demos/body-pix/index.html"

with sync_playwright() as p:
    browser = p.firefox.launch(headless=False)
    page = browser.new_page()
    page.goto(URL, wait_until="networkidle")
    time.sleep(30)
    browser.close()
