# API 1 — Exercises

These exercises build directly on the code in `apis/api1_hello/main.py`. Read the explanation first, then try each exercise on your own before peeking at the answer.

A good approach: keep the server running with `uvicorn main:app --reload` so every save you make is live-reloaded.

---

## Exercise 1 — Add German (Easy)

**Task:** The `/hello/{name}` endpoint currently supports `?lang=en` and `?lang=nl`. Add support for German so that `GET /hello/Alice?lang=de` returns:

```json
{"message": "Guten Tag, Alice!", "name": "Alice", "lang": "de"}
```

**Hint:** Look at how `"nl"` was added to the `greetings` dictionary inside the `hello` function. You only need to add one line.

<details>
<summary>Answer</summary>

Find the `greetings` dictionary in the `hello` function and add a `"de"` entry:

```python
@app.get("/hello/{name}", summary="Personalized greeting")
def hello(
    name: str,
    lang: str = Query(default="en", description="Language: 'en', 'nl', or 'de'"),
):
    greetings = {
        "en": f"Hello, {name}!",
        "nl": f"Hallo, {name}!",
        "de": f"Guten Tag, {name}!",   # ← add this line
    }
    message = greetings.get(lang, greetings["en"])
    return {"message": message, "name": name, "lang": lang}
```

That is all. Test it:

```
GET /hello/Alice?lang=de
→ {"message": "Guten Tag, Alice!", "name": "Alice", "lang": "de"}
```

</details>

---

## Exercise 2 — Add a Goodbye Route (Easy)

**Task:** Add a new endpoint `GET /goodbye/{name}` that returns:

```json
{"message": "Goodbye, Alice!"}
```

**Hint:** Copy the structure of the `root()` function (for the decorator pattern) and the `hello()` function (for the path parameter). You only need one of those two techniques here.

<details>
<summary>Answer</summary>

Add this function anywhere below the `app = FastAPI(...)` line:

```python
@app.get("/goodbye/{name}", summary="Goodbye message")
def goodbye(name: str):
    """Returns a farewell message for the given name."""
    return {"message": f"Goodbye, {name}!"}
```

Test it:

```
GET /goodbye/Alice
→ {"message": "Goodbye, Alice!"}
```

</details>

---

## Exercise 3 — Formal Farewell (Medium)

**Task:** Extend `GET /goodbye/{name}` with an optional query parameter `formal`. When `?formal=true` is passed, respond with `"Farewell, {name}."`. When it is absent (or anything other than `true`), respond with `"Bye, {name}!"`.

Expected behaviour:

```
GET /goodbye/Alice              → {"message": "Bye, Alice!"}
GET /goodbye/Alice?formal=true  → {"message": "Farewell, Alice."}
GET /goodbye/Alice?formal=false → {"message": "Bye, Alice!"}
```

**Hint:** FastAPI can automatically parse `bool` query parameters. Declare the parameter as `formal: bool = Query(default=False)` and FastAPI will accept `true`/`false`/`1`/`0` from the URL and give you a real Python `bool`.

<details>
<summary>Answer</summary>

Update the `goodbye` function you created in Exercise 2:

```python
@app.get("/goodbye/{name}", summary="Goodbye message")
def goodbye(
    name: str,
    formal: bool = Query(default=False, description="Use formal language"),
):
    """Returns a farewell message. Pass ?formal=true for a formal tone."""
    if formal:
        message = f"Farewell, {name}."
    else:
        message = f"Bye, {name}!"
    return {"message": message}
```

Test it in Postman:

1. `GET /goodbye/Alice` — no params → `{"message": "Bye, Alice!"}`
2. Add param `formal = true` → `{"message": "Farewell, Alice."}`
3. Change to `formal = false` → back to `{"message": "Bye, Alice!"}`

</details>

---

## Exercise 4 — Calculator Endpoint (Medium)

**Task:** Add a `POST /calculate` endpoint. It accepts a JSON body with two numbers and returns four computed values.

**Request body:**

```json
{"a": 10, "b": 3}
```

**Expected response:**

```json
{"sum": 13, "product": 30, "difference": 7}
```

**Hint:** You need to:
1. Create a new Pydantic model (e.g. `CalcBody`) with fields `a: float` and `b: float`.
2. Write a `POST /calculate` function that receives `body: CalcBody` and returns the computed values.

Use `float` rather than `int` for the model fields so the endpoint also works for decimal numbers like `{"a": 2.5, "b": 1.5}`.

<details>
<summary>Answer</summary>

First, add the request body model near the top of the file with the other models:

```python
class CalcBody(BaseModel):
    a: float
    b: float
```

Then add the endpoint:

```python
@app.post("/calculate", summary="Basic arithmetic")
def calculate(body: CalcBody):
    """Performs basic arithmetic on two numbers."""
    return {
        "sum":        body.a + body.b,
        "product":    body.a * body.b,
        "difference": body.a - body.b,
    }
```

Test it in Postman:

1. Method: **POST**, URL: `http://localhost:8000/calculate`
2. Body → raw → JSON:
   ```json
   {"a": 10, "b": 3}
   ```
3. Expected response:
   ```json
   {"sum": 13.0, "product": 30.0, "difference": 7.0}
   ```

**Bonus challenge:** What happens if you send `{"a": "ten", "b": 3}`? FastAPI returns a 422 error because `"ten"` cannot be converted to a `float`. You get this validation for free because of the Pydantic model.

</details>
