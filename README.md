# docker-benchmark

Live Docker container resource monitoring with matplotlib.

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
