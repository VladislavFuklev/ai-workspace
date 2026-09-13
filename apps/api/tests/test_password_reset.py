"""Password reset: single use, short life, and everything signed out afterwards."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession as DbSession

from ai_workspace_api.api.app import create_app
from ai_workspace_api.api.dependencies import get_session
from ai_workspace_api.core.database import create_engine, create_session_factory
from ai_workspace_api.core.passwords import hash_password, verify_password
from ai_workspace_api.core.settings import Settings
from ai_workspace_api.core.tokens import hash_refresh_token
from ai_workspace_api.models import PasswordResetToken, Session, User
from ai_workspace_api.services.password_reset import PasswordResetService

from .conftest import BuildSettings, running_app

REQUEST = "/api/v1/auth/password-reset/request"
CONFIRM = "/api/v1/auth/password-reset/confirm"
LOGIN = "/api/v1/auth/login"
OLD_PASSWORD = "correct horse battery staple"
NEW_PASSWORD = "a different passphrase entirely"

pytestmark = pytest.mark.integration


@dataclass
class Api:
    client: httpx.AsyncClient
    db: DbSession
    settings: Settings


@asynccontextmanager
async def build_api(
    valid_env: dict[str, str], settings_from: BuildSettings, database_url: str
) -> AsyncIterator[Api]:
    settings = settings_from({**valid_env, "DATABASE_URL": database_url})
    engine = create_engine(settings)
    factory = create_session_factory(engine)
    app = create_app(settings)

    connection = await engine.connect()
    transaction = await connection.begin()
    db = factory(bind=connection, join_transaction_mode="create_savepoint")

    async def override() -> AsyncIterator[DbSession]:
        yield db

    app.dependency_overrides[get_session] = override
    try:
        async with running_app(app) as client:
            yield Api(client=client, db=db, settings=settings)
    finally:
        app.dependency_overrides.clear()
        await db.close()
        await transaction.rollback()
        await connection.close()
        await engine.dispose()


@pytest.fixture
async def api(
    valid_env: dict[str, str], settings_from: BuildSettings, database_url: str
) -> AsyncIterator[Api]:
    async with build_api(valid_env, settings_from, database_url) as built:
        yield built


async def seed(db: DbSession, email: str) -> User:
    user = User(email=email, password_hash=hash_password(OLD_PASSWORD), display_name="Member")
    db.add(user)
    await db.flush()
    return user


async def issue_token(api: Api, email: str) -> str:
    """Through the service, because nothing sends the token yet."""
    token = await PasswordResetService(api.db, api.settings).request(email)
    assert token is not None
    return token


async def test_requesting_for_an_unknown_address_looks_identical(api: Api) -> None:
    """Otherwise the endpoint is a membership oracle, like registration was."""
    await seed(api.db, "known@example.com")

    known = await api.client.post(REQUEST, json={"email": "known@example.com"})
    unknown = await api.client.post(REQUEST, json={"email": "nobody@example.com"})

    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()


async def test_no_token_is_created_for_an_unknown_address(api: Api) -> None:
    await api.client.post(REQUEST, json={"email": "nobody@example.com"})

    stored = (await api.db.execute(select(PasswordResetToken))).scalars().all()

    assert stored == []


async def test_the_raw_token_is_not_stored(api: Api) -> None:
    await seed(api.db, "hashed@example.com")
    token = await issue_token(api, "hashed@example.com")

    stored = (await api.db.execute(select(PasswordResetToken))).scalars().one()

    assert stored.token_hash != token
    assert stored.token_hash == hash_refresh_token(token)


async def test_the_response_never_contains_the_token(api: Api) -> None:
    """There is deliberately no development mode that returns it."""
    await seed(api.db, "quiet@example.com")

    response = await api.client.post(REQUEST, json={"email": "quiet@example.com"})
    stored = (await api.db.execute(select(PasswordResetToken))).scalars().one()

    assert stored.token_hash not in response.text
    assert len(response.json()["message"]) < 200


async def test_a_valid_token_changes_the_password(api: Api) -> None:
    user = await seed(api.db, "reset@example.com")
    token = await issue_token(api, "reset@example.com")

    response = await api.client.post(CONFIRM, json={"token": token, "password": NEW_PASSWORD})

    assert response.status_code == 204
    await api.db.refresh(user)
    assert verify_password(NEW_PASSWORD, user.password_hash) is True
    assert verify_password(OLD_PASSWORD, user.password_hash) is False


async def test_a_token_works_only_once(api: Api) -> None:
    await seed(api.db, "once@example.com")
    token = await issue_token(api, "once@example.com")

    first = await api.client.post(CONFIRM, json={"token": token, "password": NEW_PASSWORD})
    second = await api.client.post(
        CONFIRM, json={"token": token, "password": "yet another passphrase"}
    )

    assert first.status_code == 204
    assert second.status_code == 422


async def test_requesting_again_invalidates_the_earlier_link(api: Api) -> None:
    """An older link left in an inbox must stop working."""
    await seed(api.db, "again@example.com")
    first_token = await issue_token(api, "again@example.com")
    await issue_token(api, "again@example.com")

    response = await api.client.post(CONFIRM, json={"token": first_token, "password": NEW_PASSWORD})

    assert response.status_code == 422


async def test_an_expired_token_fails(api: Api) -> None:
    await seed(api.db, "expired@example.com")
    token = await issue_token(api, "expired@example.com")
    stored = (await api.db.execute(select(PasswordResetToken))).scalars().one()
    stored.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    await api.db.flush()

    response = await api.client.post(CONFIRM, json={"token": token, "password": NEW_PASSWORD})

    assert response.status_code == 422


async def test_an_unknown_token_fails_the_same_way(api: Api) -> None:
    """Unknown, used and expired must be one answer, or the differences guide
    an attacker."""
    await seed(api.db, "guess@example.com")
    token = await issue_token(api, "guess@example.com")
    good = await api.client.post(CONFIRM, json={"token": token, "password": NEW_PASSWORD})
    used = await api.client.post(CONFIRM, json={"token": token, "password": NEW_PASSWORD})
    unknown = await api.client.post(CONFIRM, json={"token": "x" * 43, "password": NEW_PASSWORD})

    assert good.status_code == 204
    assert used.status_code == unknown.status_code == 422
    assert used.json()["message"] == unknown.json()["message"]


async def test_a_weak_new_password_is_rejected(api: Api) -> None:
    await seed(api.db, "weak@example.com")
    token = await issue_token(api, "weak@example.com")

    response = await api.client.post(CONFIRM, json={"token": token, "password": "short"})

    assert response.status_code == 422
    assert "password" in {item["field"] for item in response.json()["detail"]}


async def test_every_session_is_revoked_on_reset(api: Api) -> None:
    """The point of the whole flow: whoever prompted the reset is signed out."""
    user = await seed(api.db, "compromised@example.com")
    signed_in = await api.client.post(
        LOGIN, json={"email": "compromised@example.com", "password": OLD_PASSWORD}
    )
    assert signed_in.status_code == 200
    live = (
        (
            await api.db.execute(
                select(Session).where(Session.user_id == user.id, Session.revoked_at.is_(None))
            )
        )
        .scalars()
        .all()
    )
    assert live, "no session to revoke; the test proves nothing"

    token = await issue_token(api, "compromised@example.com")
    assert (
        await api.client.post(CONFIRM, json={"token": token, "password": NEW_PASSWORD})
    ).status_code == 204

    remaining = (
        (
            await api.db.execute(
                select(Session).where(Session.user_id == user.id, Session.revoked_at.is_(None))
            )
        )
        .scalars()
        .all()
    )
    assert remaining == []


async def test_the_old_password_no_longer_signs_in(api: Api) -> None:
    await seed(api.db, "old@example.com")
    token = await issue_token(api, "old@example.com")
    await api.client.post(CONFIRM, json={"token": token, "password": NEW_PASSWORD})

    old = await api.client.post(LOGIN, json={"email": "old@example.com", "password": OLD_PASSWORD})
    new = await api.client.post(LOGIN, json={"email": "old@example.com", "password": NEW_PASSWORD})

    assert old.status_code == 401
    assert new.status_code == 200
