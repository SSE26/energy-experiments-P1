import subprocess
import os
import time

# ── Experiment hyperparameters ───────────────────────────────────────────────
PLATFORMS = ["tiktok", "youtube"]
DURATION = 30           # seconds of energy measurement
SCROLL_INTERVAL = 5     # seconds between scrolls
WARMUP_TIME = 2         # seconds to warm up before measurement

READY_SIGNAL = ".measurement_ready"
OUTPUT_DIR = "measurements"
PARENT_DIR = "SSE_P1"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_experiment(platform):
    """Run the full experiment for a given platform"""
    output_file = f"{PARENT_DIR}/{OUTPUT_DIR}/chrome_{platform}.csv"
    
    print(f"\n{'='*60}")
    print(f"Running experiment: CHROME + {platform.upper()}")
    print(f"{'='*60}")
    print(f"Duration: {DURATION}s, Scroll interval: {SCROLL_INTERVAL}s, Warmup: {WARMUP_TIME}s")
    
    # 1. Start setup in the background
    print("\n[1/2] Starting setup phase...")
    setup = subprocess.Popen(["python", f"{PARENT_DIR}/chrome_setup.py", platform])
    
    # 2. Wait for the ready signal
    print("Waiting for browser setup to complete...")
    waited = 0
    while not os.path.exists(READY_SIGNAL):
        time.sleep(0.5)
        waited += 0.5
        if waited > 60:
            setup.terminate()
            raise TimeoutError("Setup never signalled ready.")
    
    # 3. Immediately hand off to energibridge — this is the only measured window
    print("\n[2/2] Starting energy measurement...")
    subprocess.run([
        "./target/release/energibridge",
        "--summary",
        "-o", output_file,
        "--",
        "python", f"{PARENT_DIR}/chrome_measure.py"
    ])
    
    # 4. Wait for setup to finish closing the browser
    setup.wait()
    
    print(f"\n✓ Experiment complete. Results saved to {output_file}")
    return output_file

if __name__ == "__main__":
    results = []
    
    for platform in PLATFORMS:
        try:
            result = run_experiment(platform)
            results.append((platform, result))
        except Exception as e:
            print(f"\n✗ Error running experiment for {platform}: {e}")
    
    print(f"\n{'='*60}")
    print("All experiments completed!")
    print(f"{'='*60}")
    for platform, result in results:
        print(f"  {platform}: {result}")