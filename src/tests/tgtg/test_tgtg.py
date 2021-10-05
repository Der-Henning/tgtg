import unittest
from .constants import GLOBAL_PROPERTIES, ITEM_PROPERTIES, STORE_PROPERTIES
from tgtg import TgtgClient
from os import environ

class TGTG_API_Test(unittest.TestCase):
    def test_get_items(self):
        client = TgtgClient(
            email=environ["TGTG_EMAIL"], password=environ["TGTG_PASSWORD"]
        )
        data = client.get_items(
            favorites_only=True
        )
        assert len(data) > 0
        for property in GLOBAL_PROPERTIES:
            assert property in data[0]


    def test_get_one_item(self):
        client = TgtgClient(
            email=environ["TGTG_EMAIL"], password=environ["TGTG_PASSWORD"]
        )
        item_id = "36684"
        data = client.get_item(item_id)

        for property in GLOBAL_PROPERTIES:
            assert property in data
        for property in ITEM_PROPERTIES:
            assert property in data["item"]
        for property in STORE_PROPERTIES:
            assert property in data["store"]

        assert data["item"]["item_id"] == item_id