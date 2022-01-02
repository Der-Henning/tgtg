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
        env_file = environ.get('GITHUB_ENV', None)
        if env_file:
            with open(env_file, "a") as myfile:
                myfile.write("TGTG_ACCESS_TOKEN={}\n".format(credentials["access_token"]))
                myfile.write("TGTG_REFRESH_TOKEN={}\n".format(credentials["refresh_token"]))
                myfile.write("TGTG_USER_ID={}\n".format(credentials["user_id"]))
        data = client.get_items(favorites_only=True)
        assert len(data) > 0
        for property in GLOBAL_PROPERTIES:
            assert property in data[0]