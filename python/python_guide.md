# Python Guide

**Tested with:** Python 3.12.3, pandas 3.0.2, matplotlib 3.10.8 (Linux). Python 3.11+ is required.

```bash
python python/analysis.py                 # run the analysis
python -m unittest discover -s tests -v   # run the 19 automated tests
```
Both commands run from the repository root; paths are derived from the script location with `pathlib` (no absolute paths).

## What the script does
| Step | Function | Detail |
|---|---|---|
| 1 | `load_data` | Reads both CSVs (UTF-8) |
| 2 | `validate_raw_data` | Exact columns, 13 / 4 rows, dtypes, no NaN, exactly 1 exact duplicate, unique `route_id`, unique `record_id` after dedupe, valid months |
| 3 | `clean_deliveries` | `drop_duplicates(keep="first")` → 12 rows |
| 4 | `merge_routes` | Left join with `validate="many_to_one"`; fails on unmatched keys |
| 5 | `calculate_metrics` | `delay_days = (actual - promised).clip(lower=0)`; `is_delayed`; ordered month categorical |
| 6 | `build_*_summary` | Service, hub, route, monthly; rate computed from counts |
| 7 | `reconcile_summaries` | Every grouping must sum to the same total |
| 8 | `export_outputs` | CSVs + chart; raw-file SHA-256 compared before/after |

## Outputs
`outputs/clean_data.csv`, `python_summary.csv` (service type), `python_hub_summary.csv`, `python_route_summary.csv`, `python_monthly_summary.csv`, `python_chart.png`.

## Troubleshooting
- `FileNotFoundError ... data/raw`: run from the repository root and keep both CSVs in `data/raw/`.
- `ModuleNotFoundError`: activate the virtual environment and run `pip install -r requirements.txt`.
- Chart errors on a headless server: the script already uses the non-interactive `Agg` backend.
