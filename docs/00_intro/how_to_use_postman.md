# How to Use Postman

Postman is a desktop application for sending HTTP requests to APIs. It is the best way to test your APIs without writing code.

## Installing Postman

1. Go to [https://www.postman.com/downloads/](https://www.postman.com/downloads/)
2. Download and install for your operating system
3. Create a free account (or skip — you can use it without one)

---

## Starting an API

Before testing in Postman, you need to run the API locally. Open a terminal in the project folder and run:

```bash
# API 1 on port 8001
uvicorn apis.api1_hello.main:app --reload --port 8001

# API 2 on port 8002
uvicorn apis.api2_crud.main:app --reload --port 8002

# ... and so on for each API
```

The `--reload` flag automatically restarts the server when you save a file.

You can also view auto-generated docs in your browser at `http://127.0.0.1:8001/docs`.

---

## Creating a Collection

A **collection** is a folder that groups related requests together. Create one for each API:

1. Click **Collections** in the left sidebar
2. Click **+** (New Collection)
3. Name it, e.g. "API 1 - Hello World"
4. Click **Create**

---

## Making a GET Request

1. Click **+** to open a new request tab
2. Make sure the dropdown says **GET**
3. Enter the URL: `http://127.0.0.1:8001/`
4. Click **Send**
5. You will see the response at the bottom:
   - **Status**: `200 OK`
   - **Body**: `{"message": "Welcome to API 1 - Hello World!"}`

### Adding Query Parameters

For `GET /hello/Alice?lang=nl`:

1. Enter URL: `http://127.0.0.1:8001/hello/Alice`
2. Click the **Params** tab below the URL bar
3. Add a row: Key = `lang`, Value = `nl`
4. The URL updates automatically to include `?lang=nl`
5. Click **Send**

---

## Making a POST Request (with JSON body)

For `POST /echo` with a JSON body:

1. Change the dropdown to **POST**
2. Enter URL: `http://127.0.0.1:8001/echo`
3. Click the **Body** tab
4. Select **raw** and change the format dropdown to **JSON**
5. Type your JSON:
   ```json
   {
     "data": {
       "fruit": "apple",
       "color": "red"
     }
   }
   ```
6. Click **Send**

---

## Adding Headers

For APIs that require an API key header (API 4):

1. Click the **Headers** tab
2. Add a row: Key = `X-API-Key`, Value = `reader-key-123`
3. Click **Send**

---

## The Authorization Tab

Postman has a dedicated tab for common authentication patterns. This is much easier than manually typing headers.

### Basic Auth (API 6)

1. Click the **Auth** tab
2. Select **Basic Auth** from the dropdown
3. Enter **Username** and **Password**
4. Postman automatically adds the `Authorization: Basic <base64>` header

### Bearer Token (API 7 — JWT)

After getting a token from `POST /token`:

1. Click the **Auth** tab
2. Select **Bearer Token**
3. Paste your token in the **Token** field
4. Postman adds `Authorization: Bearer <your-token>` to every request

### Cookies (API 8 — Sessions)

When you log in via `POST /login`, Postman automatically stores the session cookie. Subsequent requests in the same session will include it automatically.

To see cookies:
1. After a request, click **Cookies** (bottom right of the response panel)

---

## Sending Form Data (for POST /login and POST /token)

Some endpoints accept **form data** instead of JSON (login endpoints in APIs 7 and 8):

1. Click **Body**
2. Select **x-www-form-urlencoded** (not `raw`)
3. Add rows:
   - Key: `username`, Value: `alice`
   - Key: `password`, Value: `alice123`
4. Click **Send**

---

## Saving Requests in a Collection

1. After configuring a request, click **Save** (top right)
2. Give it a name, e.g. "GET all items"
3. Select the collection to save it in
4. Click **Save**

Now you can re-run it any time without re-typing everything.

---

## Using Environment Variables

Instead of hardcoding `http://127.0.0.1:8001` in every request, use a variable:

1. Click the **Environments** tab (globe icon, top right)
2. Click **+** to create a new environment
3. Add a variable: Name = `base_url`, Initial Value = `http://127.0.0.1:8001`
4. In your request URLs, use `{{base_url}}/hello/Alice`
5. When switching APIs, just update `base_url`

---

## Reading the Response

After clicking Send:

- **Status code** (top right of response): `200 OK`, `404 Not Found`, etc.
- **Body tab**: The JSON the server sent back
- **Headers tab**: Response headers (useful for seeing `Set-Cookie` in API 8)
- **Time**: How long the request took in milliseconds

If you get a `422 Unprocessable Entity`, click the **Body** tab on the response — FastAPI tells you exactly which field failed validation and why.
