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
4. Run scripts using a singular controller:
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