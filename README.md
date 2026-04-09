# docker-benchmark

Live Docker container resource monitoring with matplotlib.

## Getting Started

Copy and run the following command to get it running locally (assuming you have `uv` installed)

```sh
uv run https://raw.githubusercontent.com/danielronalds/docker-benchmark/main/benchmark.py <container>
```

## Usage

```sh
# Run locally
uv run benchmark.py <container>

# Run directly from GitHub
uv run https://raw.githubusercontent.com/danielronalds/docker-benchmark/main/benchmark.py <container>

# Show help
uv run benchmark.py --help
```

Outputs a live-updating chart with memory (MiB) and CPU (%) over time. Stats are also written to `stats.csv`.

**Note:** This script is very vibecoded. This isn't supposed to be a proper tool, just a convenient script I made for future me
