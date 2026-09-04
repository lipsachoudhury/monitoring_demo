"""Authentication service — credential verification.

Keeps route handlers thin; all credential logic lives here.
Credentials are never hardcoded: expected values come from
``current_app.config`` (populated from environment via dotenv).
"""
import hmac

from flask import current_app
from werkzeug.security import check_password_hash


def verify_credentials(username, password):
    """Verify a username/password pair against env-configured credentials.

    Uses constant-time comparison for the username and a salted hash
    comparison (Werkzeug scrypt/pbkdf2) for the password. Returns False
    when credentials are missing, unconfigured, or do not match.
    """
    if not isinstance(username, str) or not isinstance(password, str):
        return False
    if not username or not password:
        return False
    # Bound input size to avoid hashing DoS with huge payloads.
    if len(username) > 128 or len(password) > 512:
        return False

    expected_username = current_app.config.get('ADMIN_USERNAME')
    password_hash = current_app.config.get('ADMIN_PASSWORD_HASH')
    if not expected_username or not password_hash:
        return False

    if not hmac.compare_digest(username, expected_username):
        return False
    try:
        return check_password_hash(password_hash, password)
    except (ValueError, TypeError, AttributeError):
        return False
