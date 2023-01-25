# copied and modified from https://github.com/ahivert/tgtg-python

import http.client as http_client
import json
import logging
import random
import re
import time
from datetime import datetime
from http import HTTPStatus
from typing import List
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from models.errors import (TgtgAPIError, TGTGConfigurationError,
                           TgtgLoginError, TgtgPollingError)

# set to 1 to debug http headers
http_client.HTTPConnection.debuglevel = 0
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
DEFAULT_APK_VERSION = "22.11.11"

APK_RE_SCRIPT = re.compile(
    r"AF_initDataCallback\({key:\s*'ds:5'.*?"
    r"data:([\s\S]*?), sideChannel:.+<\/script"
)


class TgtgSession(requests.Session):
    http_adapter = HTTPAdapter(
        max_retries=Retry(
            total=5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
            backoff_factor=1,
        )
    )

    def __init__(self, user_agent: str = None, language: str = "en-UK",
                 timeout: int = None, proxies: dict = None,
                 datadome_cookie: str = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.mount("https://", self.http_adapter)
        self.mount("http://", self.http_adapter)
        self.headers = {
            "user-agent": user_agent,
            "accept-language": language,
            "Accept-Encoding": "gzip",
        }
        self.timeout = timeout
        self.proxies = proxies
        if datadome_cookie:
            self.cookies.set("datadome", datadome_cookie,
                             domain=".apptoogoodtogo.com",
                             path="/", secure=True)

    def post(self, url: str, access_token: str = None, **kwargs
             ) -> requests.Response:
        headers = kwargs.get("headers")
        if headers is None and getattr(self, "headers"):
            kwargs["headers"] = getattr(self, "headers")
        if "headers" in kwargs and access_token:
            kwargs["headers"]["authorization"] = f"Bearer {access_token}"
        return super().post(url, **kwargs)

    def send(self, request, **kwargs):
        for key in ["timeout", "proxies"]:
            val = kwargs.get(key)
            if val is None and hasattr(self, key):
                kwargs[key] = getattr(self, key)
        return super().send(request, **kwargs)


class TgtgClient:
    def __init__(
        self,
        url=BASE_URL,
        email=None,
        access_token=None,
        refresh_token=None,
        user_id=None,
        datadome_cookie=None,
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
        self.datadome_cookie = datadome_cookie

        self.last_time_token_refreshed = None
        self.access_token_lifetime = access_token_lifetime
        self.max_polling_tries = max_polling_tries
        self.polling_wait_time = polling_wait_time

        self.device_type = device_type
        self.fixed_user_agent = user_agent
        self.user_agent = user_agent
        self.language = language
        self.proxies = proxies
        self.timeout = timeout
        self.session = None

        self.captcha_error_count = 0

    def __del__(self) -> None:
        if self.session:
            self.session.close()

    def _get_url(self, path) -> str:
        return urljoin(self.base_url, path)

    def _create_session(self) -> TgtgSession:
        if not self.user_agent:
            self.user_agent = self._get_user_agent()
        return TgtgSession(self.user_agent,
                           self.language,
                           self.timeout,
                           self.proxies,
                           self.datadome_cookie)

    def get_credentials(self) -> dict:
        """Returns current tgtg api credentials.

        Returns:
            dict: Dictionary containing access token, refresh token and user id
        """
        self.login()
        return {
            "email": self.email,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "user_id": self.user_id,
        }

    def _post(self, path, **kwargs) -> requests.Response:
        if not self.session:
            self.session = self._create_session()
        response = self.session.post(
            self._get_url(path),
            access_token=self.access_token,
            **kwargs,
        )
        self.datadome_cookie = self.session.cookies.get("datadome")
        if response.status_code in (HTTPStatus.OK, HTTPStatus.ACCEPTED):
            self.captcha_error_count = 0
            return response
        try:
            response.json()
        except ValueError:
            # Status Code == 403 and no json contend
            # --> Blocked due to rate limit / wrong user_agent.
            # 1. Get latest APK Version from google
            # 2. Reset current session
            # 3. Sleep 10 seconds, after 10 errors sleep 1 hour
            # 4. Rety request
            if response.status_code == 403:
                log.debug("Captcha Error 403!")
                if self.captcha_error_count == 1:
                    self.user_agent = self._get_user_agent()
                    self.session = self._create_session()
                self.captcha_error_count += 1
                if self.captcha_error_count > 10:
                    log.warning(
                        "Too many captcha Errors! Sleeping for 10 minutes...")
                    time.sleep(10 * 60)
                    log.info("Retrying ...")
                    self.captcha_error_count = 0
                    self.user_agent = self._get_user_agent()
                    self.session = self._create_session()
                time.sleep(1)
                return self._post(path, **kwargs)
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
        """Returns latest APK version of the official Android TGTG App.

        Returns:
            str: APK Version string
        """
        response = requests.get(
            "https://play.google.com/store/apps/"
            "details?id=com.app.tgtg&hl=en&gl=US",
            timeout=30,
        )
        match = APK_RE_SCRIPT.search(response.text)
        data = json.loads(match.group(1))
        return data[1][2][140][0][0][0]

    @property
    def _already_logged(self) -> bool:
        return bool(self.access_token and self.refresh_token and self.user_id)

    def _refresh_token(self) -> None:
        if (
            self.last_time_token_refreshed
            and (datetime.now() - self.last_time_token_refreshed).seconds
            <= self.access_token_lifetime
        ):
            return
        response = self._post(
            REFRESH_ENDPOINT,
            json={"refresh_token": self.refresh_token}
        )
        self.access_token = response.json().get("access_token")
        self.refresh_token = response.json().get("refresh_token")
        self.last_time_token_refreshed = datetime.now()

    def login(self) -> None:
        if not (self.email or
                self.access_token and
                self.refresh_token and
                self.user_id):
            raise TGTGConfigurationError(
                "You must provide at least email or access_token, "
                "refresh_token and user_id")
        if self._already_logged:
            self._refresh_token()
        else:
            log.info("Starting login process ...")
            response = self._post(
                AUTH_BY_EMAIL_ENDPOINT,
                json={
                    "device_type": self.device_type,
                    "email": self.email,
                }
            )
            first_login_response = response.json()
            if first_login_response["state"] == "TERMS":
                raise TgtgPollingError(
                    f"This email {self.email} is not linked to a tgtg "
                    "account. Please signup with this email first."
                )
            if first_login_response.get("state") == "WAIT":
                self.start_polling(first_login_response.get("polling_id"))
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
                }
            )
            if response.status_code == HTTPStatus.ACCEPTED:
                log.warning(
                    "Check your mailbox on PC to continue... "
                    "(Mailbox on mobile won't work, "
                    "if you have installed tgtg app.)"
                )
                time.sleep(self.polling_wait_time)
                continue
            if response.status_code == HTTPStatus.OK:
                log.info("Logged in!")
                login_response = response.json()
                self.access_token = login_response.get("access_token")
                self.refresh_token = login_response.get("refresh_token")
                self.last_time_token_refreshed = datetime.now()
                self.user_id = login_response.get(
                    "startup_data", {}).get("user", {}).get("user_id")
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
    ) -> List[dict]:
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
        return response.json().get("items", [])

    def get_item(self, item_id: str) -> dict:
        self.login()
        response = self._post(
            f"{API_ITEM_ENDPOINT}/{item_id}",
            json={"user_id": self.user_id, "origin": None},
        )
        return response.json()

    def set_favorite(self, item_id: str, is_favorite: bool) -> None:
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
            }
        )
        login_response = response.json().get("login_response", {})
        self.access_token = login_response.get("access_token")
        self.refresh_token = login_response.get("refresh_token")
        self.last_time_token_refreshed = datetime.now()
        self.user_id = login_response.get(
            "startup_data", {}).get("user", {}).get("user_id")
        return self
