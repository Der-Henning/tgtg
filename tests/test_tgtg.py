import pathlib

from models import Config
from tgtg import TgtgClient


def test_get_items(properties: dict):
    if pathlib.Path('src/config.ini').exists():
        config = Config('src/config.ini')
    else:
        config = Config()

    client = TgtgClient(
        email=config.tgtg["username"],
        timeout=config.tgtg["timeout"],
        access_token_lifetime=config.tgtg["access_token_lifetime"],
        max_polling_tries=config.tgtg["max_polling_tries"],
        polling_wait_time=config.tgtg["polling_wait_time"],
        access_token=config.tgtg["access_token"],
        refresh_token=config.tgtg["refresh_token"],
        user_id=config.tgtg["user_id"],
    )

    # Tests
    items = client.get_items(favorites_only=True)
    assert len(items) > 0
    item = items[0]
    item_id = item["item"]["item_id"]
    for prop in properties.get("GLOBAL_PROPERTIES", []):
        assert prop in item
    for prop in properties.get("ITEM_PROPERTIES", []):
        assert prop in item["item"]
    for prop in properties.get("PRICE_PROPERTIES", []):
        assert prop in item["item"]["price_including_taxes"]

    client.set_favorite(item_id, False)
    client.set_favorite(item_id, True)

    item = client.get_item(item_id)

    assert item["item"]["item_id"] == item_id
