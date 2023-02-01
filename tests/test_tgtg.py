import pathlib
from os import environ

import pytest

from models import Config
from tgtg import TgtgClient


@pytest.mark.tgtg_api
def test_get_items(item_properties: dict):
    if pathlib.Path('src/config.ini').exists():
        config = Config('src/config.ini')
    else:
        config = Config()

    env_file = environ.get("GITHUB_ENV", None)

    client = TgtgClient(
        email=config.tgtg.get("username"),
        timeout=config.tgtg.get("timeout"),
        access_token_lifetime=config.tgtg.get("access_token_lifetime"),
        max_polling_tries=config.tgtg.get("max_polling_tries"),
        polling_wait_time=config.tgtg.get("polling_wait_time"),
        access_token=config.tgtg.get("access_token"),
        refresh_token=config.tgtg.get("refresh_token"),
        user_id=config.tgtg.get("user_id"),
        datadome_cookie=config.tgtg.get("datadome")
    )

    # get credentials and safe tokens to GITHUB_ENV file
    # this enables github workflow to reuse the access_token on sheduled runs
    if env_file:
        credentials = client.get_credentials()
        with open(env_file, "a", encoding="utf-8") as file:
            file.write(f"TGTG_ACCESS_TOKEN={credentials['access_token']}\n")
            file.write(f"TGTG_REFRESH_TOKEN={credentials['refresh_token']}\n")
            file.write(f"TGTG_USER_ID={credentials['user_id']}\n")
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
