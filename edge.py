from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options

def create_edge_driver(
    headless=False,
    maximize=True,
    disable_notifications=True,
    disable_popups=True,
    disable_images=False,
    private_mode=False,
    custom_download_path=None,
    adblock_extension_path=None,
    edgedriver_path="/usr/local/bin/msedgedriver",  # adjust path if needed
):
    options = Options()

    # ── Headless mode ──────────────────────────────────────────────────
    if headless:
        options.add_argument("--headless")

    # ── Private / InPrivate mode ───────────────────────────────────────
    if private_mode:
        options.add_argument("--inprivate")

    # ── Disable notifications ──────────────────────────────────────────
    if disable_notifications:
        options.add_argument("--disable-notifications")

    # ── Disable popups ─────────────────────────────────────────────────
    if disable_popups:
        options.add_argument("--disable-popup-blocking")

    # ── Disable images ─────────────────────────────────────────────────
    if disable_images:
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)

    # ── Disable password manager prompt ───────────────────────────────
    options.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    })

    # ── Disable geolocation ────────────────────────────────────────────
    options.add_argument("--disable-geolocation")

    # ── Suppress automation info bar ───────────────────────────────────
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # ── Custom download path ───────────────────────────────────────────
    if custom_download_path:
        prefs = {
            "download.default_directory": custom_download_path,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
        }
        options.add_experimental_option("prefs", prefs)

    # ── Ad blocker extension ───────────────────────────────────────────
    # Edge supports Chrome extensions (.crx files)
    # Download uBlock Origin .crx from:
    # https://github.com/gorhill/uBlock/releases
    if adblock_extension_path:
        options.add_extension(adblock_extension_path)

    # ── Initialize Edge driver ─────────────────────────────────────────
    service = Service(edgedriver_path)
    driver = webdriver.Edge(service=service, options=options)

    # ── Maximize window ────────────────────────────────────────────────
    if maximize:
        driver.maximize_window()

    return driver


# ── Example usage ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    driver = create_edge_driver(
        headless=False,
        maximize=True,
        disable_notifications=True,
        disable_popups=True,
        disable_images=False,
        private_mode=False,
        custom_download_path=None,
        adblock_extension_path=None,
        edgedriver_path="/usr/local/bin/msedgedriver",  # adjust if needed
    )

    try:
        driver.get("https://www.tiktok.com/@realmadrid/video/7607975899702643990")
        print(f"Title:   {driver.title}")
        print(f"URL:     {driver.current_url}")
        input("Press Enter to close the browser...")
    finally:
        driver.quit()