import configparser
from importlib import reload
from pathlib import Path

import pytest

import models.config
from models.cron import Cron


def test_default_ini_config():
    reload(models.config)
    config = models.config.Config("")
    for key in models.config.DEFAULT_CONFIG:
        assert hasattr(config, key)
        assert getattr(config, key) == models.config.DEFAULT_CONFIG.get(key)


def test_default_env_config():
    reload(models.config)
    config = models.config.Config()
    for key in models.config.DEFAULT_CONFIG:
        assert hasattr(config, key)
        assert getattr(config, key) == models.config.DEFAULT_CONFIG.get(key)


def test_config_set(temp_path: Path):
    reload(models.config)
    config_path = Path(temp_path, "config.ini")
    config_path.touch(exist_ok=True)
    config = models.config.Config(config_path.absolute())

    assert config.set("MAIN", "debug", True)

    config_parser = configparser.ConfigParser()
    config_parser.read(config_path, encoding='utf-8')

    assert config_parser.getboolean("MAIN", "debug")


def test_save_tokens_to_ini(temp_path: Path):
    reload(models.config)
    config_path = Path(temp_path, "config.ini")
    config_path.touch(exist_ok=True)
    config = models.config.Config(config_path.absolute())
    config.save_tokens("test_access_token", "test_refresh_token",
                       "test_user_id", "test_cookie")

    config_parser = configparser.ConfigParser()
    config_parser.read(config_path, encoding='utf-8')

    assert config_parser.get("TGTG", "AccessToken") == "test_access_token"
    assert config_parser.get("TGTG", "RefreshToken") == "test_refresh_token"
    assert config_parser.get("TGTG", "UserId") == "test_user_id"
    assert config_parser.get("TGTG", "Datadome") == "test_cookie"


def test_token_path(temp_path: Path, monkeypatch: pytest.MonkeyPatch):
    reload(models.config)
    monkeypatch.setenv("TGTG_TOKEN_PATH", str(temp_path.absolute()))

    config = models.config.Config()
    config.save_tokens("test_access_token", "test_refresh_token",
                       "test_user_id", "test_cookie")
    config._load_tokens()

    assert config.tgtg.get("access_token") == "test_access_token"
    assert config.tgtg.get("refresh_token") == "test_refresh_token"
    assert config.tgtg.get("user_id") == "test_user_id"
    assert config.tgtg.get("datadome") == "test_cookie"


def test_ini_get(temp_path: Path):
    reload(models.config)
    config_path = Path(temp_path, "config.ini")

    with open(config_path, 'w', encoding='utf-8') as file:
        file.writelines([
            "[MAIN]\n",
            "Debug = true\n",
            "ItemIDs = 23423, 32432, 234532\n",
            "[WEBHOOK]\n",
            "timeout = 42\n",
            'headers = {"Accept": "json"}\n',
            "cron = * * 1-5 * *\n",
            'body = {"content": "${{items_available}} panier(s) à '
            '${{price}} € \\nÀ récupérer"}'
        ])

    config = models.config.Config(config_path.absolute())

    assert config.debug is True
    assert config.item_ids == ["23423", "32432", "234532"]
    assert config.webhook.get("timeout") == 42
    assert config.webhook.get("headers") == {"Accept": "json"}
    assert config.webhook.get("cron") == Cron("* * 1-5 * *")
    assert config.webhook.get("body") == ('{"content": "${{items_available}} '
                                          'panier(s) à ${{price}} € \n'
                                          'À récupérer"}')


def test_env_get(monkeypatch: pytest.MonkeyPatch):
    reload(models.config)
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("ITEM_IDS", "23423, 32432, 234532")
    monkeypatch.setenv("WEBHOOK_TIMEOUT", "42")
    monkeypatch.setenv("WEBHOOK_HEADERS", '{"Accept": "json"}')
    monkeypatch.setenv("WEBHOOK_CRON", "* * 1-5 * *")
    monkeypatch.setenv("WEBHOOK_BODY", '{"content": "${{items_available}} '
                       'panier(s) à ${{price}} € \\nÀ récupérer"}')

    config = models.config.Config()

    assert config.debug is True
    assert config.item_ids == ["23423", "32432", "234532"]
    assert config.webhook.get("timeout") == 42
    assert config.webhook.get("headers") == {"Accept": "json"}
    assert config.webhook.get("cron") == Cron("* * 1-5 * *")
    assert config.webhook.get("body") == ('{"content": "${{items_available}} '
                                          'panier(s) à ${{price}} € \n'
                                          'À récupérer"}')
