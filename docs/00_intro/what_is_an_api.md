# What is an API?

## The Short Answer

An **API** (Application Programming Interface) is a way for two programs to talk to each other.

You have probably used APIs without knowing it. Every time you open a weather app, the app asks a weather server "what is the temperature today?" and the server sends back a number. That conversation uses an API.

---

## A Better Analogy: The Restaurant

Think of a restaurant:

- **You** are the client — you want food.
- **The kitchen** is the server — it prepares the food.
- **The waiter** is the API — it carries your request to the kitchen and brings back the result.

You do not go into the kitchen yourself. You tell the waiter what you want, the waiter tells the kitchen, and the waiter brings your food back. The API works the same way — it defines a clear set of requests you can make and what you get back.

---

## What is a REST API?

**REST** (Representational State Transfer) is a set of rules for designing APIs over the internet. Almost every web API you will work with uses REST.

The key ideas of REST:

1. **Resources** — Everything is a "thing" (resource). Users, books, items, notes. Each resource has its own URL.
   - `/users` — the collection of all users
   - `/users/42` — the user with ID 42
   - `/books/7/checkout` — the checkout action for book 7

2. **HTTP methods** tell the server what to do with a resource:
   - `GET` — read something
   - `POST` — create something
   - `PUT` / `PATCH` — update something
   - `DELETE` — delete something

3. **Stateless** — Each request is independent. The server does not remember the previous request. Every request must contain all the information the server needs.

4. **JSON responses** — The server almost always responds with JSON (JavaScript Object Notation), a simple text format for structured data.

---

## What is HTTP?

HTTP (HyperText Transfer Protocol) is the language of the web. When your browser visits a website, it sends an **HTTP request** and gets back an **HTTP response**.

A request has:
- A **method** (GET, POST, etc.)
- A **URL** (the address)
- **Headers** (extra information, like your identity or what format you accept)
- A **body** (optional data you send, usually JSON on POST/PUT)

A response has:
- A **status code** (a number saying what happened — 200 = OK, 404 = not found)
- **Headers** (extra information from the server)
- A **body** (the data the server sends back, usually JSON)

---

## What is FastAPI?

**FastAPI** is a Python web framework for building APIs quickly and correctly. It is what all 8 APIs in this project are built with.

Why FastAPI?

- **Automatic validation** — if you send bad data, it rejects it automatically with a helpful error
- **Automatic documentation** — visit `/docs` on any running API and you get an interactive page where you can test every endpoint in your browser
- **Modern Python** — uses Python type hints, which makes the code readable and catches errors early
- **Fast** — one of the fastest Python frameworks available

---

## What You Will Build in This Project

You will work through 8 APIs, each teaching a new concept:

| API | What you build | What you learn |
|-----|---------------|----------------|
| 1 | Hello World | Routes, path params, query params, POST body |
| 2 | Item Store | Full CRUD, status codes, validation |
| 3 | Election Data | Real data, pandas, filtering, aggregation |
| 4 | API Key Auth | Headers, roles, 401 vs 403, dependency injection |
| 5 | Job Queue | Background tasks, polling, file persistence |
| 6 | Library Books | HTTP Basic Auth, browser login dialogs |
| 7 | Personal Notes | OAuth2, JWT tokens, stateless auth |
| 8 | Shopping Cart | Session cookies, stateful auth, logout |

Start with API 1. Each API builds on what you learned in the previous one.

---

## Next Steps

- Read [HTTP Methods and Status Codes](./http_methods_and_status.md) to learn the vocabulary of REST
- Read [JSON and Pydantic](./json_and_pydantic.md) to understand how data is structured
- Read [How to Use Postman](./how_to_use_postman.md) to learn how to test APIs interactively
