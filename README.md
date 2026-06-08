# global-telemetry-data-pipeline

One sentence: what this project does.

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in any secrets
```

## Run
```bash
python -m src.global_telemetry_data_pipeline.main
```
```bash
env: gtdp
```

## Project layout
- `src/global_telemetry_data_pipeline/` — application code
- `data/raw/` — untouched source data (gitignored)
- `data/processed/` — cleaned output (gitignored)
- `tests/` — tests
