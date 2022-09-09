import logging
import requests
from models import Item, Config, Cron
from models.errors import WebHookConfigurationError, MaskConfigurationError
from notifiers import Notifier

log = logging.getLogger('tgtg')


class WebHook(Notifier):
    """Notifier for custom Webhooks"""
    def __init__(self, config: Config):
        self.enabled = config.webhook["enabled"]
        self.method = config.webhook["method"]
        self.url = config.webhook["url"]
        self.body = config.webhook["body"]
        self.type = config.webhook["type"]
        self.timeout = config.webhook["timeout"]
        self.cron = Cron(config.webhook["cron"])
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
                body = item.unmask(self.body).encode(encoding='UTF-8', errors='replace')
                headers["Content-Length"] = str(len(body))
                log.debug("Webhook body: %s", body)
            log.debug("Webhook headers: %s", headers)
            res = requests.request(method=self.method, url=url,
                                    timeout=self.timeout, data=body, headers=headers)
            if not res.ok:
                log.error(
                    "WebHook Request failed with status code %s", res.status_code)

    def __repr__(self) -> str:
        return f"WebHook: {self.url}"
