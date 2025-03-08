import configparser
import platform
import tempfile
from uuid import uuid4

import pytest

from tgtg_scanner.models import Config, Cron

SYS_PLATFORM = platform.system()
IS_WINDOWS = SYS_PLATFORM.lower() in {"windows", "cygwin"}


def test_default_ini_config():
    with tempfile.NamedTemporaryFile(delete=not IS_WINDOWS) as temp_file:
        config = Config(temp_file.name)
        assert hasattr(config, "metrics_port")
        assert config.metrics_port == 8000


def test_default_env_config():
    config = Config()
    assert hasattr(config, "metrics_port")
    assert config.metrics_port == 8000


def test_config_set():
    with tempfile.NamedTemporaryFile(delete=not IS_WINDOWS) as temp_file:
        config = Config(temp_file.name)

        assert config.set("MAIN", "debug", True)

        config_parser = configparser.ConfigParser()
        config_parser.read(temp_file.name, encoding="utf-8")

        assert config_parser.getboolean("MAIN", "debug")


def test_save_tokens_to_ini():
    with tempfile.NamedTemporaryFile(delete=not IS_WINDOWS) as temp_file:
        access_token = uuid4().hex
        refresh_token = uuid4().hex
        datadome = uuid4().hex
        config = Config(temp_file.name)
        config.save_tokens(access_token, refresh_token, datadome)

        config_parser = configparser.ConfigParser()
        config_parser.read(temp_file.name, encoding="utf-8")

        assert config_parser.get("TGTG", "AccessToken") == access_token
        assert config_parser.get("TGTG", "RefreshToken") == refresh_token
        assert config_parser.get("TGTG", "Datadome") == datadome


def test_token_path(monkeypatch: pytest.MonkeyPatch):
    with tempfile.TemporaryDirectory() as temp_dir:
        monkeypatch.setenv("TGTG_TOKEN_PATH", temp_dir)
        access_token = uuid4().hex
        refresh_token = uuid4().hex
        datadome = uuid4().hex
        config = Config()
        config.save_tokens(access_token, refresh_token, datadome)
        config._load_tokens()

        assert config.tgtg.access_token == access_token
        assert config.tgtg.refresh_token == refresh_token
        assert config.tgtg.datadome == datadome


def test_ini_get():
    with tempfile.NamedTemporaryFile(delete=not IS_WINDOWS) as temp_file:
        content = (
            "[MAIN]\n"
            "Debug = true\n"
            "ItemIDs = 23423, 32432, 234532\n"
            "[WEBHOOK]\n"
            "timeout = 42\n"
            'headers = {"Accept": "json"}\n'
            "cron = * * 1-5 * *\n"
            'body = {"content": "${{items_available}} panier(s) à ${{price}} € \\nÀ récupérer 🍔"}'
        )

        temp_file.write(content.encode("utf-8"))
        temp_file.seek(0)
        config = Config(temp_file.name)

        assert config.debug is True
        assert config.item_ids == ["23423", "32432", "234532"]
        assert config.webhook.timeout == 42
        assert config.webhook.headers == {"Accept": "json"}
        assert config.webhook.cron == Cron("* * 1-5 * *")
        assert config.webhook.body == '{"content": "${{items_available}} panier(s) à ${{price}} € \nÀ récupérer 🍔"}'


def test_env_get(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("ITEM_IDS", "23423, 32432, 234532")
    monkeypatch.setenv("WEBHOOK_TIMEOUT", "42")
    monkeypatch.setenv("WEBHOOK_HEADERS", '{"Accept": "json"}')
    monkeypatch.setenv("WEBHOOK_CRON", "* * 1-5 * *")
    monkeypatch.setenv("WEBHOOK_BODY", '{"content": "${{items_available}} panier(s) à ${{price}} € \\nÀ récupérer 🍔"}')

    config = Config()

    assert config.debug is True
    assert config.item_ids == ["23423", "32432", "234532"]
    assert config.webhook.timeout == 42
    assert config.webhook.headers == {"Accept": "json"}
    assert config.webhook.cron == Cron("* * 1-5 * *")
    assert config.webhook.body == '{"content": "${{items_available}} panier(s) à ${{price}} € \nÀ récupérer 🍔"}'
