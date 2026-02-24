## Setup

Clone this repository into the directory where you have cloned [EnergiBridge](https://github.com/tdurieux/EnergiBridge) from Github. The scripts shall only run when this project is run from a workspace that is inside the EnergiBridge project.

1. Clone the repo from Github.
2. Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # For linux
    # On Windows: venv\Scripts\activate
    ```
3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4. Run the experiment from inside the energibridge repository. This means, you'd need to explictly mention the relative path of the `run_experiment.py` file. This file contains back to back experimental run of Tiktok and Youtube Shorts.
    ```bash
    python SSE_P1/run_experiment.py
    ```

    Alternatively, to run a single platform manually:
    ```bash
        python chrome_setup.py tiktok &
        python chrome_measure.py
    ```
    Or, with energibridge directly:
    ```bash
        ./target/release/energibridge --summary -o SSE_P1/measurements/chrome_tiktok.csv -- python chrome_setup.py tiktok & sleep 2 && python chrome_measure.py
    ```
    
## Flowchart of script

Running this script performs the following sequence:

```bash
    run_experiments.py
    ├── for each PLATFORM in ["tiktok", "youtube"]:
    │
    ├─── spawns chrome_setup.py (background process)
    │    │
    │    └─── Setup Phase (NOT MEASURED)
    │         ├── Navigate to URL
    │         ├── Enter fullscreen
    │         ├── Close platform-specific popups
    │         │   ├── TikTok: close puzzle, GDPR, cookie banner
    │         │   └── YouTube: close cookie banner
    │         ├── Unmute video
    │         ├── Warmup for WARMUP_TIME seconds
    │         └── Write .measurement_ready flag file
    │             └── Doomscroll loop:
    │                 ├── sleep(SCROLL_INTERVAL)
    │                 ├── Send PAGE_DOWN / Next button click
    │                 └── repeat DURATION // SCROLL_INTERVAL times
    │
    ├─── polls for .measurement_ready file
    │    └── blocks until setup signals ready (timeout: 120s)
    │
    ├─── launches energibridge wrapping chrome_measure.py
    │    │
    │    └─── Measurement Phase (ONLY THIS IS MEASURED BY ENERGIBRIDGE)
    │         ├── Poll for .measurement_ready
    │         ├── Once found, start timer
    │         └── sleep(DURATION) seconds
    │             └── energibridge records all energy metrics during this window
    │
    ├─── energibridge exits
    │    └── CSV results written to measurements/chrome_{platform}.csv
    │
    └─── chrome_setup.py finishes
        ├── Removes .measurement_ready flag
        ├── Closes browser
        └── Process exits

    Output:
    └─── measurements/
        ├── chrome_tiktok.csv
        └── chrome_youtube.csv
```
### Key Points
1. Setup is NOT measured: all the browser setup, popups, unmuting happens outside the energy measurement window.
2. Only the sleep(DURATION) in `chrome_measure.py` is measured - this is the "doomscrolling" window that energibridge captures.
3. Synchronization - the `.measurement_ready` flag ensures measurement starts only after browser is fully ready.
4. Cleanup - setup.py continues scrolling during measurement and cleans up after.

This ensures clean, consistent energy measurements for just the doomscrolling behaviour.