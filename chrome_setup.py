from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os
import argparse

# ── Experiment constants ──────────────────────────────────────────────────────
DURATION = 30           # must match chrome_measure.py
WARMUP_TIME = 2
SCROLL_INTERVAL = 5     # seconds spent on each video before scrolling to the next

COLOR_SCHEME = "dark"
VIDEO_QUALITY = 1080

URLS = {
    "tiktok": "https://www.tiktok.com/@realmadrid/video/7607975899702643990",
    "youtube": "https://youtube.com/shorts/7F9ppUhh9yo?si=tcRMpvMWj1b4SCEf",
}

OUTPUT_DIR = "measurements"

# flag file watched by chrome_measure.py to know when to start measuring
READY_SIGNAL = ".measurement_ready"

# Remove any stale signal from a previous crashed run
if os.path.exists(READY_SIGNAL):
    os.remove(READY_SIGNAL)

os.makedirs(OUTPUT_DIR, exist_ok=True)

def setup_chrome():
    """Setup Chrome WebDriver"""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    return webdriver.Chrome(options=options)

def close_tiktok_popups(driver):
    """Close all TikTok-specific popups and banners"""
    try:
        close_puzzle = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Close']"))
        )
        close_puzzle.click()
        print("Puzzle popup closed.")
        time.sleep(1)
    except:
        pass

    try:
        got_it = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'TUXButton--primary') and .//div[@class='TUXButton-label' and text()='Got it']]"))
        )
        got_it.click()
        print("GDPR banner closed.")
        time.sleep(1)
    except:
        pass
    
    try:
        WebDriverWait(driver, 3).until(
            lambda d: d.execute_script(
                "return document.querySelector('tiktok-cookie-banner') !== null"
            )
        )
        driver.execute_script("""
            const banner = document.querySelector('tiktok-cookie-banner');
            const buttons = banner.shadowRoot.querySelectorAll('button');
            for (const btn of buttons) {
                if (btn.textContent.trim() === 'Decline optional cookies') {
                    btn.click();
                    break;
                }
            }
        """)
        print("Cookie banner declined.")
        time.sleep(1)
    except:
        pass

def unmute_video(driver, platform):
    """Unmute the video"""
    try:
        if platform == "tiktok":
            unmute_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Volume' and @aria-pressed='false']"))
            )
            unmute_button.click()
            print("Video unmuted.")
        elif platform == "youtube":
            unmute_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Unmute')]"))
            )
            unmute_button.click()
            print("Video unmuted.")
    except:
        print("Video already unmuted or button not found.")

def run_setup(platform):
    """Run the setup phase"""
    driver = None

    try:
        driver = setup_chrome()
        
        url = URLS[platform]
        print(f"\nStarting setup: CHROME + {platform.upper()}")
        print(f"URL: {url}")
        print("Navigating...")
        
        driver.get(url)
        time.sleep(4)
        
        # Enter fullscreen
        driver.execute_script("document.documentElement.requestFullscreen();")
        time.sleep(1)
        
        # Handle platform-specific popups
        if platform == "tiktok":
            close_tiktok_popups(driver)
        elif platform == "youtube":
            try:
                decline_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Reject')]"))
                )
                decline_button.click()
                print("Cookies declined.")
            except:
                print("No cookie banner.")
        
        time.sleep(1)
        
        # Unmute video
        unmute_video(driver, platform)
        time.sleep(1)
        
        print(f"Warming up for {WARMUP_TIME} s...")
        time.sleep(WARMUP_TIME)
        
        # ── Write signal: setup is done, browser is in steady state ──────────────
        open(READY_SIGNAL, "w").close()
        print("Ready. Doomscrolling starting now...")
        
        # Scroll every SCROLL_INTERVAL seconds for DURATION seconds
        for i in range(DURATION // SCROLL_INTERVAL):
            time.sleep(SCROLL_INTERVAL)
            
            # Scroll to next video
            if platform == "tiktok":
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
            elif platform == "youtube":
                try:
                    WebDriverWait(driver, 1).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Next video']"))
                    ).click()
                except:
                    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
            
            print(f"  → Video {i + 2} at t={SCROLL_INTERVAL * (i + 1)} s")
        
        os.remove(READY_SIGNAL)
        print("Setup complete.")
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup phase for energy measurement experiment")
    parser.add_argument("platform", choices=["tiktok", "youtube"], help="Platform to test")

    args = parser.parse_args()

    run_setup(args.platform)