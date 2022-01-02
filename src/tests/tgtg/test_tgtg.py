import unittest
from .constants import GLOBAL_PROPERTIES
from tgtg import TgtgClient
from os import environ
import cryptocode

class TGTG_API_Test(unittest.TestCase):
    def test_get_items(self):
        passkey = environ.get('REPO_ACCESS_TOKEN')

        encrypted_access_token = environ.get("TGTG_ACCESS_TOKEN", None)
        encrypted_refresh_token = environ.get("TGTG_REFRESH_TOKEN", None)
        encrypted_user_id = environ.get("TGTG_USER_ID", None)
        
        access_token = cryptocode.decrypt(encrypted_access_token, passkey) if encrypted_access_token else None
        refresh_token = cryptocode.decrypt(encrypted_refresh_token, passkey) if encrypted_refresh_token else None
        user_id = cryptocode.decrypt(encrypted_user_id, passkey) if encrypted_user_id else None

        client = TgtgClient(
            email=environ.get("TGTG_USERNAME", None),
            timeout=60,
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=user_id,
        )

        ## get credentials and safe tokens to GITHUB_ENV file
        ## this enables github workflow to reuse the access_token on sheduled runs
        ## the credentials are encrypted with the REPO_ACCESS_TOKEN
        credentials = client.get_credentials()
        env_file = environ.get('GITHUB_ENV', None)
        if env_file:
            with open(env_file, "a") as file:
                file.write("TGTG_ACCESS_TOKEN={}\n".format(cryptocode.encrypt(credentials["access_token"], passkey)))
                file.write("TGTG_REFRESH_TOKEN={}\n".format(cryptocode.encrypt(credentials["refresh_token"], passkey)))
                file.write("TGTG_USER_ID={}\n".format(cryptocode.encrypt(credentials["user_id"], passkey)))
        
        data = client.get_items(favorites_only=True)
        assert len(data) > 0
        for property in GLOBAL_PROPERTIES:
            assert property in data[0]