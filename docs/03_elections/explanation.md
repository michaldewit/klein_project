# API 3 — Election Data API

## What You Will Learn

- How to load a real CSV dataset into a pandas DataFrame at startup
- How to use pandas filtering inside FastAPI route handlers
- How to build query parameters that filter large datasets
- How to aggregate data (sum votes, find winners) and return the results as JSON

---

## Running the API

```bash
uvicorn apis.api3_elections.main:app --reload --port 8003
```

Visit `http://127.0.0.1:8003/docs` to explore the endpoints interactively.

---

## The Dataset

The file `uitslagen.csv` contains the results of the **2021 Dutch national election** for all 355 municipalities in the Netherlands.

Each row is one municipality. The columns are:
- **Metadata columns** — `RegioNaam` (municipality name), `RegioCode`, `OuderRegioNaam` (province), `Kiesgerechtigden` (eligible voters), `Opkomst` (turnout), etc.
- **Party columns** — one column per party: `VVD`, `D66`, `PVV (Partij voor de Vrijheid)`, `CDA`, `GROENLINKS`, and many more

---

## Why Load Data Once at Startup?

Reading a CSV file from disk takes time. If you loaded it on every request, every API call would be slow:

```python
# BAD — reads disk on every single request
@app.get("/elections")
def list_elections():
    df = pd.read_csv("uitslagen.csv", sep=";")  # slow!
    return df.head(50).to_dict(orient="records")
```

Instead, load the data **once** when the module is imported:

```python
# GOOD — reads disk once when the server starts
_df: pd.DataFrame = load_data()   # module-level variable

@app.get("/elections")
def list_elections():
    return _df[_META_COLS].head(50).to_dict(orient="records")  # fast!
```

The `_df` variable is loaded when Python imports `main.py`. All requests share the same in-memory DataFrame.

---

## Separating Metadata from Party Columns

The CSV has two kinds of columns. The code separates them with a constant list:

```python
_META_COLS = [
    "RegioNaam", "RegioCode", "AmsterdamseCode", "OuderRegioNaam",
    "OuderRegioCode", "Kiesgerechtigden", "Opkomst",
    "OngeldigeStemmen", "BlancoStemmen", "GeldigeStemmen",
]

def get_party_columns(df: pd.DataFrame) -> list[str]:
    # any column NOT in _META_COLS is a party column
    return [c for c in df.columns if c not in _META_COLS]
```

This makes it easy to iterate over parties, sum votes, etc. without hardcoding party names.

---

## Filtering a DataFrame

To filter rows where `RegioNaam` matches a user's query:

```python
region = "Aalsmeer"
filtered = df[df["RegioNaam"].str.lower() == region.lower()]
```

- `.str.lower()` converts every value in the column to lowercase
- `== region.lower()` compares to the lowercased query
- This makes the filter **case-insensitive** — `"aalsmeer"` and `"AALSMEER"` both match

After filtering, always check if anything was found:

```python
if filtered.empty:
    raise HTTPException(status_code=404, detail=f"Region '{region}' not found")
```

---

## Converting DataFrames to JSON

FastAPI returns Python objects as JSON. A pandas DataFrame is not directly JSON-serialisable, so you convert it first:

```python
df.to_dict(orient="records")
```

This produces a list of dictionaries — one per row — which FastAPI can return directly:

```python
[
  {"RegioNaam": "Aalsmeer", "VVD": 6301, "D66": 2742, ...},
  {"RegioNaam": "Aalten",   "VVD": 3782, "D66": 2045, ...},
  ...
]
```

---

## Pagination with `skip` and `limit`

For large datasets, you don't want to return all 355 rows at once. Pandas `.iloc` does slice-based indexing:

```python
skip: int = 0
limit: int = 50
subset = df.iloc[skip : skip + limit]
```

| Request | Returns |
|---------|---------|
| `GET /elections` | rows 0–49 (first 50) |
| `GET /elections?skip=50` | rows 50–99 |
| `GET /elections?skip=100&limit=10` | rows 100–109 |

---

## Aggregation: Total Votes per Party

To sum all votes for every party across all municipalities:

```python
party_cols = get_party_columns(_df)
totals = _df[party_cols].sum()          # Series: party -> total votes
totals = totals.sort_values(ascending=False)  # sort highest first
return {"totals": totals.to_dict()}
```

The result looks like:
```json
{"totals": {"VVD": 2279328, "D66": 1567278, "PVV": 1124482, ...}}
```

---

## Code Walkthrough

### `load_data()` — `main.py:20`

```python
def load_data(path: Optional[str] = None) -> pd.DataFrame:
    csv_path = Path(path) if path else _CSV_PATH
    df = pd.read_csv(csv_path, sep=";")         # semicolon-separated CSV
    party_cols = [c for c in df.columns if c not in _META_COLS]
    df[party_cols] = df[party_cols].fillna(0).astype(int)  # NaN → 0
    return df
```

`fillna(0)` replaces missing vote counts with zero (some small parties got zero votes in many municipalities). `.astype(int)` ensures all vote columns are integers.

### `GET /elections/results` — filtering by region and/or party

```python
@app.get("/elections/results")
def get_results(party: Optional[str] = None, region: Optional[str] = None):
    df = _df.copy()

    if region:
        df = df[df["RegioNaam"].str.lower() == region.lower()]
        if df.empty:
            raise HTTPException(404, ...)

    if party:
        matched = next((c for c in party_cols if c.lower() == party.lower()), None)
        if not matched:
            raise HTTPException(404, ...)
        return df[["RegioNaam", matched]].to_dict(orient="records")

    return df[["RegioNaam"] + party_cols].to_dict(orient="records")
```

Both `region` and `party` are optional. You can use neither, one, or both together.

---

## Testing in Postman

| Request | What to check |
|---------|---------------|
| `GET /elections?limit=5` | Returns exactly 5 records |
| `GET /elections/parties` | VVD and D66 are in the list |
| `GET /elections/regions` | 355 regions, sorted alphabetically |
| `GET /elections/results?region=Aalsmeer` | One record for Aalsmeer |
| `GET /elections/results?party=VVD` | One row per region, only VVD column |
| `GET /elections/results?region=FAKE` | 404 response |
| `GET /elections/summary` | VVD should be near the top |
| `GET /elections/zero-votes` | Parties with zero votes in some regions |
| `GET /elections/region/Amsterdam` | Full breakdown for Amsterdam |
