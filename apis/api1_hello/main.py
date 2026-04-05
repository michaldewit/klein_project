"""
API 1 - Hello World REST API
Goal: Learn routes, HTTP methods, path/query params, request body, JSON responses.

Endpoints:
  GET  /           - welcome message
  GET  /hello/{name} - personalized greeting with optional lang query param
  POST /echo       - echoes back whatever JSON body is sent
"""

from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Any

app = FastAPI(
    title="API 1 - Hello World",
    description="Learn the basics of REST: routes, methods, params, and JSON bodies.",
    version="1.0.0",
)


class EchoBody(BaseModel):
    # Accepts any key/value pairs
    data: dict[str, Any]


@app.get("/", summary="Welcome message")
def root():
    """Returns a welcome message."""
    return {"message": "Welcome to API 1 - Hello World!"}


@app.get("/hello/{name}", summary="Personalized greeting")
def hello(
    name: str,
    lang: str = Query(default="en", description="Language: 'en' or 'nl'"),
):
    """
    Returns a greeting for {name}.
    - Path param : name
    - Query param: lang (en/nl)
    """
    greetings = {
        "en": f"Hello, {name}!",
        "nl": f"Hallo, {name}!",
    }
    message = greetings.get(lang, greetings["en"])
    return {"message": message, "name": name, "lang": lang}


@app.post("/echo", summary="Echo JSON body", status_code=200)
def echo(body: EchoBody):
    """Receives a JSON body and echoes it back with a timestamp note."""
    return {
        "echoed": body.data,
        "keys_received": list(body.data.keys()),
        "count": len(body.data),
    }
