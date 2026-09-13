"""Password hashing and policy."""

from __future__ import annotations

import time

import pytest
from argon2 import PasswordHasher
from pydantic import BaseModel, ValidationError

from ai_workspace_api.core.passwords import (
    hash_password,
    needs_rehash,
    verify_absent_user,
    verify_password,
)
from ai_workspace_api.schemas.password import MAX_LENGTH, MIN_LENGTH, Password

GOOD = "correct horse battery staple"


def test_the_same_password_hashes_differently_each_time() -> None:
    """Otherwise identical passwords are visible as identical hashes, and one
    cracked hash gives away every account that shares it."""
    assert hash_password(GOOD) != hash_password(GOOD)


def test_the_hash_does_not_contain_the_password() -> None:
    assert GOOD not in hash_password(GOOD)


def test_the_hash_is_argon2id() -> None:
    assert hash_password(GOOD).startswith("$argon2id$")


def test_a_correct_password_verifies() -> None:
    assert verify_password(GOOD, hash_password(GOOD)) is True


@pytest.mark.parametrize(
    "wrong",
    ["correct horse battery stapl", "Correct horse battery staple", "", " " + GOOD],
)
def test_a_wrong_password_does_not_verify(wrong: str) -> None:
    assert verify_password(wrong, hash_password(GOOD)) is False


def test_an_absent_hash_verifies_to_false_without_raising() -> None:
    """An identity-provider account has no password (task 3.1). This must be a
    plain no, not an exception a handler has to catch."""
    assert verify_password(GOOD, None) is False


@pytest.mark.parametrize(
    "corrupt",
    ["", "not-a-hash", "$argon2id$truncated", "$2b$12$bcrypt.style.hash.from.elsewhere"],
)
def test_a_corrupt_or_foreign_hash_verifies_to_false(corrupt: str) -> None:
    assert verify_password(GOOD, corrupt) is False


def test_the_hash_fits_the_column() -> None:
    """password_hash is varchar(255); a hash that overflows it fails at insert."""
    assert len(hash_password(GOOD)) <= 255


def test_a_weaker_hash_is_reported_as_needing_a_rehash() -> None:
    """Cost rises with hardware. Rehashing on sign-in is the only moment the
    plaintext is available to do it."""
    weak = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1).hash(GOOD)

    assert needs_rehash(weak) is True
    assert needs_rehash(hash_password(GOOD)) is False


def test_an_unreadable_hash_is_treated_as_needing_replacement() -> None:
    assert needs_rehash("nonsense") is True


def test_verifying_an_absent_user_costs_about_the_same_as_a_real_one() -> None:
    """Without this, an unregistered address answers in microseconds and a
    registered one in milliseconds, which enumerates accounts."""
    stored = hash_password(GOOD)

    def elapsed(work: object) -> float:
        start = time.perf_counter()
        work()  # type: ignore[operator]
        return time.perf_counter() - start

    real = min(elapsed(lambda: verify_password("wrong password here", stored)) for _ in range(3))
    absent = min(elapsed(lambda: verify_absent_user("wrong password here")) for _ in range(3))

    # Generous: this asserts the same order of magnitude, not a constant time.
    # A missing dummy verification would make `absent` hundreds of times faster.
    assert absent > real / 4, f"absent={absent:.4f}s real={real:.4f}s"


class PasswordCarrier(BaseModel):
    password: Password


@pytest.mark.parametrize(
    "value",
    ["correct horse battery staple", "x" * MIN_LENGTH, "MyPasswordIsLongEnough"],
)
def test_the_policy_accepts_a_reasonable_password(value: str) -> None:
    """A passphrase containing a common word is fine — only the whole password
    reducing to one is not."""
    assert PasswordCarrier(password=value).password == value


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        ("short", "at least"),
        ("x" * (MIN_LENGTH - 1), "at least"),
        ("x" * (MAX_LENGTH + 1), "at most"),
        ("password1234", "too common"),
        ("qwerty123456", "too common"),
        ("Welcome2026!", "too common"),
        ("PASSWORD", "at least"),
        ("            ", "whitespace"),
    ],
)
def test_the_policy_rejects_and_says_why(value: str, reason: str) -> None:
    """A rejection with no reason makes the user guess."""
    with pytest.raises(ValidationError) as caught:
        PasswordCarrier(password=value)

    assert reason in str(caught.value).lower()
