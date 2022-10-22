from os import environ
from tgtg import TgtgClient


def login():
    """Login function for Github CI
    """
    username = environ.get("TGTG_USERNAME", None)
    env_file = environ.get("GITHUB_ENV", None)
    timeout = environ.get("TGTG_TIMEOUT", 60)
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
    credentials = client.get_credentials()
    if env_file:
        with open(env_file, "a", encoding="utf-8") as file:
            file.write(f"TGTG_ACCESS_TOKEN={credentials['access_token']}\n")
            file.write(f"TGTG_REFRESH_TOKEN={credentials['refresh_token']}\n")
            file.write(f"TGTG_USER_ID={credentials['user_id']}\n")


if __name__ == "__main__":
    login()
