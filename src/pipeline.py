import pandas as pd
import numpy as np
from pathlib import Path

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def load_raw():
    sales = pd.read_csv(RAW_DIR / "sales_daily.csv")
    sku = pd.read_csv(RAW_DIR / "sku_master.csv")
    cal = pd.read_csv(RAW_DIR / "calendar.csv")
    inv = pd.read_csv(RAW_DIR / "inventory_snapshots.csv")
    print(f"Loaded -> sales:{sales.shape} sku:{sku.shape} calendar:{cal.shape} inventory:{inv.shape}")
    return sales, sku, cal, inv


def clean_sales_daily(df):
    df = df.copy()
    
    # Step 1: drop exact duplicate rows
    df = df.drop_duplicates()
    
    # Step 2: negative units_sold are impossible -- treat as missing
    df.loc[df["units_sold"] < 0, "units_sold"] = np.nan
    
    # Step 3: recover missing revenue using units_sold * unit_price
    can_fix_revenue = df["revenue"].isna() & df["units_sold"].notna()
    df.loc[can_fix_revenue, "revenue"] = df.loc[can_fix_revenue, "units_sold"] * df.loc[can_fix_revenue, "unit_price"]
    
    # Step 4: recover missing units_sold using revenue / unit_price
    can_fix_units = df["units_sold"].isna() & df["revenue"].notna() & (df["unit_price"] > 0)
    df.loc[can_fix_units, "units_sold"] = (df.loc[can_fix_units, "revenue"] / df.loc[can_fix_units, "unit_price"]).round()
    
    # Step 5: anything still missing is unrecoverable -- fill with 0
    df["units_sold"] = df["units_sold"].fillna(0)
    df["revenue"] = df["revenue"].fillna(0)
    
    return df

def clean_sku_master(df):
    df = df.copy()
    
    # Step 1: standardize category text (strip spaces, fix casing)
    df["category"] = df["category"].str.strip().str.title()
    
    # Step 2: drop exact duplicate rows
    df = df.drop_duplicates()
    
    # Step 3: fill missing unit_cost / list_price with that category's median
    for col in ["unit_cost", "list_price"]:
        df[col] = df.groupby("category")[col].transform(lambda s: s.fillna(s.median()))
    
    return df

def clean_calendar(df):
    df = df.copy()
    df = df.drop_duplicates(subset="date")
    return df

def clean_inventory(df):
    df = df.copy()
    
    # Step 1: drop exact duplicate rows
    df = df.drop_duplicates()
    
    # Step 2: negative on_hand_units is impossible -- treat as a sign error, take absolute value
    neg_mask = df["on_hand_units"] < 0
    df.loc[neg_mask, "on_hand_units"] = df.loc[neg_mask, "on_hand_units"].abs()
    
    # Step 3: fill missing lead_time_days with that SKU's own median lead time
    df["lead_time_days"] = df.groupby("sku_id")["lead_time_days"].transform(lambda s: s.fillna(s.median()))
    
    # Step 4: if a SKU has NO lead time data at all, fall back to the overall median
    df["lead_time_days"] = df["lead_time_days"].fillna(df["lead_time_days"].median())
    
    return df

def build_sales_master(sales, sku, cal):
    df = sales.merge(sku, on="sku_id", how="left")
    df = df.merge(cal, on="date", how="left")
    return df
def main():
    sales, sku, cal, inv = load_raw()
    
    sales_clean = clean_sales_daily(sales)
    sku_clean = clean_sku_master(sku)
    cal_clean = clean_calendar(cal)
    inv_clean = clean_inventory(inv)
    
    sales_master = build_sales_master(sales_clean, sku_clean, cal_clean)
    
    sales_master.to_csv(PROCESSED_DIR / "sales_master.csv", index=False)
    inv_clean.to_csv(PROCESSED_DIR / "inventory_clean.csv", index=False)
    sku_clean.to_csv(PROCESSED_DIR / "sku_master_clean.csv", index=False)
    
    print(f"Wrote sales_master.csv  shape={sales_master.shape}")
    print(f"Wrote inventory_clean.csv  shape={inv_clean.shape}")
    print(f"Wrote sku_master_clean.csv  shape={sku_clean.shape}")
    print("Pipeline complete.")


if __name__ == "__main__":
    main()