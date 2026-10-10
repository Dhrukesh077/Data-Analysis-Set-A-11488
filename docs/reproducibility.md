# Reproducibility

## Environment used for this build
| Component | Version | Verified |
|---|---|---|
| Python | 3.12.3 | ✔ ran script and tests |
| pandas / matplotlib | 3.0.2 / 3.10.8 | ✔ |
| openpyxl (workbook generation) | 3.1.5 | ✔ |
| MariaDB (MySQL-compatible) | 10.11.14 | ✔ ran `setup.sql`, `queries.sql` |
| LibreOffice (recalculation + render check) | 24.2.7.2 | ✔ 0 formula errors |
| Oracle MySQL 8.0 | – | ✘ not tested |
| Microsoft Excel desktop | – | ✘ not opened |
| Power BI Desktop | – | ✘ not available; PBIX not built |

## Steps
```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python python/analysis.py
python -m unittest discover -s tests -v
mysql -u <user> -p < sql/setup.sql && mysql -u <user> -p < sql/queries.sql
```
Raw files are verified unchanged by SHA-256 on every run.
