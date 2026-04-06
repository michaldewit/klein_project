# Exercises — API 3: Election Data

Run the API while working: `uvicorn apis.api3_elections.main:app --reload --port 8003`

---

## Exercise 1 (Easy) — Top 5 parties nationally

**Task:** Add `GET /elections/top5` that returns the 5 parties with the most total votes across all 355 municipalities.

**Hint:** Reuse the logic from `GET /elections/summary`. A pandas `Series` has a `.head(N)` method and `.to_dict()`.

<details>
<summary>Answer</summary>

```python
@app.get("/elections/top5", summary="Top 5 parties by national vote total")
def get_top5():
    party_cols = get_party_columns(_df)
    top5 = _df[party_cols].sum().sort_values(ascending=False).head(5)
    return {"top5": top5.to_dict()}
```

**Test it:** `GET /elections/top5` — you should see VVD, D66, PVV near the top.

</details>

---

## Exercise 2 (Medium) — Minimum votes filter

**Task:** Add a `min_votes` query parameter (integer, optional, default `0`) to `GET /elections/results?party=VVD`. When provided, only return regions where that party got **at least** that many votes.

Example: `GET /elections/results?party=VVD&min_votes=5000` returns only large cities.

**Hint:** After finding the matched party column, add a second boolean filter on the DataFrame.

<details>
<summary>Answer</summary>

```python
@app.get("/elections/results")
def get_results(
    party: Optional[str] = Query(default=None),
    region: Optional[str] = Query(default=None),
    min_votes: int = Query(default=0, ge=0),      # ← add this
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
        if min_votes > 0:                           # ← add this block
            df = df[df[matched] >= min_votes]
        cols = ["RegioNaam"] + [matched]
        return df[cols].to_dict(orient="records")

    return df[["RegioNaam"] + get_party_columns(_df)].to_dict(orient="records")
```

**Test it:** `GET /elections/results?party=VVD&min_votes=5000` — should return only large urban municipalities.

</details>

---

## Exercise 3 (Medium) — Compare two parties

**Task:** Add `GET /elections/compare?party1=VVD&party2=D66` that returns all 355 municipalities with the vote counts for both parties side-by-side.

Both `party1` and `party2` should be required (no default). Return 404 if either party name is unknown.

**Hint:** You need to look up both party names (case-insensitive) and return `df[["RegioNaam", matched1, matched2]]`.

<details>
<summary>Answer</summary>

```python
@app.get("/elections/compare", summary="Compare two parties side by side")
def compare_parties(
    party1: str = Query(..., description="First party name"),
    party2: str = Query(..., description="Second party name"),
):
    party_cols = get_party_columns(_df)

    matched1 = next((c for c in party_cols if c.lower() == party1.lower()), None)
    if not matched1:
        raise HTTPException(status_code=404, detail=f"Party '{party1}' not found")

    matched2 = next((c for c in party_cols if c.lower() == party2.lower()), None)
    if not matched2:
        raise HTTPException(status_code=404, detail=f"Party '{party2}' not found")

    cols = ["RegioNaam", matched1, matched2]
    return _df[cols].to_dict(orient="records")
```

**Test it:** `GET /elections/compare?party1=VVD&party2=D66`

</details>

---

## Exercise 4 (Hard) — Who won each municipality?

**Task:** Add `GET /elections/winner` that returns, for every municipality, the name of the party that got the most votes.

The response should be a list of objects like:
```json
[
  {"region": "Aalsmeer", "winner": "VVD"},
  {"region": "Aalten", "winner": "CDA"},
  ...
]
```

**Hint:** Use `pandas.DataFrame.idxmax(axis=1)` — this returns the column name with the highest value for each row. Pair it with `_df["RegioNaam"]`.

<details>
<summary>Answer</summary>

```python
@app.get("/elections/winner", summary="Winning party per municipality")
def get_winners():
    party_cols = get_party_columns(_df)
    # idxmax(axis=1) returns the column name of the maximum value per row
    winners = _df[party_cols].idxmax(axis=1)
    result = [
        {"region": region, "winner": winner}
        for region, winner in zip(_df["RegioNaam"], winners)
    ]
    return result
```

**Test it:** `GET /elections/winner` — you should see VVD winning in many western municipalities and CDA or PVV winning in others.

**Interesting follow-up question:** Which party won the most municipalities? You can find out with:
```python
from collections import Counter
Counter(r["winner"] for r in result).most_common(5)
```

</details>
