import subprocess
import os
import time
from datetime import datetime

# ── Experiment hyperparameters ───────────────────────────────────────────────
PLATFORMS = ["tiktok", "youtube"]
DURATION = 30           # seconds of energy measurement
SCROLL_INTERVAL = 5     # seconds between scrolls
WARMUP_TIME = 2         # seconds to warm up before measurement
NUM_ITERATIONS = 30     # number of times to run each experiment

READY_SIGNAL = ".measurement_ready"
OUTPUT_DIR = "measurements_5"
PARENT_DIR = "SSE_P1"

os.makedirs(f"{PARENT_DIR}/{OUTPUT_DIR}", exist_ok=True)

def run_experiment(platform, iteration):
    """Run a single experiment for a given platform and iteration"""
    # Unique naming: chrome_tiktok_001.csv, chrome_tiktok_002.csv, etc.
    output_file = f"{PARENT_DIR}/{OUTPUT_DIR}/chrome_{platform}_{iteration:03d}.csv"
    
    print(f"\n{'='*60}")
    print(f"Experiment {iteration}/{NUM_ITERATIONS}: CHROME + {platform.upper()}")
    print(f"{'='*60}")
    print(f"Output: {output_file}")
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
        if waited > 120:
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
    
    print(f"\n✓ Experiment {iteration} complete. Results saved to {output_file}")
    return output_file

if __name__ == "__main__":
    start_time = datetime.now()
    results = []
    total_experiments = len(PLATFORMS) * NUM_ITERATIONS
    completed = 0
    
    print(f"\n{'='*60}")
    print(f"STARTING EXPERIMENT SUITE")
    print(f"{'='*60}")
    print(f"Platforms: {', '.join(PLATFORMS)}")
    print(f"Iterations per platform: {NUM_ITERATIONS}")
    print(f"Total experiments: {total_experiments}")
    print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    for platform in PLATFORMS:
        print(f"\n{'#'*60}")
        print(f"# PLATFORM: {platform.upper()}")
        print(f"{'#'*60}")
        
        platform_results = []
        for iteration in range(1, NUM_ITERATIONS + 1):
            try:
                result = run_experiment(platform, iteration)
                platform_results.append((iteration, result))
                completed += 1
                
                # Print progress
                progress = (completed / total_experiments) * 100
                print(f"\nProgress: {completed}/{total_experiments} ({progress:.1f}%)")
                
                # Add small delay between experiments to let system settle
                if iteration < NUM_ITERATIONS:
                    print(f"Waiting 5 seconds before next experiment...")
                    time.sleep(5)
                    
            except Exception as e:
                print(f"\n✗ Error running experiment {iteration} for {platform}: {e}")
                completed += 1
        
        results.append((platform, platform_results))
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n{'='*60}")
    print(f"EXPERIMENT SUITE COMPLETED!")
    print(f"{'='*60}")
    print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total duration: {duration}")
    print(f"Total experiments completed: {completed}/{total_experiments}")
    print(f"{'='*60}\n")
    
    for platform, platform_results in results:
        print(f"\n{platform.upper()}:")
        print(f"  Total runs: {len(platform_results)}")
        for iteration, result in platform_results:
            print(f"    Run {iteration:03d}: {result}")