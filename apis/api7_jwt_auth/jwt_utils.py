"""
Pure-Python JWT implementation using only the standard library.

This is intentionally simple and educational — it shows exactly how JWTs work:
  1. Encode header and payload as JSON, then base64url-encode them
  2. Create a HMAC-SHA256 signature over "header.payload"
  3. Return "header.payload.signature"

Only HS256 (HMAC-SHA256) is supported, which is the most common algorithm for
server-side tokens where the same secret signs and verifies.
"""

import base64
import hashlib
import hmac
import json
import time


class JWTError(Exception):
    """Raised when a token is invalid, expired, or tampered with."""


def _b64url_encode(data: bytes) -> str:
    """Base64url encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    """Base64url decode, adding back padding as needed."""
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def encode(payload: dict, secret: str, algorithm: str = "HS256") -> str:
    """Create a signed JWT string."""
    header = {"alg": algorithm, "typ": "JWT"}
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    message = f"{header_b64}.{payload_b64}".encode()
    sig = hmac.new(secret.encode(), message, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(sig)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode(token: str, secret: str, algorithms: list[str] | None = None) -> dict:
    """Verify and decode a JWT. Raises JWTError on any failure."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise JWTError("Token must have three parts")
        header_b64, payload_b64, sig_b64 = parts

        # Verify signature
        message = f"{header_b64}.{payload_b64}".encode()
        expected_sig = hmac.new(secret.encode(), message, hashlib.sha256).digest()
        actual_sig = _b64url_decode(sig_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            raise JWTError("Signature verification failed")

        # Decode payload
        payload = json.loads(_b64url_decode(payload_b64))

        # Check expiry
        exp = payload.get("exp")
        if exp is not None and time.time() > exp:
            raise JWTError("Token has expired")

        return payload
    except JWTError:
        raise
    except Exception as exc:
        raise JWTError(f"Token decode failed: {exc}") from exc
