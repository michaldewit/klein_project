# HTTP Methods and Status Codes

## HTTP Methods

HTTP methods tell the server **what action to perform** on a resource. Think of them as verbs.

### GET — Read

Use `GET` to retrieve data. It should never change anything on the server.

```
GET /items          → returns a list of all items
GET /items/42       → returns the item with id 42
```

### POST — Create

Use `POST` to create a new resource. Send the new data in the request body.

```
POST /items         → creates a new item (body contains the item data)
POST /login         → sends credentials to start a session
POST /token         → sends credentials to get a JWT token
```

### PUT — Full Update

Use `PUT` to replace an existing resource entirely. You must send all fields.

```
PUT /items/42       → replace item 42 with the data in the body
```

If you only send `{"name": "Apple"}` with PUT, the other fields (price, stock) would be wiped out or set to defaults.

### PATCH — Partial Update

Use `PATCH` to update only the fields you provide. Fields you omit are left unchanged.

```
PATCH /items/42     → update only the fields provided (e.g. just the price)
PATCH /books/7/checkout  → a specific action on a resource
```

### DELETE — Delete

Use `DELETE` to remove a resource.

```
DELETE /items/42    → delete item 42
DELETE /cart/items/Apple  → remove Apple from the cart
```

---

## HTTP Status Codes

Status codes are 3-digit numbers in every response. They tell you whether the request succeeded and why.

### 2xx — Success

| Code | Name | Meaning |
|------|------|---------|
| **200** | OK | Standard success. Used for GET, PATCH, PUT. |
| **201** | Created | A new resource was created. Used after successful POST. The new resource is in the body. |
| **202** | Accepted | Request accepted, but work is still in progress (used for background jobs). |
| **204** | No Content | Success, but there is nothing to return. Used after DELETE. |

### 4xx — Client Error (You made a mistake)

| Code | Name | Meaning |
|------|------|---------|
| **400** | Bad Request | The request is malformed or makes no logical sense. |
| **401** | Unauthorized | You are not authenticated — send credentials first. |
| **403** | Forbidden | You are authenticated but not allowed to do this. |
| **404** | Not Found | The resource does not exist. |
| **409** | Conflict | The request conflicts with the current state (e.g. trying to check out an already checked-out book). |
| **422** | Unprocessable Entity | The data structure is right but the values are invalid (FastAPI uses this for validation failures). |

### 5xx — Server Error (The server made a mistake)

| Code | Name | Meaning |
|------|------|---------|
| **500** | Internal Server Error | Something went wrong in the server code. |

---

## 401 vs 403 — A Common Confusion

These two are easy to mix up:

- **401 Unauthorized** = "I do not know who you are." You have not provided credentials, or your credentials are wrong. *Fix: log in.*
- **403 Forbidden** = "I know who you are, but you cannot do this." You are logged in but your role does not permit this action. *Fix: use a different account with more permissions.*

Example with API 4:

```
GET /admin/notes  (no key header)      → 401  (who are you?)
GET /admin/notes  (X-API-Key: reader)  → 403  (I know you, but readers cannot do this)
GET /admin/notes  (X-API-Key: admin)   → 200  (welcome, admin)
```

---

## How FastAPI Maps Python to HTTP

In FastAPI, the decorator tells the framework which HTTP method and path to use:

```python
@app.get("/items")          # GET /items
def list_items():
    ...

@app.post("/items")         # POST /items
def create_item(body: ItemCreate):
    ...

@app.delete("/items/{id}")  # DELETE /items/42 (when id=42)
def delete_item(id: int):
    ...
```

To return a specific status code other than 200, pass `status_code` to the decorator:

```python
@app.post("/items", status_code=201)   # returns 201 Created
def create_item(body: ItemCreate):
    ...

@app.delete("/items/{id}", status_code=204)  # returns 204 No Content
def delete_item(id: int):
    ...
```

To return an error, raise `HTTPException`:

```python
from fastapi import HTTPException

if item_id not in _store:
    raise HTTPException(status_code=404, detail="Item not found")
```
