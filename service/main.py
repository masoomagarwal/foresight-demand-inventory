import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import pandas as pd

# Make the project-root auth_store module importable regardless of cwd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from auth_store import create_user, verify_user

app = FastAPI(title="Project FORESIGHT Scoring API")

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "risk_scored.csv"
risk_data = pd.read_csv(DATA_PATH)

# ---------- Auth ----------
# Accounts are shared with the dashboard (same data/users.json store via
# auth_store.py). Register with POST /register, then call the protected
# routes below using HTTP Basic Auth with that username/password.
security = HTTPBasic()


def authenticate(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    if not verify_user(credentials.username, credentials.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str = ""
    email: str = ""


def serialize_sku(row):
    return {
        "sku_id": row["sku_id"],
        "demand_8weeks": round(row["demand_8weeks"], 1),
        "risk_category": row["risk_category"],
        "recommended_action": row["recommended_action"],
        "stockout_value_at_risk": round(row["stockout_value_at_risk"], 2),
        "overstock_capital_locked": round(row["overstock_capital_locked"], 2),
    }


@app.get("/")
def read_root():
    return {"message": "Project FORESIGHT scoring service is running."}


@app.post("/register")
def register(payload: RegisterRequest):
    """Create a new account. Shared with the dashboard's login/register form."""
    success, message = create_user(
        payload.username, payload.password, name=payload.name, email=payload.email
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}


@app.get("/forecast/batch")
def get_forecast_batch(sku_ids: str, username: str = Depends(authenticate)):
    """
    Return forecast and risk for multiple SKUs at once.
    Pass a comma-separated list, e.g. /forecast/batch?sku_ids=SKU0077,SKU0198
    """
    requested = [s.strip().upper() for s in sku_ids.split(",") if s.strip()]
    if not requested:
        raise HTTPException(status_code=400, detail="No SKU IDs provided.")

    results = []
    not_found = []
    for sku_id in requested:
        match = risk_data[risk_data["sku_id"] == sku_id]
        if match.empty:
            not_found.append(sku_id)
        else:
            results.append(serialize_sku(match.iloc[0]))

    return {"results": results, "not_found": not_found}


@app.get("/forecast/{sku_id}")
def get_forecast(sku_id: str, username: str = Depends(authenticate)):
    """Return the 8-week demand forecast and risk assessment for a single SKU."""
    match = risk_data[risk_data["sku_id"] == sku_id.upper()]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"SKU '{sku_id}' not found.")
    return serialize_sku(match.iloc[0])