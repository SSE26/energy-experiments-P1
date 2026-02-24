import time
import os

# ── Must match chrome_setup.py ────────────────────────────────────────────────
DURATION = 30
READY_SIGNAL = ".measurement_ready"

# Wait for setup to reach steady state (timeout after 60 s)
print("Waiting for browser setup to complete...")
waited = 0
while not os.path.exists(READY_SIGNAL):
    time.sleep(0.5)
    waited += 0.5
    if waited > 60:
        raise TimeoutError("chrome_setup.py never signalled ready.")

# ── This sleep is the exact window energibridge measures ─────────────────────
print(f"Measuring energy for {DURATION} s...")
time.sleep(DURATION)
print("Measurement complete.")