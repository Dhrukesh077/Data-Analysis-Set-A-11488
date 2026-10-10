# Excel Guide

`excel/analysis.xlsx` – 4 sheets, 98 formulas, **0 formula errors** (recalculated with LibreOffice 24.2; not opened in desktop Microsoft Excel in this environment).

| Sheet | Content |
|---|---|
| `Raw` | 13 original rows (duplicate shaded, row 14), filters, frozen header, live row count and duplicate count |
| `Lookup` | 4 routes as table `LookupTbl`; `route_id` highlighted as the key |
| `Clean` | 12 unique rows; `service_type` via `INDEX/MATCH`, `delay_days` via `MAX`, `is_delayed`; side panel shows 13 → 12 check |
| `Summary` | Hub SUMIFS table, service × month grid, service comparison, route contribution, consistency checks, column chart |

## Key formulas
```excel
service_type : =IFERROR(INDEX(Lookup!$C$2:$C$5,MATCH(C2,Lookup!$A$2:$A$5,0)),"NOT FOUND")
delay_days   : =MAX(F2-E2,0)
hub total    : =SUMIFS(Clean!$H$2:$H$13,Clean!$D$2:$D$13,A6)
service×month: =SUMIFS(Clean!$H$2:$H$13,Clean!$G$2:$G$13,$A14,Clean!$B$2:$B$13,B$13)
overall rate : =D9/C9        (from counts, not an average of hub rates)
```
`INDEX/MATCH` is used instead of `XLOOKUP` for compatibility with every Excel version; `XLOOKUP` gives the same result.

## PivotTable – manual step required
A genuine PivotTable cannot be generated reliably by the Python tooling used, so **the Summary sheet contains a formula grid in PivotTable layout, not a PivotTable** (and is labelled as such). To add the native PivotTable in Excel:
1. Click any cell in `Clean!A1:I13` → **Insert → PivotTable** → new worksheet (or place on `Summary`).
2. Rows: `service_type`; Columns: `month`; Values: **Sum of `delay_days`**.
3. Months sort alphabetically by default – drag to Jan, Feb, Mar (or right-click → Sort → Custom list `Jan,Feb,Mar`).
4. **PivotTable Analyze → PivotChart → Clustered Column**; add title, axis titles and legend.
5. Check that the Standard total equals 22 and the grand total equals 34.

## Extending safely
Add new records at the bottom of `Clean`, copy the formula columns G:I down and extend the `$2:$13` ranges (or convert `Clean` to an Excel Table to make ranges grow automatically).
