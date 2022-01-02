import unittest
from .constants import GLOBAL_PROPERTIES
from tgtg import TgtgClient
from os import environ

class TGTG_API_Test(unittest.TestCase):
    def test_get_items(self):
        client = TgtgClient(
            email=environ.get("TGTG_USERNAME", None),
            access_token=environ.get("TGTG_ACCESS_TOKEN", None),
            refresh_token=environ.get("TGTG_REFRESH_TOKEN", None),
            user_id=environ.get("TGTG_USER_ID", None),
        )
        credentials = client.get_credentials()
        print(credentials)
        environ["TGTG_ACCESS_TOKEN"] = credentials["access_token"]
        environ["TGTG_REFRESH_TOKEN"] = credentials["refresh_token"]
        environ["TGTG_USER_ID"] = credentials["user_id"]

        data = client.get_items(favorites_only=True)
        assert len(data) > 0
        for property in GLOBAL_PROPERTIES:
            assert property in data[0]