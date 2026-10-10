# Findings

All numbers are computed from the 12 clean records (`python python/analysis.py`) and confirmed in MariaDB SQL and the Excel workbook.

## Headline results

| Measure | Result |
|---|---|
| Total delay days | **34** |
| Delayed records | 9 of 12 → **75.00%** incidence |
| Highest-burden service type | **Standard – 22 days** (64.71% of total) vs Express 12 |
| Highest-burden hub | **Mumbai – 15 days**, then Delhi 14, Chennai 5 |
| Highest-burden route | **R4 Rural Feeder – 14 days (41.18% of total)** |
| Routes above 8-day threshold | R4 (14) and R1 (9); R3 sits exactly at 8 and is **not** included (strictly > 8) |

## Monthly trend

| Month | Delay days | Delayed records | Incidence |
|---|---:|---:|---:|
| Jan | 8 | 3 of 4 | 75.00% |
| Feb | 9 | 3 of 4 | 75.00% |
| Mar | 17 | 3 of 4 | 75.00% |

The number of delayed records is flat; the burden **more than doubled from Jan to Mar (8 → 17)** because delays became *longer* (March contains the 9-day delay on R4 and the 6-day delay on R1).

## Service type: burden vs incidence

| Service type | Delay days | Delayed / total | Incidence |
|---|---:|---:|---:|
| Standard | 22 | 5 / 6 | 83.33% |
| Express | 12 | 4 / 6 | 66.67% |

Standard is worse on both measures here. Express still has two thirds of its records delayed, so a lower total does not mean a low incidence.

## Hubs
Mumbai (15) and Delhi (14) together hold 85.29% of the delay days; Chennai holds 5. Every hub has the same 75.00% incidence (3 of 4), so hub differences are about **severity**, not frequency. Mumbai's total is driven by R4 (record 12: 9 days; record 4: 4 days).

## Sensitivity of the hub ranking
Mumbai leads Delhi by only **1 day (15 vs 14)**. A leave-one-out test (notebook section 10) shows that removing any single one of records **4, 10 or 12** (all Mumbai) makes Delhi the top hub. The Mumbai-first ranking is therefore fragile; R4 (14 days, 3 of 3 records delayed) is the more robust signal.

## Recommendation
Prioritise a review of **Standard-service route R4 (Rural Feeder) out of Mumbai** first, then Delhi, because that combination carries the largest single share of cumulative delay (R4 = 41.18% of all delay days; Mumbai = 44.12%). Practical first step: examine the promised-day commitments and handling steps on R4/Mumbai, where promised 6 days vs actual 10 and 15.

**How the evidence supports it:** R4 has the highest route total (14), is 100% delayed (3 of 3 records: 4, 1 and 9 days in Jan, Feb and Mar) and holds the single largest delay (9 days, March). Mumbai has the highest hub total. Both point at the same place.

## Cross-tool reconciliation (Standard total delay days)

| Metric | Excel | SQL (MariaDB 10.11.14) | Python | Power BI | Status |
|---|---|---|---|---|---|
| Standard total delay days | 22 | 22.00 | 22 | Not built (no Power BI Desktop in this environment) | Excel = SQL = Python ✔; Power BI pending |

No rounding differences (SQL returns DECIMAL(…,2) so `22.00`).

## Limitations
- 12 synthetic summary rows over 3 months: no statistical significance can be claimed.
- Rows are month-end summaries, not parcels; delay days are cumulative, not a count of parcels.
- The data cannot show **why** delays occur (no capacity, weather, volume, distance) – no causation is claimed.
- Hub × route combinations contain 1–2 records, so single records drive several rankings (e.g. record 12 = 9 of Mumbai's 15 days).
