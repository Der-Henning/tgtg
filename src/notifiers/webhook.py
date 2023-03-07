import json
import logging

import requests
from requests.auth import HTTPBasicAuth

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
        self.headers = config.webhook.get("headers", {})
        self.auth = None
        self.username = config.webhook.get("username")
        self.password = config.webhook.get("password")
        self.timeout = config.webhook.get("timeout", 60)
        self.cron = config.webhook.get("cron")
        if self.enabled:
            if not self.method or not self.url:
                raise WebHookConfigurationError()
            if (self.username and self.password) is not None:
                self.auth = HTTPBasicAuth(self.username, self.password)
                log.debug("Using basic auth with user '%s' "
                          "for webhook", self.username)
            try:
                Item.check_mask(self.body)
                Item.check_mask(self.url)
            except MaskConfigurationError as exc:
                raise WebHookConfigurationError(exc.message) from exc

    def _send(self, item: Item) -> None:
        """Sends item information via configured Webhook endpoint"""
        url = item.unmask(self.url)
        log.debug("%s url: %s", self.__class__.__name__, url)
        body = None
        headers = self.headers
        if self.type:
            headers["Content-Type"] = self.type
        if self.body:
            body = item.unmask(self.body)
            if self.type and 'json' in self.type:
                body = json.dumps(json.loads(body.replace('\n', '\\n')))
            else:
                body = body.encode('utf-8')
            log.debug("%s body: '%s'", self.__class__.__name__, body)
        log.debug("%s headers: %s", self.__class__.__name__, headers)
        res = requests.request(method=self.method, url=url,
                               timeout=self.timeout, data=body,
                               headers=headers, auth=self.auth)
        if not res.ok:
            log.error("%s Request failed with status code %s",
                      self.__class__.__name__, res.status_code)
            log.debug("Response content: %s", res.text)

    def __repr__(self) -> str:
        return f"WebHook: {self.url}"
