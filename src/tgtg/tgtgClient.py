## copied from https://github.com/ahivert/tgtg-python

import datetime
import random
import logging as log
from http import HTTPStatus
from urllib.parse import urljoin
import requests
from models import TgtgAPIError, TgtgLoginError

BASE_URL = "https://apptoogoodtogo.com/api/"
API_ITEM_ENDPOINT = "item/v7/"
LOGIN_ENDPOINT = "auth/v1/loginByEmail"
SIGNUP_BY_EMAIL_ENDPOINT = "auth/v2/signUpByEmail"
REFRESH_ENDPOINT = "auth/v1/token/refresh"
ALL_BUSINESS_ENDPOINT = "map/v1/listAllBusinessMap"
USER_AGENTS = [
    "TGTG/20.12.3 Dalvik/2.1.0 (Linux; U; Android 6.0.1; Nexus 5 Build/M4B30Z)",
    "TGTG/20.12.3 Dalvik/2.1.0 (Linux; U; Android 7.0; SM-G935F Build/NRD90M)",
    "TGTG/20.12.3 Dalvik/2.1.0 (Linux; Android 6.0.1; SM-G920V Build/MMB29K)",
]
DEFAULT_ACCESS_TOKEN_LIFETIME = 3600 * 4  # 4 hours


class TgtgClient:
    def __init__(
        self,
        url=BASE_URL,
        email=None,
        password=None,
        access_token=None,
        user_id=None,
        user_agent=None,
        language="en-UK",
        proxies=None,
        timeout=None,
        access_token_lifetime=DEFAULT_ACCESS_TOKEN_LIFETIME,
    ):
        self.base_url = url

        self.email = email
        self.password = password

        self.access_token = access_token
        if self.access_token is not None:
            log.warn("'access_token' is deprecated; use 'email' and 'password'")
        self.refresh_token = None
        self.last_time_token_refreshed = None
        self.access_token_lifetime = access_token_lifetime

        self.user_id = user_id
        if self.user_id is not None:
            log.warn("'user_id' is deprecated; use 'email' and 'password'")
        #self.user_agent = user_agent if user_agent else random.choice(USER_AGENTS)
        self.user_agent = None
        self.language = language
        self.proxies = proxies
        self.timeout = timeout

    def _get_url(self, path):
        return urljoin(self.base_url, path)

    @property
    def _headers(self):
        headers = {"user-agent": self.user_agent, "accept-language": self.language}
        if self.access_token:
            headers["authorization"] = f"Bearer {self.access_token}"
        return headers

    @property
    def _already_logged(self):
        return bool(self.access_token and self.user_id)

    def _refresh_token(self):
        if (
            self.last_time_token_refreshed
            and (datetime.datetime.now() - self.last_time_token_refreshed).seconds
            <= self.access_token_lifetime
        ):
            return

        response = requests.post(
            self._get_url(REFRESH_ENDPOINT),
            headers=self._headers,
            json={"refresh_token": self.refresh_token},
            proxies=self.proxies,
            timeout=self.timeout,
        )
        if response.status_code == HTTPStatus.OK:
            self.access_token = response.json()["access_token"]
            self.refresh_token = response.json()["refresh_token"]
            self.last_time_token_refreshed = datetime.datetime.now()
        else:
            raise TgtgAPIError(response.status_code, response.content)

    def _login(self):
        if self._already_logged:
            self._refresh_token()
        else:
            if not self.email or not self.password:
                raise ValueError(
                    "You must fill email and password or access_token and user_id"
                )

            response = requests.post(
                self._get_url(LOGIN_ENDPOINT),
                headers=self._headers,
                json={
                    "device_type": "ANDROID",
                    "email": self.email,
                    "password": self.password,
                },
                proxies=self.proxies,
                timeout=self.timeout,
            )
            if response.status_code == HTTPStatus.OK:
                login_response = response.json()
                self.access_token = login_response["access_token"]
                self.refresh_token = login_response["refresh_token"]
                self.last_time_token_refreshed = datetime.datetime.now()
                self.user_id = login_response["startup_data"]["user"]["user_id"]
            else:
                raise TgtgLoginError(response.status_code, response.content)

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
    ):
        self._login()

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
        response = requests.post(
            self._get_url(API_ITEM_ENDPOINT),
            headers=self._headers,
            json=data,
            proxies=self.proxies,
            timeout=self.timeout,
        )
        if response.status_code == HTTPStatus.OK:
            return response.json()["items"]
        else:
            raise TgtgAPIError(response.status_code, response.content)

    def get_item(self, item_id):
        self._login()
        response = requests.post(
            urljoin(self._get_url(API_ITEM_ENDPOINT), str(item_id)),
            headers=self._headers,
            json={"user_id": self.user_id, "origin": None},
            proxies=self.proxies,
            timeout=self.timeout,
        )
        if response.status_code == HTTPStatus.OK:
            return response.json()
        else:
            raise TgtgAPIError(response.status_code, response.content)

    def set_favorite(self, item_id, is_favorite):
        self._login()
        response = requests.post(
            urljoin(self._get_url(API_ITEM_ENDPOINT), f"{item_id}/setFavorite"),
            headers=self._headers,
            json={"is_favorite": is_favorite},
            proxies=self.proxies,
            timeout=self.timeout,
        )
        if response.status_code != HTTPStatus.OK:
            raise TgtgAPIError(response.status_code, response.content)

    def signup_by_email(
        self,
        *,
        email,
        password,
        name,
        country_id="GB",
        device_type="ANDROID",
        newsletter_opt_in=False,
        push_notification_opt_in=True,
    ):
        response = requests.post(
            self._get_url(SIGNUP_BY_EMAIL_ENDPOINT),
            headers=self._headers,
            json={
                "country_id": country_id,
                "device_type": device_type,
                "email": email,
                "name": name,
                "newsletter_opt_in": newsletter_opt_in,
                "password": password,
                "push_notification_opt_in": push_notification_opt_in,
            },
            proxies=self.proxies,
            timeout=self.timeout,
        )
        if response.status_code == HTTPStatus.OK:
            self.access_token = response.json()["access_token"]
            self.refresh_token = response.json()["refresh_token"]
            self.last_time_token_refreshed = datetime.datetime.now()
            self.user_id = response.json()["startup_data"]["user"]["user_id"]
            return self
        else:
            raise TgtgAPIError(response.status_code, response.content)