import unittest
from os import environ
import cryptocode
from tgtg import TgtgClient
from .constants import GLOBAL_PROPERTIES, ITEM_PROPERTIES, PRICE_PROPERTIES


class TGTGAPITest(unittest.TestCase):
    def test_get_items(self):
        passkey = environ.get("REPO_ACCESS_TOKEN")
        username = environ.get("TGTG_USERNAME", None)
        env_file = environ.get("GITHUB_ENV", None)
        timeout = environ.get("TGTG_TIMEOUT", 60)

        if passkey:
            encrypted_access_token = environ.get("TGTG_ACCESS_TOKEN", None)
            encrypted_refresh_token = environ.get("TGTG_REFRESH_TOKEN", None)
            encrypted_user_id = environ.get("TGTG_USER_ID", None)
            access_token = (
                cryptocode.decrypt(encrypted_access_token, passkey)
                if encrypted_access_token
                else None
            )
            refresh_token = (
                cryptocode.decrypt(encrypted_refresh_token, passkey)
                if encrypted_refresh_token
                else None
            )
            user_id = (
                cryptocode.decrypt(encrypted_user_id, passkey)
                if encrypted_user_id
                else None
            )
        else:
            access_token = environ.get("TGTG_ACCESS_TOKEN", None)
            refresh_token = environ.get("TGTG_REFRESH_TOKEN", None)
            user_id = environ.get("TGTG_USER_ID", None)

        client = TgtgClient(
            email=username,
            timeout=timeout,
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=user_id,
        )

        # get credentials and safe tokens to GITHUB_ENV file
        # this enables github workflow to reuse the access_token on sheduled runs
        # the credentials are encrypted with the REPO_ACCESS_TOKEN
        credentials = client.get_credentials()
        if env_file:
            with open(env_file, "a", encoding="utf-8") as file:
                file.write(
                    f"TGTG_ACCESS_TOKEN={cryptocode.encrypt(credentials['access_token'], passkey)}\n"
                )
                file.write(
                    f"TGTG_REFRESH_TOKEN={cryptocode.encrypt(credentials['refresh_token'], passkey)}\n"
                )
                file.write(
                    f"TGTG_USER_ID={cryptocode.encrypt(credentials['user_id'], passkey)}\n"
                )

        # Tests
        items = client.get_items(favorites_only=True)
        assert len(items) > 0
        item = items[0]
        item_id = item["item"]["item_id"]
        for prop in GLOBAL_PROPERTIES:
            assert prop in item
        for prop in ITEM_PROPERTIES:
            assert prop in item["item"]
        for prop in PRICE_PROPERTIES:
            assert prop in item["item"]["price_including_taxes"]

        client.set_favorite(item_id, False)
        client.set_favorite(item_id, True)

        item = client.get_item(item_id)

        assert item["item"]["item_id"] == item_id
