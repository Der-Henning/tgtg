import pathlib

from models import Config
from tgtg import TgtgClient


def test_get_items(item_properties: dict):
    if pathlib.Path('src/config.ini').exists():
        config = Config('src/config.ini')
    else:
        config = Config()

    client = TgtgClient(
        email=config.tgtg.get("username"),
        timeout=config.tgtg.get("timeout"),
        access_token_lifetime=config.tgtg.get("access_token_lifetime"),
        max_polling_tries=config.tgtg.get("max_polling_tries"),
        polling_wait_time=config.tgtg.get("polling_wait_time"),
        access_token=config.tgtg.get("access_token"),
        refresh_token=config.tgtg.get("refresh_token"),
        user_id=config.tgtg.get("user_id")
    )

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
