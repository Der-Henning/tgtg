import unittest
from .constants import GLOBAL_PROPERTIES
from tgtg import TgtgClient
from os import environ

class TGTG_API_Test(unittest.TestCase):
    def test_get_items(self):
        client = TgtgClient(
            email=environ.get("TGTG_USERNAME", None),
            timeout=60,
            access_token=environ.get("TGTG_ACCESS_TOKEN", None),
            refresh_token=environ.get("TGTG_REFRESH_TOKEN", None),
            user_id=environ.get("TGTG_USER_ID", None),
        )

        print("Access Token: {}".format(environ.get("TGTG_ACCESS_TOKEN", None)))
        print("Refresh Token: {}".format(environ.get("TGTG_REFRESH_TOKEN", None)))
        print("User ID: {}".format(environ.get("TGTG_USER_ID", None)))

        ## get credentials and safe tokens to GITHUB_ENV file
        ## this enables github workflow to reuse the access_token on sheduled runs
        credentials = client.get_credentials()
        env_file = environ.get('GITHUB_ENV', None)
        if env_file:
            with open(env_file, "a") as file:
                file.write("TGTG_ACCESS_TOKEN={}\n".format(credentials["access_token"]))
                file.write("TGTG_REFRESH_TOKEN={}\n".format(credentials["refresh_token"]))
                file.write("TGTG_USER_ID={}\n".format(credentials["user_id"]))
        
        data = client.get_items(favorites_only=True)
        assert len(data) > 0
        for property in GLOBAL_PROPERTIES:
            assert property in data[0]