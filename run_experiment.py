import subprocess
import os
import time

READY_SIGNAL = ".measurement_ready"
OUTPUT_FILE = "energy-experiments-P1/measurements/instagram_exp.csv"

# 1. Start setup in the background
setup = subprocess.Popen(["python", "energy-experiments-P1/chrome_instagram_setup.py"])

# 2. Wait for the ready signal
print("Waiting for browser setup...")
while not os.path.exists(READY_SIGNAL):
    time.sleep(0.5)

# 3. Immediately hand off to energibridge — this is the only measured window
print("Starting energy measurement...")
subprocess.run([
    "./target/release/energibridge",
    "--summary",
    "-o", OUTPUT_FILE,
    "--",
    "python", "energy-experiments-P1/chrome_instagram_measure.py"
])

# 4. Wait for setup to finish closing the browser
setup.wait()
print(f"Done. Results saved to {OUTPUT_FILE}")
