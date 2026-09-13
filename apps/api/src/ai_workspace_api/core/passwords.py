"""Password hashing.

Argon2id, via `argon2-cffi`. The algorithm sits behind this module so changing
it — and OWASP's recommendation does change — is a change here rather than
everywhere a password is touched.

Three rules the rest of the codebase relies on:

1. `verify` returns a boolean. It does not raise for a wrong password, an absent
   hash or a corrupt one; a handler that has to catch an exception to learn "no"
   will eventually catch the wrong thing.
2. Verifying a user who does not exist costs the same as verifying one who does.
   Otherwise response time answers "is this address registered?" for anyone who
   asks, which is the whole point of a generic sign-in error.
3. A hash made with weaker parameters is reported as needing a rehash, so cost
   rises with hardware without asking anyone to reset a password.
"""

from __future__ import annotations

from contextlib import suppress

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

# OWASP's Argon2id baseline: 19 MiB of memory, two iterations, one lane. Memory
# is what makes GPU cracking expensive, so it is the parameter to raise first.
_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=19456,
    parallelism=1,
    hash_len=32,
    salt_len=16,
)

# Verified against when no user exists, so the work done is the same either way.
# Computed once at import: doing it per request would be its own timing signal.
_DUMMY_HASH = _hasher.hash("a password nobody has")


def hash_password(password: str) -> str:
    """Argon2id embeds the salt and the parameters, so the hash is self-describing."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    """Whether the password matches. Never raises.

    `password_hash` is `None` for an identity-provider account (task 3.1). That
    still runs the dummy verification, so "this account has no password" and
    "this password is wrong" take the same time.
    """
    if password_hash is None:
        _spend_equivalent_time(password)
        return False
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        # A corrupt or foreign hash is a failed verification, not a server error.
        return False


def verify_absent_user(password: str) -> None:
    """Call when no user matched, before returning a generic failure.

    Without it, a sign-in for an unregistered address returns in microseconds
    while a registered one takes ~50ms, and the difference enumerates accounts.
    """
    _spend_equivalent_time(password)


def _spend_equivalent_time(password: str) -> None:
    # The verification is expected to fail; the point is the work, not the answer.
    with suppress(VerifyMismatchError, VerificationError, InvalidHashError):
        _hasher.verify(_DUMMY_HASH, password)


def needs_rehash(password_hash: str) -> bool:
    """True when the stored hash used weaker parameters than the current ones.

    The caller re-hashes during a successful sign-in, when the plaintext is in
    hand — the only moment it can.
    """
    try:
        return _hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        # Unreadable: treat as needing replacement rather than as acceptable.
        return True
