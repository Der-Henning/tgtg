import logging
import re
import requests
from models import Item, Config, WebHookConfigurationError

log = logging.getLogger('tgtg')


class WebHook():
    def __init__(self, config: Config):
        self.enabled = config.webhook["enabled"]
        self.method = config.webhook["method"]
        self.url = config.webhook["url"]
        self.body = config.webhook["body"]
        self.type = config.webhook["type"]
        self.timeout = config.webhook["timeout"]
        if self.enabled and (not self.method or not self.url):
            raise WebHookConfigurationError()
        for match in re.finditer(r"\${{([a-zA-Z0-9_]+)}}", self.body):
            if not match.group(1) in Item.ATTRS:
                raise WebHookConfigurationError()
        for match in re.finditer(r"\${{([a-zA-Z0-9_]+)}}", self.url):
            if not match.group(1) in Item.ATTRS:
                raise WebHookConfigurationError()

    def send(self, item: Item):
        if self.enabled:
            log.debug("Sending WebHook Notification")
            try:
                url = self.url
                for match in re.finditer(r"\${{([a-zA-Z0-9_]+)}}", url):
                    if hasattr(item, match.group(1)):
                        url = url.replace(match.group(0), str(getattr(item, match.group(1))))
                log.debug("Webhook url: %s", url)
                body = None
                headers = {
                    "Content-Type": self.type
                }
                log.debug("Webhook headers: %s", headers)
                if self.body:
                    body = self.body
                    for match in re.finditer(r"\${{([a-zA-Z0-9_]+)}}", body):
                        if hasattr(item, match.group(1)):
                            body = body.replace(
                                match.group(0), f"{getattr(item, match.group(1))}")
                    headers["Content-Length"] = str(len(body))
                    log.debug("Webhook body: %s", body)
                res = requests.request(method=self.method, url=self.url,
                                       timeout=self.timeout, data=body, headers=headers)
                if res.status_code != 200:
                    log.error(
                        "WebHook Request failed with status code %s", res.status_code)
            except Exception as err:
                log.error(err)
