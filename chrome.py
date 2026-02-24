from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os
import argparse

# ── Experiment constants ──────────────────────────────────────────────────────
DURATION = 30
WARMUP_TIME = 2
SCROLL_INTERVAL = 5

COLOR_SCHEME = "dark"
VIDEO_QUALITY = 1080  # 1080p

OUTPUT_DIR = "measurements"

URLS = {
    "tiktok": "https://www.tiktok.com/@realmadrid/video/7607975899702643990",
    "youtube": "https://youtube.com/shorts/7F9ppUhh9yo?si=tcRMpvMWj1b4SCEf",
    "instagram": "https://www.instagram.com/reels/DU4DND4CKiL/?igsh=MTMwMWczcXg4ejdmaA==",
    "facebook": "https://www.facebook.com/share/r/1CWfzQSNss/",
}

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
    # Close the puzzle slider popup
    try:
        close_puzzle = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Close']"))
        )
        close_puzzle.click()
        print("Puzzle popup closed.")
        time.sleep(1)
    except:
        pass

    # Close the GDPR "Got it" banner
    try:
        got_it = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'TUXButton--primary') and .//div[@class='TUXButton-label' and text()='Got it']]"))
        )
        got_it.click()
        print("GDPR banner closed.")
        time.sleep(1)
    except:
        pass
    
    # Close the cookie banner by clicking "Decline optional cookies" (inside shadow DOM)
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

def close_instagram_popups(driver):
    """Close Instagram-specific popups"""
    # Close login/signup dialog if it appears
    try:
        close_btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='dialog']//button[@aria-label='Close']"))
        )
        close_btn.click()
        print("Instagram dialog closed.")
        time.sleep(1)
    except:
        pass

    # Decline optional cookies
    try:
        decline = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Decline optional cookies')]"))
        )
        decline.click()
        print("Instagram cookies declined.")
        time.sleep(1)
    except:
        pass


def close_facebook_popups(driver):
    """Close Facebook-specific popups"""
    # Decline optional cookies using JavaScript
    try:
        decline_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Decline optional cookies']"))
        )
        decline_button.click()
        print("Cookies declined.")
    except:
        print("No cookie banner.")
    
    # Close the "See more on Facebook" login dialog
    try:
        close_btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Close']"))
        )
        close_btn.click()
        print("Facebook login dialog closed.")
        time.sleep(1)
    except:
        print("No login dialog found.")


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
        elif platform == "instagram":
            # Instagram unmute button - look for mute icon in top-right
            try:
                unmute_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//svg[@aria-label='Unmute']"))
                )
                unmute_button.click()
                print("Video unmuted.")
            except:
                # Try the button wrapper instead
                unmute_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button//svg[@aria-label='Unmute']"))
                )
                unmute_button.click()
                print("Video unmuted.")
        elif platform == "facebook":
            # Facebook unmute button - located in bottom-left area
            try:
                unmute_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Unmute']"))
                )
                unmute_button.click()
                print("Video unmuted.")
            except:
                print("Video already unmuted or button not found.")
    except:
        print("Video already unmuted or button not found.")

def run_experiment(platform):
    """Run the doomscrolling experiment"""
    driver = None

    try:
        driver = setup_chrome()
        
        url = URLS[platform]
        print(f"\nStarting experiment: CHROME + {platform.upper()}")
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
        elif platform == "instagram":
            close_instagram_popups(driver)
        elif platform == "facebook":
            close_facebook_popups(driver)
        
        time.sleep(1)
        
        # Unmute video
        unmute_video(driver, platform)
        time.sleep(1)
        
        print(f"Warming up for {WARMUP_TIME} s...")
        time.sleep(WARMUP_TIME)
        
        print("Ready. Starting measurement...")
        
        # ── Scroll every SCROLL_INTERVAL seconds for DURATION seconds ──────────────
        for i in range(DURATION // SCROLL_INTERVAL):
            time.sleep(SCROLL_INTERVAL)
            
            # Close any popups that appear during scrolling
            # if platform == "tiktok":
            #     close_tiktok_popups(driver)
            
            # Scroll to next video
            if platform == "tiktok":
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
            elif platform == "youtube":
                WebDriverWait(driver, 1).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Next video']"))
                ).click()
            elif platform == "instagram":
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ARROW_DOWN)
            elif platform == "facebook":
                # Facebook scrolls with arrow down or page down
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
            

            print(f"  → Scrolled at t={SCROLL_INTERVAL * (i + 1)} s")
        
        print("Measurement complete.")
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Energy measurement experiment for social media platforms")
    parser.add_argument("platform", choices=["tiktok", "youtube", "instagram", "facebook"], help="Platform to test")

    args = parser.parse_args()

    run_experiment(args.platform)