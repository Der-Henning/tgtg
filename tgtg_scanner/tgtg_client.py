"""Too Good To Go client for the scanner.

Thin subclass of the official ``tgtg`` package with only scanner-specific behavior:
browser PIN login (Docker) and paginated favorites.
"""

from __future__ import annotations

import builtins
import contextlib
import logging
import re
from collections.abc import Iterator

import tgtg
from tgtg import BASE_URL
from tgtg import TgtgClient as _UpstreamTgtgClient

from tgtg_scanner.pin_prompt import prompt_via_browser

log = logging.getLogger("tgtg")

_DATADOME_RE = re.compile(r"datadome=([^;]+)", re.IGNORECASE)


def normalize_cookie(value: str | None) -> str | None:
    """Map config Datadome (raw token or Cookie header) to upstream cookie."""
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    if "=" in value:
        return value
    return f"datadome={value}"


def extract_datadome(client: _UpstreamTgtgClient) -> str:
    """Datadome token for config.ini / token files (legacy field name)."""
    values = [c.value for c in client.session.cookies if c.name == "datadome" and c.value]
    if values:
        return values[-1]
    if client.cookie:
        match = _DATADOME_RE.search(client.cookie)
        if match:
            return match.group(1)
        if "=" not in client.cookie:
            return client.cookie
    return ""


def resolve_user_agent(user_agent: str | None = None, apk_version: str | None = None) -> str | None:
    """Optional UA override for config. None lets upstream pick APK version + UA."""
    if user_agent:
        return user_agent
    if apk_version:
        # Minimal override when only APK version is configured
        return f"TGTG/{apk_version} Dalvik/2.1.0 (Linux; U; Android 12; SM-G920V Build/MMB29K)"
    return None


@contextlib.contextmanager
def _patched_input(value: str) -> Iterator[None]:
    original = builtins.input
    builtins.input = lambda *_args, **_kwargs: value  # type: ignore[assignment]
    try:
        yield
    finally:
        builtins.input = original


class TgtgClient(_UpstreamTgtgClient):
    """Official tgtg client + browser PIN login + full favorites pagination."""

    def __init__(
        self,
        *args,
        pin_port: int = 0,
        max_polling_tries: int | None = None,
        polling_wait_time: int | None = None,
        **kwargs,
    ) -> None:
        self.pin_port = pin_port
        if max_polling_tries is not None:
            tgtg.MAX_POLLING_TRIES = max_polling_tries
        if polling_wait_time is not None:
            tgtg.POLLING_WAIT_TIME = polling_wait_time
        if kwargs.get("url") and kwargs["url"] != BASE_URL:
            log.warning("Using custom tgtg base url: %s", kwargs["url"])
        super().__init__(*args, **kwargs)

    def login(self) -> None:
        try:
            super().login()
        except TypeError as err:
            from tgtg_scanner.errors import TgtgConfigurationError

            raise TgtgConfigurationError(str(err)) from err

    def start_polling(self, polling_id: str) -> None:
        """Use browser PIN form, then defer to upstream (PIN auth or email-link poll)."""
        pin = prompt_via_browser(email=self.email, port=self.pin_port) or ""
        with _patched_input(pin):
            super().start_polling(polling_id)

    def get_favorites(self, **kwargs) -> list[dict]:
        """Fetch all favorites via upstream paging (page_size 100)."""
        items: list[dict] = []
        page = 0
        page_size = 100
        while True:
            batch = super().get_favorites(page=page, page_size=page_size, **kwargs)
            items.extend(batch)
            if len(batch) < page_size:
                break
            page += 1
        return items

    def get_credentials(self) -> dict:
        """Credentials in the shape the scanner CLI / config persistence expect."""
        self.login()
        return {
            "email": self.email,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "datadome_cookie": extract_datadome(self),
        }
