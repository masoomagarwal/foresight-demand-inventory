# Project FORESIGHT — Demand & Inventory Intelligence

Client engagement for **NorthBay Living**, a D2C home & lifestyle brand. NorthBay was planning
inventory on gut feel — running out of best-sellers while sitting on slow movers. This project
delivers an 8-week SKU-level demand forecast, a stockout/overstock risk score for every SKU, and
a rupee-quantified action list the operations team can use without a data scientist in the room.

## The Data

Four raw extracts, in `data/raw/`:
- `sales_daily.csv` — daily units sold, revenue, price, promo flag per SKU
- `sku_master.csv` — category, subcategory, launch date, cost, list price per SKU
- `calendar.csv` — date, week/month/season, holiday flag, promo events
- `inventory_snapshots.csv` — on-hand, on-order, lead time, reorder point per SKU

Cleaning decisions and data-quality issues found are documented in `reports/data_quality_report.md`.

## Setup & Run

1. Create and activate a virtual environment, then `pip install -r requirements.txt`
2. Run the cleaning pipeline from the project root — this produces the cleaned data everything else depends on:
```
   python src/pipeline.py
```
3. Run the notebooks in order — each one regenerates the processed files the next one needs:
   - `notebooks/01_explore.ipynb`
   - `notebooks/02_eda.ipynb`
   - `notebooks/03_baseline.ipynb` — builds the baseline, trains the model, backtests it, generates the 8-week horizon forecast
   - `notebooks/04_risk_scoring.ipynb` — turns the forecast into risk scores and rupee impact
4. Dashboard (run from the project root):
```
   streamlit run app/dashboard.py
```
5. Scoring API (run from inside `service/`):
```
   cd service
   uvicorn main:app --reload
```
   Interactive docs at `http://127.0.0.1:8000/docs`

### First-time login
Both the dashboard and the API require a registered account before use — there's no default/guest access.
- **Dashboard:** use the registration form on first load to create an account, then log in.
- **API:** call `POST /register` with a username and password first, then use those credentials for subsequent requests.

## Backtest Result

Model: LightGBM regressor, features = SKU, year-ago demand, 3 lag features, rolling 4-week average, month, promo flag.
Validated with 3-fold **rolling-origin** cross-validation (never a random split — see Section 07 of the engagement brief for why that matters for time series).

| | WAPE |
|---|---|
| Seasonal-naive baseline | 14.5% |
| LightGBM model | **13.9%** |

The model beats the baseline on an honest backtest. Full detail in `reports/eda_insight_memo.md`.

## Key Assumptions & Limitations

- **No future promotional calendar** exists in the provided data — `promo_flag = 0` is assumed for all 8 forecast weeks. Demand in weeks with an actual planned promotion will be underestimated.
- **The 8-week forecast is built recursively** — each week's prediction feeds into the next week's lag features. Error can compound over the horizon, most visibly for SKUs with volatile recent history (e.g. `SKU0077`, see `reports/eda_insight_memo.md` Section 5).
- **30 of 200 SKUs** have too little sales history to support the full model and fall back to a flat category-average forecast — flagged via `is_low_confidence` in the output.

## Live Links

- Dashboard: https://foresight-sku-forecast.streamlit.app
- Scoring API: https://foresight-demand-inventory-yawt.onrender.com
- API docs (Swagger UI): https://foresight-demand-inventory-yawt.onrender.com/docs

## Repository Structure

```
foresight/
  data/              raw + processed data
  notebooks/         01_explore, 02_eda, 03_baseline, 04_risk_scoring
  app/                Streamlit planning dashboard
  service/            FastAPI scoring service
  reports/            data quality report, EDA memo, figures
  requirements.txt
```