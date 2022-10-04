# copied and modified from https://github.com/ahivert/tgtg-python

import datetime
import random
import logging
import time
import re
import json
from http import HTTPStatus
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
import requests
from urllib3.util import Retry
from models.errors import (
    TGTGConfigurationError,
    TgtgAPIError,
    TgtgCaptchaError,
    TgtgLoginError,
    TgtgPollingError,
)

log = logging.getLogger("tgtg")
BASE_URL = "https://apptoogoodtogo.com/api/"
API_ITEM_ENDPOINT = "item/v7/"
AUTH_BY_EMAIL_ENDPOINT = "auth/v3/authByEmail"
AUTH_POLLING_ENDPOINT = "auth/v3/authByRequestPollingId"
SIGNUP_BY_EMAIL_ENDPOINT = "auth/v3/signUpByEmail"
REFRESH_ENDPOINT = "auth/v3/token/refresh"
ACTIVE_ORDER_ENDPOINT = "order/v6/active"
INACTIVE_ORDER_ENDPOINT = "order/v6/inactive"
USER_AGENTS = [
    "TGTG/{} Dalvik/2.1.0 (Linux; U; Android 9; Nexus 5 Build/M4B30Z)",
    "TGTG/{} Dalvik/2.1.0 (Linux; U; Android 10; SM-G935F Build/NRD90M)",
    "TGTG/{} Dalvik/2.1.0 (Linux; Android 12; SM-G920V Build/MMB29K)",
]
DEFAULT_ACCESS_TOKEN_LIFETIME = 3600 * 4  # 4 hours
DEFAULT_MAX_POLLING_TRIES = 24  # 24 * POLLING_WAIT_TIME = 2 minutes
DEFAULT_POLLING_WAIT_TIME = 5  # Seconds
DEFAULT_APK_VERSION = "22.9.10"

APK_RE_SCRIPT = re.compile(
    r"AF_initDataCallback\({key:\s*'ds:5'.*?data:([\s\S]*?), sideChannel:.+<\/script"
)


class TgtgClient:
    def __init__(
        self,
        url=BASE_URL,
        email=None,
        access_token=None,
        refresh_token=None,
        user_id=None,
        user_agent=None,
        language="en-UK",
        proxies=None,
        timeout=None,
        access_token_lifetime=DEFAULT_ACCESS_TOKEN_LIFETIME,
        max_polling_tries=DEFAULT_MAX_POLLING_TRIES,
        polling_wait_time=DEFAULT_POLLING_WAIT_TIME,
        device_type="ANDROID",
    ):
        self.base_url = url

        self.email = email
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.user_id = user_id

        self.last_time_token_refreshed = None
        self.access_token_lifetime = access_token_lifetime
        self.max_polling_tries = max_polling_tries
        self.polling_wait_time = polling_wait_time

        self.device_type = device_type
        self.fixed_user_agent = user_agent
        self.user_agent = self._get_user_agent()
        self.language = language
        self.proxies = proxies
        self.timeout = timeout
        self.http_adapter = HTTPAdapter(
            max_retries=Retry(
                total=5,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET", "POST"],
                backoff_factor=1,
            )
        )
        self.session = requests.Session()
        self.session.mount("https://", self.http_adapter)
        self.session.mount("http://", self.http_adapter)
        self.session.headers = self._headers

        self.captcha_error_count = 0

    def __del__(self) -> None:
        self.session.close()

    def _get_url(self, path) -> str:
        return urljoin(self.base_url, path)

    def get_credentials(self) -> dict:
        self.login()
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "user_id": self.user_id,
        }

    def _post(self, path, retry: int = 0, **kwargs) -> requests.Response:
        max_retries = 1
        response = self.session.post(
            self._get_url(path),
            headers=self._headers,
            proxies=self.proxies,
            timeout=self.timeout,
            **kwargs,
        )
        if response.status_code in (HTTPStatus.OK, HTTPStatus.ACCEPTED):
            self.captcha_error_count = 0
            return response
        try:
            response.json()
        except ValueError as err:
            # Status Code == 403 and no json contend --> Blocked due to rate limit / wrong user_agent.
            # Get latest APK Version from google and retry
            if response.status_code == 403 and retry < max_retries:
                self.user_agent = self._get_user_agent()
                return self._post(path, retry=retry + 1, **kwargs)
            self.captcha_error_count += 1
            raise TgtgCaptchaError(response.status_code, response.content) from err
        raise TgtgAPIError(response.status_code, response.content)

    def _get_user_agent(self) -> str:
        if self.fixed_user_agent:
            return self.fixed_user_agent
        version = DEFAULT_APK_VERSION
        try:
            version = self.get_latest_apk_version()
        except Exception:
            log.warning("Failed to get latest APK version!")
        log.debug("Using APK version %s.", version)
        return random.choice(USER_AGENTS).format(version)

    @staticmethod
    def get_latest_apk_version() -> str:
        response = requests.get(
            "https://play.google.com/store/apps/details?id=com.app.tgtg&hl=en&gl=US",
            timeout=30)
        match = APK_RE_SCRIPT.search(response.text)
        data = json.loads(match.group(1))
        return data[1][2][140][0][0][0]

    @property
    def _headers(self) -> dict:
        headers = {
            "user-agent": self.user_agent,
            "accept-language": self.language,
            "Accept-Encoding": "gzip",
        }
        if self.access_token:
            headers["authorization"] = f"Bearer {self.access_token}"
        return headers

    @property
    def _already_logged(self) -> bool:
        return bool(self.access_token and self.refresh_token and self.user_id)

    def _refresh_token(self) -> None:
        if (
            self.last_time_token_refreshed
            and (datetime.datetime.now() - self.last_time_token_refreshed).seconds
            <= self.access_token_lifetime
        ):
            return
        response = self._post(
            REFRESH_ENDPOINT, json={"refresh_token": self.refresh_token}
        )
        self.access_token = response.json()["access_token"]
        self.refresh_token = response.json()["refresh_token"]
        self.last_time_token_refreshed = datetime.datetime.now()

    def login(self) -> None:
        if not (
            self.email or self.access_token and self.refresh_token and self.user_id
        ):
            raise TGTGConfigurationError(
                "You must provide at least email or access_token, refresh_token and user_id"
            )
        if self._already_logged:
            self._refresh_token()
        else:
            response = self._post(
                AUTH_BY_EMAIL_ENDPOINT,
                json={
                    "device_type": self.device_type,
                    "email": self.email,
                },
            )
            first_login_response = response.json()
            if first_login_response["state"] == "TERMS":
                raise TgtgPollingError(
                    f"This email {self.email} is not linked to a tgtg account. "
                    "Please signup with this email first."
                )
            if first_login_response["state"] == "WAIT":
                self.start_polling(first_login_response["polling_id"])
            else:
                raise TgtgLoginError(response.status_code, response.content)

    def start_polling(self, polling_id) -> None:
        for _ in range(self.max_polling_tries):
            response = self._post(
                AUTH_POLLING_ENDPOINT,
                json={
                    "device_type": self.device_type,
                    "email": self.email,
                    "request_polling_id": polling_id,
                },
            )
            if response.status_code == HTTPStatus.ACCEPTED:
                log.warning(
                    "Check your mailbox on PC to continue... "
                    "(Mailbox on mobile won't work, if you have installed tgtg app.)"
                )
                time.sleep(self.polling_wait_time)
                continue
            if response.status_code == HTTPStatus.OK:
                log.info("Logged in!")
                login_response = response.json()
                self.access_token = login_response["access_token"]
                self.refresh_token = login_response["refresh_token"]
                self.last_time_token_refreshed = datetime.datetime.now()
                self.user_id = login_response["startup_data"]["user"]["user_id"]
                return
        raise TgtgPollingError("Max polling retries reached. Try again.")

    def get_items(
        self,
        *,
        latitude=0.0,
        longitude=0.0,
        radius=21,
        page_size=20,
        page=1,
        discover=False,
        favorites_only=True,
        item_categories=None,
        diet_categories=None,
        pickup_earliest=None,
        pickup_latest=None,
        search_phrase=None,
        with_stock_only=False,
        hidden_only=False,
        we_care_only=False,
    ) -> dict:
        self.login()

        # fields are sorted like in the app
        data = {
            "user_id": self.user_id,
            "origin": {"latitude": latitude, "longitude": longitude},
            "radius": radius,
            "page_size": page_size,
            "page": page,
            "discover": discover,
            "favorites_only": favorites_only,
            "item_categories": item_categories if item_categories else [],
            "diet_categories": diet_categories if diet_categories else [],
            "pickup_earliest": pickup_earliest,
            "pickup_latest": pickup_latest,
            "search_phrase": search_phrase if search_phrase else None,
            "with_stock_only": with_stock_only,
            "hidden_only": hidden_only,
            "we_care_only": we_care_only,
        }
        response = self._post(API_ITEM_ENDPOINT, json=data)
        return response.json()["items"]

    def get_item(self, item_id) -> dict:
        self.login()
        response = self._post(
            f"{API_ITEM_ENDPOINT}/{item_id}",
            json={"user_id": self.user_id, "origin": None},
        )
        return response.json()

    def set_favorite(self, item_id, is_favorite) -> None:
        self.login()
        self._post(
            f"{API_ITEM_ENDPOINT}/{item_id}/setFavorite",
            json={"is_favorite": is_favorite},
        )

    def signup_by_email(
        self,
        *,
        email,
        name="",
        country_id="GB",
        newsletter_opt_in=False,
        push_notification_opt_in=True,
    ):
        response = self._post(
            SIGNUP_BY_EMAIL_ENDPOINT,
            json={
                "country_id": country_id,
                "device_type": self.device_type,
                "email": email,
                "name": name,
                "newsletter_opt_in": newsletter_opt_in,
                "push_notification_opt_in": push_notification_opt_in,
            },
        )
        self.access_token = response.json()["login_response"]["access_token"]
        self.refresh_token = response.json()["login_response"]["refresh_token"]
        self.last_time_token_refreshed = datetime.datetime.now()
        self.user_id = response.json()["login_response"]["startup_data"]["user"][
            "user_id"
        ]
        return self
