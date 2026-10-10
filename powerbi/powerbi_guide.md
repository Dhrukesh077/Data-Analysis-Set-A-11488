# Power BI Guide (build instructions – PBIX not yet created)

> **Status:** Power BI Desktop is a Windows desktop application and was not available in the build environment, so `powerbi/dashboard.pbix` and `outputs/powerbi_dashboard.png` have **not** been created. Follow the steps below; expected values are provided for validation.

## 1. Import
Home → Get data → Text/CSV: `data/raw/deliveries.csv` and `data/raw/routes.csv` → **Transform Data**.

## 2. Power Query (M)
Create a parameter `RepoPath` (Text) = folder containing the cloned repo (e.g. `C:\projects\delivery-delay-analysis`). Power BI stores CSV paths as absolute paths; a parameter means you change them in one place (Home → Transform data → Edit parameters).

`deliveries`:
```m
let
    Source   = Csv.Document(File.Contents(RepoPath & "\data\raw\deliveries.csv"),[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed    = Table.TransformColumnTypes(Promoted,{{"record_id", Int64.Type},{"month", type text},{"route_id", type text},{"hub", type text},{"promised_days", type number},{"actual_days", type number}}),
    Deduped  = Table.Distinct(Typed)          // removes the exact duplicate -> 12 rows
in
    Deduped
```
`routes`:
```m
let
    Source   = Csv.Document(File.Contents(RepoPath & "\data\raw\routes.csv"),[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed    = Table.TransformColumnTypes(Promoted,{{"route_id", type text},{"route", type text},{"service_type", type text}})
in
    Typed
```
Check in the preview: `deliveries` = **12** rows, `routes` = **4** rows. Add a `MonthSort` helper to `deliveries` (Add Column → Conditional: Jan=1, Feb=2, Mar=3) → Close & Apply.

## 3. Model
Model view: `routes[route_id]` **1 → \*** `deliveries[route_id]`, active, cross-filter **Single** (routes → deliveries). Select `deliveries[month]` → Column tools → **Sort by column → MonthSort**. Hide `MonthSort`.

## 4. Measures table
Home → Enter data → empty table named `Measures` (delete the dummy column after creating the first measure).
```dax
Delivery Count = COUNTROWS(deliveries)

Total Delay Days =
SUMX(deliveries, MAX(deliveries[actual_days] - deliveries[promised_days], 0))

Delay Incidence Rate =
DIVIDE(
    COUNTROWS(FILTER(deliveries, deliveries[actual_days] > deliveries[promised_days])),
    COUNTROWS(deliveries),
    0
)
```
Format Delay Incidence Rate as Percentage, 2 decimals; Total Delay Days with 2 decimals; Delivery Count as whole number.
(Note: `MAX(a, b)` of two scalar expressions is valid DAX row-context syntax.)

## 5. Report page
| Visual | Fields |
|---|---|
| Card | `Measures[Delivery Count]` |
| Card | `Measures[Total Delay Days]` |
| Card | `Measures[Delay Incidence Rate]` |
| Bar chart "Total Delay Days by Service Type" | Axis `routes[service_type]`, Values `Total Delay Days` |
| Column/line chart "Monthly Delay Trend" | Axis `deliveries[month]` (sorted Jan→Feb→Mar), Values `Total Delay Days` |
| Slicer "Hub" | `deliveries[hub]` |

Use one palette (e.g. `#1F4E79`, `#2E75B6`, `#9DC3E6`), titles on every visual, data labels on.

## 6. Expected values for validation
| Context | Delivery Count | Total Delay Days | Delay Incidence Rate |
|---|---:|---:|---:|
| No filter | 12 | 34.00 | 75.00% |
| Standard (bar) | 6 | 22.00 | 83.33% |
| Express (bar) | 6 | 12.00 | 66.67% |
| Jan / Feb / Mar | 4 / 4 / 4 | 8 / 9 / 17 | 75% each |
| Hub = Mumbai | 4 | 15.00 | 75.00% |
| Hub = Delhi | 4 | 14.00 | 75.00% |
| Hub = Chennai | 4 | 5.00 | 75.00% |

Test the slicer by selecting Mumbai (cards and both charts must change to the values above), then clear it.

## 7. Screenshot
With the slicer cleared: View → Full screen (or Windows Snipping Tool) → save as `outputs/powerbi_dashboard.png`. Save the report as `powerbi/dashboard.pbix`.

## 8. Refresh by a new user
Clone the repo → open the PBIX → Home → Transform data → Edit parameters → set `RepoPath` → Refresh → confirm 12/4 rows, the relationship and the measure values above → Save.
