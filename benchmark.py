# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///

import csv
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.animation as animation

CSV_PATH = Path("stats.csv")
INTERVAL_SECONDS = 1


ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|\x1b\[H")


def strip_ansi(text):
    return ANSI_ESCAPE.sub("", text)


def parse_memory_mb(raw):
    raw = strip_ansi(raw).strip().split("/")[0].strip()
    if raw.endswith("GiB"):
        return float(raw.replace("GiB", "")) * 1024
    if raw.endswith("MiB"):
        return float(raw.replace("MiB", ""))
    if raw.endswith("KiB"):
        return float(raw.replace("KiB", "")) / 1024
    return 0.0


def parse_cpu(raw):
    return float(strip_ansi(raw).replace("%", "").strip())


def collect_stats(container):
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["elapsed_s", "memory_mb", "cpu_percent"])

    start = time.time()
    proc = subprocess.Popen(
        ["docker", "stats", container, "--format", "{{.MemUsage}},{{.CPUPerc}}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue

        parts = line.split(",")
        if len(parts) != 2:
            continue

        mem_mb = parse_memory_mb(parts[0])
        cpu = parse_cpu(parts[1])
        elapsed = round(time.time() - start, 1)

        with open(CSV_PATH, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([elapsed, mem_mb, cpu])


def read_csv():
    if not CSV_PATH.exists():
        return [], [], []
    with open(CSV_PATH, "r") as f:
        reader = csv.DictReader(f)
        elapsed, mem, cpu = [], [], []
        for row in reader:
            elapsed.append(float(row["elapsed_s"]))
            mem.append(float(row["memory_mb"]))
            cpu.append(float(row["cpu_percent"]))
        return elapsed, mem, cpu


def main():
    container = sys.argv[1] if len(sys.argv) > 1 else "pluto"

    collector = threading.Thread(target=collect_stats, args=(container,), daemon=True)
    collector.start()

    fig, (ax_mem, ax_cpu) = plt.subplots(2, 1, sharex=True, figsize=(10, 6))
    fig.suptitle(f"Docker stats: {container}")

    def update(_frame):
        elapsed, mem, cpu = read_csv()
        if not elapsed:
            return

        ax_mem.clear()
        ax_mem.plot(elapsed, mem, color="steelblue")
        ax_mem.set_ylabel("Memory (MiB)")
        ax_mem.grid(True, alpha=0.3)

        ax_cpu.clear()
        ax_cpu.plot(elapsed, cpu, color="coral")
        ax_cpu.set_ylabel("CPU (%)")
        ax_cpu.set_xlabel("Elapsed (s)")
        ax_cpu.grid(True, alpha=0.3)

    _anim = animation.FuncAnimation(fig, update, interval=INTERVAL_SECONDS * 1000, cache_frame_data=False)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
