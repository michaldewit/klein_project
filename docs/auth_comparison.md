# Authentication Methods Compared

After working through APIs 4–8, you have implemented four different authentication methods. This guide compares them side-by-side so you can choose the right one for your next project.

---

## At a Glance

| | API Key (API 4) | HTTP Basic (API 6) | JWT / OAuth2 (API 7) | Session Cookie (API 8) |
|--|--|--|--|--|
| **Credential sent per request** | Yes (header) | Yes (header) | Token only (no password) | No (just a cookie ID) |
| **Server stores state** | No | No | No (stateless) | Yes (`_sessions` dict) |
| **Expiry** | Never (until rotated) | Never | Yes (30 min by default) | Until logout |
| **Real logout possible** | Revoke the key | No | No (wait for expiry) | Yes — instant |
| **Browser-friendly** | No | Limited | Yes (with JS) | Yes (native) |
| **Complexity** | Low | Low | High | Medium |
| **Postman setup** | Headers tab | Auth → Basic Auth | POST /token → Bearer Token | Cookies (automatic) |

---

## Detailed Comparison

### API Key Authentication

API keys are the simplest method. You generate a long random string, give it to trusted clients, and they include it in a header. The server looks up the key in a dictionary or database.

**When to use it:**
- Server-to-server communication (one backend calls another)
- Simple scripts and automation tools
- When users are developers, not end users

**When NOT to use it:**
- Browser-based applications (users cannot safely store API keys in JavaScript)
- When you need per-user identities (API keys typically represent applications, not people)

**Example flow:**
```
Client → GET /data  (X-API-Key: secret-key-abc)
Server → look up "secret-key-abc" → role: admin → 200 OK
```

---

### HTTP Basic Authentication

Basic Auth sends the username and password encoded in Base64 on every single request. The browser stores the credentials and sends them automatically, similar to cookies.

**When to use it:**
- Simple internal tools where you control the client
- CI/CD webhook endpoints
- Quick demos and prototypes

**When NOT to use it:**
- Any public-facing application (password goes over the wire every time)
- When you need logout (you cannot clear credentials from a browser without tricks)
- When you need per-session state

**Key technical detail:** `secrets.compare_digest()` — always use this instead of `==` to compare passwords. The `==` operator short-circuits when it finds the first mismatch, which leaks timing information that attackers can exploit.

**Example flow:**
```
Client → GET /books  (Authorization: Basic YWxpY2U6YWxpY2VwYXNz)
Server → decode Base64 → "alice:alicepass" → check USERS dict → 200 OK
```

---

### JWT / OAuth2 Token Authentication

The OAuth2 Password Flow exchanges credentials once for a short-lived token. The token is self-contained — it encodes the username and role inside it — so the server can verify it without looking anything up in a database.

**When to use it:**
- Public REST APIs used by mobile apps or single-page applications
- Microservices architectures where many services need to authenticate users
- When you need token expiry and role-based access
- When you care about performance (no database lookup per request)

**When NOT to use it:**
- When you need instant logout (you cannot invalidate a JWT before it expires without adding a database)
- Very simple use cases where the added complexity is not worth it

**Example flow:**
```
Client → POST /token  (username=alice&password=alice123)
Server → verify password → create JWT → return {"access_token": "eyJ..."}

Client → GET /notes  (Authorization: Bearer eyJ...)
Server → decode JWT → verify signature → check exp → extract username → 200 OK
```

---

### Session Cookie Authentication

Sessions store state on the server. The client receives only an opaque session ID in a cookie. The browser sends this cookie automatically with every request, and the server looks up who the session ID belongs to.

**When to use it:**
- Traditional web applications with server-rendered HTML
- When you need instant logout (delete the session ID from the server)
- Shopping carts, user preferences, and other per-user server-side state
- When you want the browser to handle credentials automatically

**When NOT to use it:**
- Stateless APIs called by mobile apps (cookies are a browser concept)
- When you need to scale across many servers (sessions must be shared, e.g. via Redis)

**Example flow:**
```
Client → POST /login  (username=alice&password=alicepass)
Server → verify → generate session_id → store in _sessions → Set-Cookie: session=abc

Client → GET /cart  (Cookie: session=abc  ← browser adds automatically)
Server → read session cookie → look up "abc" in _sessions → "alice" → 200 OK

Client → POST /logout
Server → delete "abc" from _sessions → cookie useless now → 200 OK
```

---

## Real-World Combinations

Most production systems use **multiple methods simultaneously**:

- **API key** for machine-to-machine communication (your payment service calls your order service)
- **JWT** for authenticated users via mobile or browser JavaScript
- **Session cookie** for server-rendered web pages

For example, a banking application might use:
- Cookies for the web interface (easy, browser-native)
- JWT tokens for the mobile app (stateless, works across servers)
- API keys for internal microservices talking to each other

---

## Security Basics (All Methods)

Regardless of which method you choose:

1. **Always use HTTPS in production.** All four methods send credentials in plain text over HTTP. HTTPS encrypts the connection, protecting credentials from eavesdropping.

2. **Never log credentials.** Access logs should not contain passwords, API keys, or tokens. Sanitise log output.

3. **Rotate secrets regularly.** API keys, JWT secret keys, and session secret keys should be rotated periodically and immediately if leaked.

4. **Use environment variables for secrets.** Never hardcode `SECRET_KEY = "..."` in code that goes to version control. Use `os.environ.get("SECRET_KEY")` and store real values in `.env` files or secrets managers.

5. **Set appropriate expiry.** Tokens and sessions should expire. Short-lived tokens (15–60 minutes) limit damage from theft.

---

## Quick Decision Guide

```
Is this for a browser-based web app?
├── Yes, server renders HTML → Session Cookies (API 8)
└── Yes, JavaScript SPA/mobile → JWT/OAuth2 (API 7)

Is this for server-to-server (no humans)?
├── Simple internal tool → API Key (API 4)
└── Already have a user system → JWT with service accounts

Do you need instant logout?
├── Yes → Session Cookies (API 8)
└── No → JWT is fine (API 7)

Is this a quick prototype or internal script?
└── HTTP Basic Auth (API 6) — simplest to set up
```
