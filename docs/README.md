# Python API Learning Project

A hands-on guide to building REST APIs in Python with FastAPI. You will build 8 progressively complex APIs, each teaching a new concept — starting from "what is a route?" and ending with production authentication patterns.

---

## Prerequisites

- Python 3.11+
- Basic Python knowledge (functions, dictionaries, loops)
- Postman installed (see [How to Use Postman](./00_intro/how_to_use_postman.md))

## Installation

```bash
# From the project root
pip install fastapi uvicorn pytest httpx pandas python-multipart itsdangerous bcrypt
```

---

## Learning Path

Work through the APIs in order. Each one builds on what came before.

| # | API | Concept | Run on port |
|---|-----|---------|-------------|
| 0 | Intro | What is an API? HTTP, JSON, Postman | — |
| 1 | [Hello World](./01_hello_world/explanation.md) | Routes, path params, query params, POST body | 8001 |
| 2 | [CRUD Items](./02_crud/explanation.md) | GET/POST/PUT/PATCH/DELETE, status codes, validation | 8002 |
| 3 | [Election Data](./03_elections/explanation.md) | Real data, pandas, filtering, pagination | 8003 |
| 4 | [API Key Auth](./04_api_key_auth/explanation.md) | Headers, API keys, roles, `Depends()` | 8004 |
| 5 | [Background Tasks](./05_background_tasks/explanation.md) | Async jobs, polling, file persistence | 8005 |
| 6 | [HTTP Basic Auth](./06_basic_auth/explanation.md) | Basic Auth, `secrets.compare_digest`, browser dialogs | 8006 |
| 7 | [JWT Auth](./07_jwt_auth/explanation.md) | OAuth2, JWT tokens, bcrypt, stateless auth | 8007 |
| 8 | [Session Auth](./08_session_auth/explanation.md) | Session cookies, stateful auth, instant logout | 8008 |

After completing APIs 4–8, read [Authentication Methods Compared](./auth_comparison.md) to understand when to use each.

---

## Start to Read

**New to APIs?** Start here:

1. [What is an API?](./00_intro/what_is_an_api.md)
2. [HTTP Methods and Status Codes](./00_intro/http_methods_and_status.md)
3. [JSON and Pydantic](./00_intro/json_and_pydantic.md)
4. [How to Use Postman](./00_intro/how_to_use_postman.md)

Then work through each API's `explanation.md` and `exercises.md`.

---

## Running an API

```bash
# Replace N with the API number (1–8)
uvicorn apis.apiN_name.main:app --reload --port 800N

# Examples:
uvicorn apis.api1_hello.main:app --reload --port 8001
uvicorn apis.api2_crud.main:app --reload --port 8002
uvicorn apis.api3_elections.main:app --reload --port 8003
uvicorn apis.api4_auth.main:app --reload --port 8004
uvicorn apis.api5_background.main:app --reload --port 8005
uvicorn apis.api6_basic_auth.main:app --reload --port 8006
uvicorn apis.api7_jwt_auth.main:app --reload --port 8007
uvicorn apis.api8_session_auth.main:app --reload --port 8008
```

Each API also serves **interactive documentation** (Swagger UI) at `http://127.0.0.1:800N/docs`.
API 7 has a built-in **Authorize** button in Swagger UI for testing OAuth2 directly in the browser.

---

## Running Tests

```bash
# All tests
python -m pytest apis/ -v

# One API at a time
python -m pytest apis/api1_hello/test_api1.py -v
python -m pytest apis/api2_crud/test_api2.py -v
python -m pytest apis/api3_elections/test_api3.py -v
python -m pytest apis/api4_auth/test_api4.py -v
python -m pytest apis/api5_background/test_api5.py -v
python -m pytest apis/api6_basic_auth/test_api6.py -v
python -m pytest apis/api7_jwt_auth/test_api7.py -v
python -m pytest apis/api8_session_auth/test_api8.py -v
```

---

## Project Structure

```
klein_project/
├── docs/                          ← You are here
│   ├── README.md                  ← This file
│   ├── 00_intro/                  ← Foundational concepts
│   ├── 01_hello_world/            ← API 1 docs + exercises
│   ├── 02_crud/                   ← API 2 docs + exercises
│   ├── 03_elections/              ← API 3 docs + exercises
│   ├── 04_api_key_auth/           ← API 4 docs + exercises
│   ├── 05_background_tasks/       ← API 5 docs + exercises
│   ├── 06_basic_auth/             ← API 6 docs + exercises
│   ├── 07_jwt_auth/               ← API 7 docs + exercises
│   ├── 08_session_auth/           ← API 8 docs + exercises
│   └── auth_comparison.md         ← Side-by-side auth guide
│
├── apis/
│   ├── api1_hello/                ← main.py + test_api1.py
│   ├── api2_crud/                 ← main.py + test_api2.py
│   ├── api3_elections/            ← main.py + test_api3.py
│   ├── api4_auth/                 ← main.py + test_api4.py
│   ├── api5_background/           ← main.py + test_api5.py
│   ├── api6_basic_auth/           ← main.py + test_api6.py
│   ├── api7_jwt_auth/             ← main.py + jwt_utils.py + test_api7.py
│   └── api8_session_auth/         ← main.py + test_api8.py
│
└── uitslagen.csv                  ← Dutch 2021 election data (used by API 3)
```

---

## Test Credentials

| API | Username | Password | Role |
|-----|----------|----------|------|
| API 4 (key) | — | `reader-key-123` | reader |
| API 4 (key) | — | `admin-key-456` | admin |
| API 6 (Basic) | alice | alicepass | reader |
| API 6 (Basic) | bob | bobpass | reader |
| API 6 (Basic) | admin | adminpass | librarian |
| API 7 (JWT) | alice | alice123 | user |
| API 7 (JWT) | bob | bob123 | user |
| API 7 (JWT) | admin | admin123 | admin |
| API 8 (Session) | alice | alicepass | — |
| API 8 (Session) | bob | bobpass | — |
