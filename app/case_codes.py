"""Case code generation and zero-knowledge hashing (ADR-0001).

The plaintext case code is returned to the reporter exactly once.
Only the SHA-256 hash is ever persisted.
"""

import hashlib
import secrets
import string

_ALPHABET = string.ascii_uppercase + string.digits


def generate_case_code() -> str:
    """Generate a cryptographically random case code in ``WD-XXXX-XXXX`` format."""
    block = lambda: "".join(secrets.choice(_ALPHABET) for _ in range(4))  # noqa: E731
    return f"WD-{block()}-{block()}"


def hash_case_code(case_code: str) -> str:
    """Return the lowercase hex SHA-256 digest of *case_code*."""
    return hashlib.sha256(case_code.encode()).hexdigest()
