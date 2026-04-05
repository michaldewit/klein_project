"""
API 3 - Election Data API
Goal: Serve real data from uitslagen.csv using pandas + FastAPI.
      Learn query params, filtering, and working with DataFrames in an API.

Data: 2021 Dutch national election results per municipality.

Endpoints:
  GET /elections                        - paginated list of all records
  GET /elections/parties                - list all party names
  GET /elections/regions                - list all region names
  GET /elections/results                - filter by ?party= and/or ?region=
  GET /elections/summary                - totals per party across all regions
  GET /elections/zero-votes             - parties that have 0 votes in any region
  GET /elections/region/{region_name}   - full breakdown for one region (404 if unknown)
"""

import os
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query

app = FastAPI(
    title="API 3 - Election Data",
    description="Query Dutch 2021 election results from uitslagen.csv.",
    version="1.0.0",
)

# ── Load data ─────────────────────────────────────────────────────────────────

_CSV_PATH = Path(__file__).parent.parent.parent / "uitslagen.csv"

# Party columns start after the metadata columns
_META_COLS = [
    "RegioNaam", "RegioCode", "AmsterdamseCode", "OuderRegioNaam",
    "OuderRegioCode", "Kiesgerechtigden", "Opkomst",
    "OngeldigeStemmen", "BlancoStemmen", "GeldigeStemmen",
]


def load_data(path: Optional[str] = None) -> pd.DataFrame:
    csv_path = Path(path) if path else _CSV_PATH
    df = pd.read_csv(csv_path, sep=";")
    # Fill NaN vote counts with 0
    party_cols = [c for c in df.columns if c not in _META_COLS]
    df[party_cols] = df[party_cols].fillna(0).astype(int)
    return df


def get_party_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in _META_COLS]


# Load data at import time so TestClient and uvicorn both work
_df: pd.DataFrame = load_data()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/elections", summary="List all election records")
def list_elections(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=355),
):
    subset = _df[_META_COLS].iloc[skip: skip + limit]
    return subset.to_dict(orient="records")


@app.get("/elections/parties", summary="List all party names")
def list_parties():
    return {"parties": get_party_columns(_df)}


@app.get("/elections/regions", summary="List all region names")
def list_regions():
    return {"regions": sorted(_df["RegioNaam"].tolist())}


@app.get("/elections/results", summary="Filter results by party and/or region")
def get_results(
    party: Optional[str] = Query(default=None, description="Party column name"),
    region: Optional[str] = Query(default=None, description="Region name (RegioNaam)"),
):
    df = _df.copy()

    if region:
        df = df[df["RegioNaam"].str.lower() == region.lower()]
        if df.empty:
            raise HTTPException(status_code=404, detail=f"Region '{region}' not found")

    if party:
        party_cols = get_party_columns(_df)
        matched = next((c for c in party_cols if c.lower() == party.lower()), None)
        if not matched:
            raise HTTPException(status_code=404, detail=f"Party '{party}' not found")
        cols = ["RegioNaam"] + [matched]
        return df[cols].to_dict(orient="records")

    return df[["RegioNaam"] + get_party_columns(_df)].to_dict(orient="records")


@app.get("/elections/summary", summary="Total votes per party across all regions")
def get_summary():
    party_cols = get_party_columns(_df)
    totals = _df[party_cols].sum().sort_values(ascending=False)
    return {"totals": totals.to_dict()}


@app.get("/elections/zero-votes", summary="Regions where a party received 0 votes")
def get_zero_votes():
    party_cols = get_party_columns(_df)
    results = []
    for party in party_cols:
        zero_regions = _df.loc[_df[party] == 0, "RegioNaam"].tolist()
        if zero_regions:
            results.append({"party": party, "regions_with_zero_votes": zero_regions})
    return {"count": len(results), "data": results}


@app.get("/elections/region/{region_name}", summary="Full results for one region")
def get_region(region_name: str):
    row = _df[_df["RegioNaam"].str.lower() == region_name.lower()]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"Region '{region_name}' not found")
    record = row.iloc[0].to_dict()
    return record
