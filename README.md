## Setup

Clone this repository into the directory where you have cloned [EnergiBridge](https://github.com/tdurieux/EnergiBridge) from Github. The scripts shall only run when this project is run from a workspace that is inside the EnergiBridge project.

1. Clone the repo from Github.
2. Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # For linux
    # On Windows: venv\Scripts\activate
    ```
3. Install dependencies (Python 3.13):
    ```bash
    pip install -r requirements.txt
    ```
4. Run the experiment on Chrome:
    ```bash
    python chrome.py [platform]
    ```
    Where `[platform]` is one of:
    - `tiktok` — opens TikTok, closes popups/banners, unmutes, then scrolls every 10 s for 60 s
    - `youtube` — opens YouTube Shorts, declines cookies, unmutes, then clicks next video every 10 s for 60 s

    Examples:
    ```bash
    python chrome.py tiktok
    python chrome.py youtube
    ```

    Alternatively, run scripts using a singular controller:
    ```bash
        python run_experiment.py
    ```
    Running this script performs the following sequence:
    ```bash
        run_experiment.py
        ├── spawns setup.py  (background)
        │     navigate → cookies → unmute → warmup → writes .measurement_ready
        └── polls for .measurement_ready
            → launches energibridge wrapping measure.py  ← only this is measured
                    sleep(DURATION)
            → energibridge exits, CSV is written
            → setup.py cleans up and closes browser
    ```
    The setup.py and measure.py can be altered for various social media platforms and browsers.
