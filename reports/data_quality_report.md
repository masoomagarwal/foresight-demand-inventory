# Data Quality Report — Project FORESIGHT

## 1. Source Data

- `sales_daily.csv` contains 125,967 rows. Each row represents units of one SKU sold on one date.
- `sku_master.csv` contains 203 rows. Each row represents one SKU (product), with its category, subcategory, launch date, cost, and price.
- `calendar.csv` contains 731 rows. Each row represents one calendar date, with week/month/season and holiday/promo info.
- `inventory_snapshots.csv` contains 17,859 rows. Each row represents one SKU's stock position on one date (weekly snapshots).

## 2. Issues Found and How They Were Handled

### sales_daily

- Found 1,890 missing values in `units_sold` and 1,888 missing values in `revenue`.
  Fixed by: recovering missing values using the relationship `revenue = units_sold × unit_price`.
  Why this works: if I know two of the three values (units_sold, unit_price, revenue), I can calculate the third algebraically — no guessing involved.
  For the 23 rows where both values were missing and unrecoverable, I filled them with `0` instead of dropping the row, because dropping would remove that date entirely from the table, creating a gap in the daily calendar that could later be mistaken for a real stockout by a forecasting model.

- Found 376 duplicate rows (exact copies across all columns).
  Fixed by: dropping them — they add no new information and would otherwise double-count sales.

- Found 123 negative values in `units_sold`, which is impossible because you cannot physically sell a negative number of units (no returns field exists in this data).
  Fixed by: treating them as missing, then applying the same recovery logic used above.

### sku_master

- Found ~20 rows with inconsistent category text (e.g. `"FURNISHINGS"`, `" Decor "`, `"decor"` instead of a single consistent spelling).
  Fixed by: stripping extra whitespace and standardizing to Title Case, collapsing 16 inconsistent text variants down to the correct 5 categories.

- Found 3 duplicate rows (exact copies).
  Fixed by: dropping them.

- Found 5 missing `unit_cost` values and 3 missing `list_price` values.
  Fixed by: filling with that SKU's category median, since cost and price cluster far more by category (e.g. Furnishings vs. Décor) than by any other available attribute — a more defensible stand-in than guessing an arbitrary number.

### inventory_snapshots

- Found 32 negative `on_hand_units` values, which is physically impossible — stock cannot be negative.
  Fixed by: taking the absolute value, treating it as a sign-entry error rather than discarding the row.

- Found 178 missing `lead_time_days` values.
  Fixed by: filling with that specific SKU's own median lead time (lead time is mostly a property of the SKU/supplier relationship), falling back to the overall median only if a SKU had no other snapshots to learn from.

### calendar

- No data-quality issues found. 0 duplicate dates, 0 missing values in any required column.
- Note: `promo_event` is null for most rows (605 of 731) — this is expected, not an issue, since most days simply aren't a promotion day.

## 3. Resulting Datasets

Running `python src/pipeline.py` produces:

| Output | Shape | Purpose |
|---|---|---|
| `data/processed/sales_master.csv` | 125,591 rows × 16 cols | Daily, SKU-level, analysis-ready — used for demand forecasting |
| `data/processed/sku_master_clean.csv` | 200 rows × 6 cols | Cleaned SKU dimension |
| `data/processed/inventory_clean.csv` | 17,859 rows × 6 cols | Cleaned weekly inventory positions — used later for risk scoring |

`inventory_snapshots` is kept as a separate table rather than merged into `sales_master` because it's captured at a different grain (weekly, not daily) — it gets joined in during risk scoring (Week 3), where the relevant time unit is the forecast horizon, not the daily sales record.