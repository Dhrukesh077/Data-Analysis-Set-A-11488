# SQL Guide

**Engine:** MySQL 8.0-compatible SQL. **Actually tested on MariaDB 10.11.14** (MySQL-compatible). It has **not** been run on Oracle MySQL 8.0 here; only standard features are used (`GREATEST`, `GROUP_CONCAT`, `HAVING`, `LIMIT`, FK constraints), which MySQL 8.0 supports.

## Run
```bash
mysql -u <user> -p < sql/setup.sql      # creates delivery_delay_analysis, loads 4 routes + 12 deliveries (re-runnable)
mysql -u <user> -p < sql/queries.sql    # S2a, S2b, S2c and the integrity diagnostic
```
(Requires database credentials – never commit passwords.)

## Expected results
| Query | Result |
|---|---|
| setup check | route_rows 4, delivery_rows 12 |
| S2a | Standard 22, Express 12 |
| S2b (> 8) | R4 Rural Feeder 14, R1 Metro Link 9 (R3 = 8 excluded) |
| S2c | Mumbai 15, Delhi 14 |
| Integrity | 12 rows checked, 0 unmatched route keys |

## Exporting results (as done for `outputs/sql/`)
```bash
mysql -u <user> -p -B delivery_delay_analysis -e "<query>" | tr '\t' ','  > outputs/sql/<file>.csv
```
(Safe here because no value contains a comma. The committed CSVs were produced with a Python csv writer for strict quoting.)
`data_integrity_check.txt` was produced from the diagnostic query plus row counts.

## Tests actually performed
- Schema creation from scratch and a second re-run (idempotent) ✔
- FK enforcement: inserting `route_id = 'R9'` fails with error 1452 ✔
- Diagnostic negative test: with FK checks disabled and a bad `R9` row, the diagnostic reports `unmatched = 1, ids = R9` (then the database was reset) ✔
