import json
import pathlib
import re
from os import environ
from urllib.parse import urljoin

import pytest
import responses
from pytest_mock.plugin import MockerFixture

from tgtg_scanner.models import Config
from tgtg_scanner.tgtg.tgtg_client import (
    API_ITEM_ENDPOINT,
    AUTH_BY_EMAIL_ENDPOINT,
    AUTH_POLLING_ENDPOINT,
    BASE_URL,
    FAVORITE_ITEM_ENDPOINT,
    REFRESH_ENDPOINT,
    USER_AGENTS,
    TgtgClient,
)


def test_get_latest_apk_version():
    pattern = re.compile("^[0-9]+.[0-9]+.[0-9]+$")
    apk_version = TgtgClient.get_latest_apk_version()
    assert pattern.match(apk_version)


def test_get_user_agent(mocker: MockerFixture):
    apk_version = "22.11.11"
    mocker.patch(
        "tgtg_scanner.tgtg.tgtg_client.TgtgClient.get_latest_apk_version",
        return_value=apk_version,
    )
    client = TgtgClient(email="test@example.com")
    user_agent = client._get_user_agent()
    assert user_agent in [agent.format(apk_version) for agent in USER_AGENTS]


@responses.activate
def test_tgtg_login_with_mail(mocker: MockerFixture):
    mocker.patch(
        "tgtg_scanner.tgtg.tgtg_client.TgtgClient.get_latest_apk_version",
        return_value="22.11.11",
    )
    client = TgtgClient(email="test@example.com", polling_wait_time=1)
    auth_response_data = {
        "state": "WAIT",
        "polling_id": "009350f7-650a-43d0-ab2c-2ff0676c9626",
    }
    poll_response_data = {
        "access_token": "new_access_token",
        "access_token_ttl_seconds": 172800,
        "refresh_token": "new_refresh_token",
    }
    responses.add(
        responses.POST,
        urljoin(BASE_URL, AUTH_BY_EMAIL_ENDPOINT),
        json.dumps(auth_response_data),
        status=200,
    )
    responses.add(
        responses.POST,
        urljoin(BASE_URL, AUTH_POLLING_ENDPOINT),
        status=202,
    )
    responses.add(
        responses.POST,
        urljoin(BASE_URL, AUTH_POLLING_ENDPOINT),
        json.dumps(poll_response_data),
        status=200,
    )
    client.login()
    assert client.access_token == poll_response_data.get("access_token")
    assert client.refresh_token == poll_response_data.get("refresh_token")
    assert json.loads(responses.calls[1].request.body) == {
        "device_type": client.device_type,
        "email": client.email,
        "request_polling_id": auth_response_data.get("polling_id"),
    }


@responses.activate
def test_tgtg_login_with_token(mocker: MockerFixture):
    mocker.patch(
        "tgtg_scanner.tgtg.tgtg_client.TgtgClient.get_latest_apk_version",
        return_value="22.11.11",
    )
    client = TgtgClient(
        email="test@example.com",
        access_token="old_access_token",
        refresh_token="old_refresh_token",
    )
    response_data = {
        "access_token": "new_access_token",
        "access_token_ttl_seconds": 172800,
        "refresh_token": "new_refresh_token",
    }
    responses.add(
        responses.POST,
        urljoin(BASE_URL, REFRESH_ENDPOINT),
        json.dumps(response_data),
        status=200,
    )
    client.login()
    assert client.access_token == response_data.get("access_token")
    assert client.refresh_token == response_data.get("refresh_token")


@responses.activate
def test_tgtg_get_items(mocker: MockerFixture, tgtg_item: dict):
    mocker.patch(
        "tgtg_scanner.tgtg.tgtg_client.TgtgClient.get_latest_apk_version",
        return_value="22.11.11",
    )
    mocker.patch("tgtg_scanner.tgtg.tgtg_client.TgtgClient.login", return_value=None)
    responses.add(
        responses.POST,
        urljoin(BASE_URL, API_ITEM_ENDPOINT),
        json.dumps({"items": [tgtg_item]}),
        status=200,
    )
    client = TgtgClient(
        email="test@example.com",
        access_token="access_token",
        refresh_token="refresh_token",
    )
    response = client.get_items(favorites_only=True)
    assert response == [tgtg_item]


@responses.activate
def test_tgtg_get_item(mocker: MockerFixture, tgtg_item: dict):
    mocker.patch(
        "tgtg_scanner.tgtg.tgtg_client.TgtgClient.get_latest_apk_version",
        return_value="22.11.11",
    )
    mocker.patch("tgtg_scanner.tgtg.tgtg_client.TgtgClient.login", return_value=None)
    item_id = tgtg_item.get("item", {}).get("item_id")
    responses.add(
        responses.POST,
        urljoin(BASE_URL, API_ITEM_ENDPOINT + item_id),
        json.dumps(tgtg_item),
        status=200,
    )
    client = TgtgClient(
        email="test@example.com",
        access_token="access_token",
        refresh_token="refresh_token",
    )
    response = client.get_item(item_id)
    assert response == tgtg_item


@responses.activate
def test_tgtg_set_favorite(mocker: MockerFixture):
    mocker.patch(
        "tgtg_scanner.tgtg.tgtg_client.TgtgClient.get_latest_apk_version",
        return_value="22.11.11",
    )
    mocker.patch("tgtg_scanner.tgtg.tgtg_client.TgtgClient.login", return_value=None)
    item_id = "12345"
    responses.add(
        responses.POST,
        urljoin(BASE_URL, FAVORITE_ITEM_ENDPOINT.format(item_id)),
        json.dumps({"is_favorite": True}),
        status=200,
    )
    client = TgtgClient(
        email="test@example.com",
        access_token="access_token",
        refresh_token="refresh_token",
    )
    client.set_favorite(item_id, True)
    assert json.loads(responses.calls[0].request.body) == {"is_favorite": True}


@pytest.mark.tgtg_api
def test_tgtg_api(item_properties: dict):
    if pathlib.Path("config.ini").is_file():
        config = Config("config.ini")
    else:
        config = Config()

    env_file = environ.get("GITHUB_ENV", None)

    client = TgtgClient(
        email=config.tgtg.username,
        timeout=config.tgtg.timeout,
        access_token_lifetime=config.tgtg.access_token_lifetime,
        max_polling_tries=config.tgtg.max_polling_tries,
        polling_wait_time=config.tgtg.polling_wait_time,
        access_token=config.tgtg.access_token,
        refresh_token=config.tgtg.refresh_token,
        datadome_cookie=config.tgtg.datadome,
    )

    # get credentials and safe tokens to GITHUB_ENV file
    # this enables github workflow to reuse the access_token on sheduled runs
    if env_file:
        credentials = client.get_credentials()
        with open(env_file, "a", encoding="utf-8") as file:
            file.write(f"TGTG_ACCESS_TOKEN={credentials['access_token']}\n")
            file.write(f"TGTG_REFRESH_TOKEN={credentials['refresh_token']}\n")
            file.write(f"TGTG_COOKIE={credentials['datadome_cookie']}\n")

    # Tests
    items = client.get_items(favorites_only=True)
    assert len(items) > 0
    item = items[0]
    item_id = item.get("item", {}).get("item_id")
    for prop in item_properties.get("GLOBAL_PROPERTIES", []):
        assert prop in item
    for prop in item_properties.get("ITEM_PROPERTIES", []):
        assert prop in item.get("item", {})
    for prop in item_properties.get("PRICE_PROPERTIES", []):
        assert prop in item.get("item", {}).get("price_including_taxes")

    client.set_favorite(item_id, False)
    client.set_favorite(item_id, True)

    item = client.get_item(item_id)

    assert item.get("item", {}).get("item_id") == item_id
