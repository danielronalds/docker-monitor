# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///

import argparse
import csv
import re
import subprocess
import threading
import time
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.animation as animation

CSV_PATH = Path("stats.csv")
INTERVAL_SECONDS = 1

ALL_STATS = ["memory", "cpu", "net_io", "block_io"]

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


def parse_bytes_mb(raw):
    raw = strip_ansi(raw).strip()
    if raw.endswith("GB"):
        return float(raw.replace("GB", "")) * 1024
    if raw.endswith("MB"):
        return float(raw.replace("MB", ""))
    if raw.endswith("kB"):
        return float(raw.replace("kB", "")) / 1024
    if raw.endswith("B"):
        return float(raw.replace("B", "")) / (1024 * 1024)
    return 0.0


def parse_io_pair(raw):
    parts = strip_ansi(raw).split("/")
    if len(parts) != 2:
        return 0.0, 0.0
    return parse_bytes_mb(parts[0]), parse_bytes_mb(parts[1])


def parse_pids(raw):
    return int(strip_ansi(raw).strip())


CSV_HEADER = [
    "elapsed_s", "memory_mb", "cpu_percent",
    "net_in_mb", "net_out_mb", "block_in_mb", "block_out_mb", "pids",
]


def collect_stats(container):
    with open(CSV_PATH, "w", newline="") as f:
        csv.writer(f).writerow(CSV_HEADER)

    start = time.time()
    proc = subprocess.Popen(
        [
            "docker", "stats", container, "--format",
            "{{.MemUsage}},{{.CPUPerc}},{{.NetIO}},{{.BlockIO}},{{.PIDs}}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue

        parts = line.split(",")
        if len(parts) != 5:
            continue

        mem_mb = parse_memory_mb(parts[0])
        cpu = parse_cpu(parts[1])
        net_in, net_out = parse_io_pair(parts[2])
        block_in, block_out = parse_io_pair(parts[3])
        pids = parse_pids(parts[4])
        elapsed = round(time.time() - start, 1)

        with open(CSV_PATH, "a", newline="") as f:
            csv.writer(f).writerow([
                elapsed, mem_mb, cpu, net_in, net_out, block_in, block_out, pids,
            ])


def read_csv():
    if not CSV_PATH.exists():
        return {}
    with open(CSV_PATH, "r") as f:
        reader = csv.DictReader(f)
        data = {col: [] for col in CSV_HEADER}
        for row in reader:
            for col in CSV_HEADER:
                data[col].append(float(row[col]))
        return data


STAT_CONFIG = {
    "memory": {
        "ylabel": "Memory (MiB)",
        "columns": [("memory_mb", "steelblue", None)],
    },
    "cpu": {
        "ylabel": "CPU (%)",
        "columns": [("cpu_percent", "coral", None)],
    },
    "net_io": {
        "ylabel": "Net I/O (MB)",
        "columns": [
            ("net_in_mb", "forestgreen", "In"),
            ("net_out_mb", "mediumpurple", "Out"),
        ],
    },
    "block_io": {
        "ylabel": "Block I/O (MB)",
        "columns": [
            ("block_in_mb", "goldenrod", "Read"),
            ("block_out_mb", "indianred", "Write"),
        ],
    },
}


def main():
    parser = argparse.ArgumentParser(
        description="Live-stream Docker container stats to a matplotlib chart.",
    )
    parser.add_argument("container", nargs="?", help="name or ID of the Docker container to monitor")
    parser.add_argument("-c", "--cpu", action="store_true", help="show CPU usage")
    parser.add_argument("-m", "--memory", action="store_true", help="show memory usage")
    parser.add_argument("-n", "--net-io", action="store_true", help="show network I/O")
    parser.add_argument("-b", "--block-io", action="store_true", help="show block I/O")
    args = parser.parse_args()

    if not args.container:
        parser.print_help()
        raise SystemExit(1)

    container = args.container

    selected = [s for s in ALL_STATS if getattr(args, s.replace("-", "_"))]
    if not selected:
        selected = ALL_STATS

    collector = threading.Thread(target=collect_stats, args=(container,), daemon=True)
    collector.start()

    n = len(selected)
    fig, axes = plt.subplots(n, 1, sharex=True, figsize=(10, 3 * n), squeeze=False)
    axes = [ax[0] for ax in axes]
    fig.canvas.manager.set_window_title(f"{container} - Stats")

    def update(_frame):
        data = read_csv()
        if not data or not data.get("elapsed_s"):
            return

        elapsed = data["elapsed_s"]

        if data.get("pids"):
            latest_pids = int(data["pids"][-1])
            fig.canvas.manager.set_window_title(f"{container} - Stats (PIDs: {latest_pids})")

        for ax, stat in zip(axes, selected):
            config = STAT_CONFIG[stat]
            ax.clear()
            for col, colour, label in config["columns"]:
                ax.plot(elapsed, data[col], color=colour, label=label)
            ax.set_ylabel(config["ylabel"])
            ax.grid(True, alpha=0.3)
            if label:
                ax.legend(loc="upper left", fontsize="small")

        axes[-1].set_xlabel("Elapsed (s)")

    _anim = animation.FuncAnimation(fig, update, interval=INTERVAL_SECONDS * 1000, cache_frame_data=False)
    plt.tight_layout()
    plt.subplots_adjust(left=0.1, bottom=0.1)
    plt.show()


if __name__ == "__main__":
    main()
