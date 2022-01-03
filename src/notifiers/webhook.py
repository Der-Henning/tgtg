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
        self.data = config.webhook["data"]
        self.json = config.webhook["json"]
        self.timeout = config.webhook["timeout"]
        if self.enabled and (not self.method or not self.url):
            raise WebHookConfigurationError()
        for match in re.finditer(r"\${{([a-zA-Z0-9]+)}}", self.data):
            if not match.group(1) in Item.__dict__:
                raise WebHookConfigurationError()
        for match in re.finditer(r"\${{([a-zA-Z0-9]+)}}", self.json):
            if not match.group(1) in Item.__dict__:
                raise WebHookConfigurationError()
        for match in re.finditer(r"\${{([a-zA-Z0-9]+)}}", self.url):
            if not match.group(1) in Item.__dict__:
                raise WebHookConfigurationError()

    def send(self, item: Item):
        if self.enabled:
            log.info("Sending Request Notification")
            try:
                url = self.url
                for match in re.finditer(r"\${{([a-zA-Z0-9]+)}}", url):
                    url = url.replace(match.group(0), item[match.group(1)])
                data = None
                headers = {}
                if self.data:
                    data = self.data
                    for match in re.finditer(r"\${{([a-zA-Z0-9]+)}}", data):
                        data = data.replace(
                            match.group(0), item[match.group(1)])
                    headers["Content-Type"] = "text/plain"
                    headers["Content-Length"] = str(len(data))
                    log.debug("Webhook data: %s", data)
                elif self.json:
                    data = self.json
                    for match in re.finditer(r"\${{([a-zA-Z0-9]+)}}", data):
                        data = data.replace(
                            match.group(0), item[match.group(1)])
                    headers["Content-Type"] = "application/json"
                    headers["Content-Length"] = str(len(data))
                    log.debug("Webhook json: %s", data)
                res = requests.request(method=self.method, url=self.url,
                                       timeout=self.timeout, data=data, headers=headers)
                if res.status_code != 200:
                    log.error(
                        "WebHook Request failed with status code %s", res.status_code)
            except Exception as err:
                log.error(err)
