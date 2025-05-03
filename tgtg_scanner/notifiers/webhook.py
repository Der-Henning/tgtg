import json
import logging
from typing import Union

import requests
from requests.auth import HTTPBasicAuth

from tgtg_scanner.errors import MaskConfigurationError, WebHookConfigurationError
from tgtg_scanner.models import Config, Favorites, Item, Reservations
from tgtg_scanner.models.reservations import Reservation
from tgtg_scanner.notifiers.base import Notifier

log = logging.getLogger("tgtg")


class WebHook(Notifier):
    """Notifier for custom Webhooks."""

    def __init__(self, config: Config, reservations: Reservations, favorites: Favorites):
        super().__init__(config, reservations, favorites)
        self.enabled: bool = config.webhook.enabled
        self.method: str = config.webhook.method
        self.url: Union[str, None] = config.webhook.url
        self.body: Union[str, None] = config.webhook.body
        self.type: Union[str, None] = config.webhook.type
        self.headers: dict[str, Union[str, bytes]] = config.webhook.headers
        self.auth = None
        self.username: Union[str, None] = config.webhook.username
        self.password: Union[str, None] = config.webhook.password
        self.timeout: int = config.webhook.timeout
        self.cron = config.webhook.cron
        if self.enabled:
            if self.method is None or self.url is None:
                raise WebHookConfigurationError()
            if self.username is not None and self.password is not None:
                self.auth = HTTPBasicAuth(self.username, self.password)
                log.debug("Using basic auth with user '%s' for webhook", self.username)
            try:
                Item.check_mask(self.body)
                Item.check_mask(self.url)
            except MaskConfigurationError as exc:
                raise WebHookConfigurationError(exc.message) from exc

    def _send(self, item: Union[Item, Reservation]) -> None:
        """Sends item information via configured Webhook endpoint."""
        if isinstance(item, Item):
            if self.url is None:
                raise WebHookConfigurationError()
            url = item.unmask(self.url)
            log.debug("%s url: %s", self.name, url)
            body: Union[bytes, None] = None
            headers = self.headers or dict()
            if self.type:
                headers["Content-Type"] = self.type
            if self.body:
                if self.type is not None and "json" in self.type:
                    body = json.dumps(json.loads(item.unmask(self.body).replace("\n", "\\n"))).encode("utf-8")
                else:
                    body = item.unmask(self.body).encode("utf-8")
                log.debug("%s body: %s", self.name, body)
                # body = item.unmask(self.body)
                # if isinstance(body, bytes):
                #     pass
                # elif self.type and "json" in self.type:
                #     body = json.dumps(json.loads(body.replace("\n", "\\n")))
                #     log.debug("%s body: %s", self.name, body)
                # else:
                #     body = body.encode("utf-8")
                #     log.debug("%s body: %s", self.name, body)
            log.debug("%s headers: %s", self.name, headers)
            res = requests.request(
                method=self.method,
                url=url,
                timeout=self.timeout,
                data=body,
                headers=headers,
                auth=self.auth,
            )
            if not res.ok:
                log.error("%s Request failed with status code %s", self.name, res.status_code)
                log.debug("%s Response content: %s", self.name, res.text)

    def __repr__(self) -> str:
        return f"WebHook: {self.url}"
