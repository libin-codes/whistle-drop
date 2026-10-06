"""Tests for case code generation and hashing (ADR-0001)."""

import hashlib
import re

from app.case_codes import generate_case_code, hash_case_code


def test_case_code_format():
    """Case code must match WD-XXXX-XXXX where X is an uppercase alphanumeric char."""
    code = generate_case_code()
    assert re.fullmatch(r"WD-[A-Z0-9]{4}-[A-Z0-9]{4}", code)


def test_case_code_uniqueness():
    """Successive calls should produce distinct codes (probabilistic but safe at 8 chars)."""
    codes = {generate_case_code() for _ in range(100)}
    assert len(codes) == 100


def test_hash_case_code_deterministic():
    """Hashing the same code twice must yield the same digest."""
    code = generate_case_code()
    assert hash_case_code(code) == hash_case_code(code)


def test_hash_case_code_is_sha256_hex():
    """The hash must be a lowercase hex SHA-256 digest."""
    code = generate_case_code()
    digest = hash_case_code(code)
    assert len(digest) == 64
    assert digest == hashlib.sha256(code.encode()).hexdigest()
