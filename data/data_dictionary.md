# Data Dictionary

Each delivery row is a **month-end route/hub delivery summary**, not an individual parcel.

## `data/raw/deliveries.csv` (13 data rows, 12 unique)

| Column | Type | Meaning |
|---|---|---|
| `record_id` | Integer | Delivery summary record identifier |
| `month` | Text | Month represented: `Jan`, `Feb` or `Mar` |
| `route_id` | Text | Route key used to join the route lookup |
| `hub` | Text | Delivery hub (Chennai, Delhi, Mumbai) |
| `promised_days` | Numeric | Promised delivery duration |
| `actual_days` | Numeric | Actual delivery duration |

Derived columns (added after cleaning and merging):

| Column | Type | Meaning |
|---|---|---|
| `service_type` | Text | Service classification from the route lookup |
| `delay_days` | Numeric | `MAX(actual_days - promised_days, 0)` |
| `is_delayed` | Integer (0/1) | 1 when `actual_days > promised_days` (Python/Excel helper column) |
| `route` | Text | Route name from the lookup (present in `outputs/clean_data.csv`) |

## `data/raw/routes.csv` (4 data rows)

| Column | Type | Meaning |
|---|---|---|
| `route_id` | Text | Unique route identifier (lookup key) |
| `route` | Text | Human-readable route name |
| `service_type` | Text | `Express` or `Standard` |

## Relationship

`routes[route_id]` (1) → `deliveries[route_id]` (many). One route is referenced by several delivery records.

## Intentional data-quality issue

`record_id = 12` (`Mar, R4, Mumbai, 6, 15`) appears **twice** as an exact duplicate. The duplicate is removed in every tool, leaving 12 unique records. No values are imputed or altered.
