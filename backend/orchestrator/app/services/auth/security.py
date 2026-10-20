"""
File: orchestrator/app/services/auth/security.py
Description: Security utilities for PIN hashing (PBKDF2-HMAC-SHA256) and
             lightweight RFC 7519 HMAC-SHA256 JWT generation and verification.
"""

import base64
import json
import hmac
import hashlib
import time
from typing import Dict, Any, Optional


def _b64encode(data: bytes) -> str:
    """Base64url encode without padding."""
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64decode(data: str) -> bytes:
    """Base64url decode with padding compensation."""
    padding = "=" * ((4 - (len(data) % 4)) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("utf-8"))


def hash_pin(pin: str, salt: Optional[str] = None) -> str:
    """
    Hashes a 4-digit student/teacher PIN using PBKDF2-HMAC-SHA256 with 100,000 iterations.
    Format: <salt>$<hex_digest>
    """
    clean_pin = pin.strip()
    if not salt:
        salt = hashlib.sha256(f"{time.time()}:{clean_pin}".encode()).hexdigest()[:16]
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        clean_pin.encode("utf-8"),
        salt.encode("utf-8"),
        100000
    ).hex()
    return f"{salt}${hashed}"


def verify_pin(pin: str, stored_hash: str) -> bool:
    """
    Verifies a plain-text PIN against a stored salted hash.
    Constant-time comparison protects against timing attacks.
    """
    if not stored_hash or "$" not in stored_hash:
        return False
    clean_pin = pin.strip()
    salt, hashed = stored_hash.split("$", 1)
    computed = hashlib.pbkdf2_hmac(
        "sha256",
        clean_pin.encode("utf-8"),
        salt.encode("utf-8"),
        100000
    ).hex()
    return hmac.compare_digest(computed, hashed)


def create_access_token(
    payload: Dict[str, Any],
    secret_key: str,
    expires_in_seconds: int = 86400 * 30
) -> str:
    """
    Creates an RFC 7519 compliant JSON Web Token (JWT) signed with HMAC-SHA256 (HS256).
    """
    header = {"alg": "HS256", "typ": "JWT"}
    token_payload = dict(payload)
    token_payload["iat"] = int(time.time())
    token_payload["exp"] = int(time.time()) + expires_in_seconds

    header_bytes = json.dumps(header, separators=(",", ":")).encode("utf-8")
    payload_bytes = json.dumps(token_payload, separators=(",", ":")).encode("utf-8")

    header_b64 = _b64encode(header_bytes)
    payload_b64 = _b64encode(payload_bytes)

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_b64 = _b64encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_access_token(token: str, secret_key: str) -> Dict[str, Any]:
    """
    Decodes and validates signature and expiration of an HS256 JWT.
    Raises ValueError on invalid format, bad signature, or expired token.
    """
    if not token or not isinstance(token, str):
        raise ValueError("Invalid token")
    parts = token.strip().split(".")
    if len(parts) != 3:
        raise ValueError("Invalid token format (expected 3 dot-separated segments)")

    header_b64, payload_b64, signature_b64 = parts

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    actual_sig = _b64decode(signature_b64)

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Invalid token signature")

    payload_bytes = _b64decode(payload_b64)
    payload = json.loads(payload_bytes.decode("utf-8"))

    if "exp" in payload and payload["exp"] < int(time.time()):
        raise ValueError("Token has expired")

    return payload
