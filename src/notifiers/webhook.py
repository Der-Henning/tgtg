import logging

import requests

from models import Config, Item
from models.errors import MaskConfigurationError, WebHookConfigurationError
from notifiers import Notifier

log = logging.getLogger('tgtg')


class WebHook(Notifier):
    """Notifier for custom Webhooks"""

    def __init__(self, config: Config):
        self.enabled = config.webhook.get("enabled", False)
        self.method = config.webhook.get("method")
        self.url = config.webhook.get("url")
        self.body = config.webhook.get("body")
        self.type = config.webhook.get("type")
        self.timeout = config.webhook.get("timeout", 60)
        self.cron = config.webhook.get("cron")
        if self.enabled and (not self.method or not self.url):
            raise WebHookConfigurationError()
        if self.enabled:
            try:
                Item.check_mask(self.body)
                Item.check_mask(self.url)
            except MaskConfigurationError as exc:
                raise WebHookConfigurationError(exc.message) from exc

    def send(self, item: Item) -> None:
        """Sends item information via configured Webhook endpoint"""
        if self.enabled and self.cron.is_now:
            log.debug("Sending WebHook Notification")
            url = item.unmask(self.url)
            log.debug("Webhook url: %s", url)
            body = None
            headers = {
                "Content-Type": self.type
            }
            if self.body:
                body = item.unmask(self.body).encode(
                    encoding='UTF-8', errors='replace')
                headers["Content-Length"] = str(len(body))
                log.debug("Webhook body: %s", body)
            log.debug("Webhook headers: %s", headers)
            res = requests.request(method=self.method, url=url,
                                   timeout=self.timeout, data=body,
                                   headers=headers)
            if not res.ok:
                log.error("WebHook Request failed with status code %s",
                          res.status_code)
                log.debug("Response content: %s", res.text)

    def __repr__(self) -> str:
        return f"WebHook: {self.url}"
