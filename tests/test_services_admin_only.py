# tests/test_services_admin_only.py
"""Fork change: maintenance services are restricted to administrators.

``refresh_device_urls``, ``rebuild_device_registry`` and ``rebuild_registry``
rewrite the device/entity registry and reload config entries. They are wrapped
by ``services.admin_only_service`` (same check as Core's
``async_register_admin_service``); the user-facing services (locate, sound)
stay available to every user.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest import mock

import pytest
from homeassistant.exceptions import Unauthorized, UnknownUser

from custom_components.googlefindmy import services
from custom_components.googlefindmy.const import (
    SERVICE_LOCATE_DEVICE,
    SERVICE_LOCATE_EXTERNAL,
    SERVICE_PLAY_SOUND,
    SERVICE_REBUILD_REGISTRY,
    SERVICE_REFRESH_DEVICE_URLS,
    SERVICE_STOP_SOUND,
)

ADMIN_SERVICES = {
    SERVICE_REFRESH_DEVICE_URLS,
    "rebuild_device_registry",
    SERVICE_REBUILD_REGISTRY,
}
USER_SERVICES = {
    SERVICE_LOCATE_DEVICE,
    SERVICE_LOCATE_EXTERNAL,
    SERVICE_PLAY_SOUND,
    SERVICE_STOP_SOUND,
}

_USERS = {
    "admin-id": SimpleNamespace(is_admin=True),
    "user-id": SimpleNamespace(is_admin=False),
}


def _hass() -> SimpleNamespace:
    async def _get_user(user_id: str) -> Any:
        return _USERS.get(user_id)

    return SimpleNamespace(auth=SimpleNamespace(async_get_user=_get_user))


def _call(user_id: str | None) -> SimpleNamespace:
    return SimpleNamespace(data={}, context=SimpleNamespace(user_id=user_id))


def _registered_handlers() -> dict[str, Any]:
    handlers: dict[str, Any] = {}

    def _capture(domain: str, name: str, handler: Any) -> None:
        handlers[name] = handler

    hass = SimpleNamespace(
        services=SimpleNamespace(async_register=_capture),
        config_entries=SimpleNamespace(async_entries=lambda _domain: []),
        auth=_hass().auth,
        data={},
    )
    ctx = {"domain": services.DOMAIN}
    coro = services.async_register_services(hass, ctx)
    try:
        coro.send(None)
    except StopIteration:
        pass
    else:  # pragma: no cover - registration must not await
        coro.close()
        raise RuntimeError("async_register_services unexpectedly awaited")
    return handlers


def test_only_maintenance_services_are_admin_only() -> None:
    """The three registry/reload services are wrapped, the others are not."""

    handlers = _registered_handlers()
    assert set(handlers) == ADMIN_SERVICES | USER_SERVICES
    # functools.wraps exposes the original handler as ``__wrapped__``.
    for name in ADMIN_SERVICES:
        assert hasattr(handlers[name], "__wrapped__"), name
    for name in USER_SERVICES:
        assert not hasattr(handlers[name], "__wrapped__"), name


@pytest.mark.asyncio
@pytest.mark.parametrize("user_id", [None, "admin-id"])
async def test_admin_and_userless_calls_run(user_id: str | None) -> None:
    """Admins and calls without a user (automations, scripts) are allowed."""

    inner = mock.AsyncMock()
    wrapped = services.admin_only_service(_hass(), inner)
    call = _call(user_id)
    await wrapped(call)
    inner.assert_awaited_once_with(call)


@pytest.mark.asyncio
async def test_call_without_context_runs() -> None:
    """A bare call object (internal callers, test doubles) is allowed."""

    inner = mock.AsyncMock()
    wrapped = services.admin_only_service(_hass(), inner)
    call = SimpleNamespace(data={})
    await wrapped(call)
    inner.assert_awaited_once_with(call)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("user_id", "exc"),
    [("user-id", Unauthorized), ("missing-id", UnknownUser)],
)
async def test_non_admin_or_unknown_user_is_rejected(user_id: str, exc: type) -> None:
    """A non-admin user gets Unauthorized, an unknown user UnknownUser."""

    inner = mock.AsyncMock()
    wrapped = services.admin_only_service(_hass(), inner)
    with pytest.raises(exc):
        await wrapped(_call(user_id))
    inner.assert_not_awaited()
