"""Password policy.

Length first: length beats composition rules, which mostly teach people to write
`Password1!`. The list of forbidden values is deliberately short — a serious
breach-corpus check belongs behind a service, not in a constant.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator

MIN_LENGTH = 12
# bcrypt's 72-byte limit does not apply to Argon2, but an unbounded password is
# unbounded work for the server. 128 is far past any real passphrase.
MAX_LENGTH = 128

# Roots that appear at the top of every breach corpus. Matched after stripping
# trailing digits and punctuation, because "password1234" and "qwerty!!!" are the
# shape people actually pick when told to add a number.
#
# An exact-match list is close to useless — the first version of this let
# "password1234" through, which a test caught. This is still not a substitute
# for checking a real breach corpus; that belongs behind a service, not in a
# constant, and is worth revisiting at 3.7.
FORBIDDEN_ROOTS = frozenset(
    {
        "password",
        "passwd",
        "passw0rd",
        "qwerty",
        "qwertyuiop",
        "letmein",
        "iloveyou",
        "admin",
        "administrator",
        "welcome",
        "monkey",
        "dragon",
        "abc",
        "123",
    }
)


def _root(password: str) -> str:
    """The password with trailing digits and punctuation removed, lowercased."""
    stripped = password.lower().strip()
    return stripped.rstrip("0123456789!@#$%^&*()_+-=.,")


def _check(password: str) -> str:
    if len(password) < MIN_LENGTH:
        raise ValueError(f"Use at least {MIN_LENGTH} characters.")
    if len(password) > MAX_LENGTH:
        raise ValueError(f"Use at most {MAX_LENGTH} characters.")
    if _root(password) in FORBIDDEN_ROOTS:
        raise ValueError("That password is too common. Choose something else.")
    if password.strip() == "":
        raise ValueError("A password cannot be only whitespace.")
    return password


Password = Annotated[str, AfterValidator(_check)]
