# docker-benchmark

Live Docker container resource monitoring with matplotlib.

## Getting Started

Copy and run the following command to get it running locally (Assuming you have `uv` installed)

```sh
uv run https://raw.githubusercontent.com/danielronalds/docker-benchmark/main/benchmark.py
```

## Usage

```sh
# Run locally
uv run benchmark.py

# Run directly from GitHub
uv run https://raw.githubusercontent.com/danielronalds/docker-benchmark/main/benchmark.py

# Specify a container name (defaults to "pluto")
uv run benchmark.py mycontainer
```

Outputs a live-updating chart with memory (MiB) and CPU (%) over time. Stats are also written to `stats.csv`.

**Note:** This script is very vibecoded. This isn't supposed to be a proper tool, just a convenient script I made for future me
