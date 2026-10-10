# Methodology

## Pipeline (identical logic in Python, SQL, Excel, Power BI)
1. Load `deliveries.csv` (13 rows) and `routes.csv` (4 rows).
2. Validate columns, types, row counts, exactly one exact duplicate, unique `route_id`.
3. Remove the exact duplicate (keep first) → 12 records.
4. Left-join routes on `route_id` (many-to-one); assert no missing `service_type`.
5. Compute `delay_days`, delayed flag, then aggregate by service type, hub, route and month.

## Metric definitions
```text
delay_days            = MAX(actual_days - promised_days, 0)
Total Delay Days      = SUM(delay_days)                      (12 clean records)
Delayed record        = actual_days > promised_days
Delay Incidence Rate  = delayed records / total records * 100
Month order           = Jan -> Feb -> Mar   (never alphabetical)
```

Rates are always recomputed from underlying counts. Averaging subgroup rates gives a wrong overall rate whenever group sizes differ (unit test `test_incidence_not_average_of_subgroup_rates` demonstrates this).

## Interpretation rules
- `delay_days` is a **cumulative record-level delay burden**, not a count of parcels to expedite.
- Rows are summaries; no parcel-level inference is made.
- Cumulative delay (days) and delay incidence (share of delayed records) answer different questions and are reported separately.

## Tie handling
Rankings sort by total delay descending, then name ascending. No ties occur in the supplied data at the top ranks.
