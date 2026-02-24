import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("measurements/instagram.csv")

total_package_energy = df["PACKAGE_ENERGY (J)"].iloc[-1] - df["PACKAGE_ENERGY (J)"].iloc[0]
total_dram_energy    = df["DRAM_ENERGY (J)"].iloc[-1]    - df["DRAM_ENERGY (J)"].iloc[0]
df["elapsed_s"] = (df["Time"] - df["Time"].iloc[0]) / 1e9  # nanoseconds → seconds

print(f"Package energy: {total_package_energy:.2f} J")
print(f"DRAM energy:    {total_dram_energy:.2f} J")
print(f"Total energy:   {total_package_energy + total_dram_energy:.2f} J")

plt.plot(df["elapsed_s"], df["PACKAGE_ENERGY (J)"])
plt.xlabel("Time (s)")
plt.ylabel("Cumulative Package Energy (J)")
plt.title("Spotify - Energy over Time")
plt.show()
