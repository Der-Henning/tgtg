import configparser
from pathlib import Path

import pytest

from models import Config
from models.config import DEFAULT_CONFIG


def test_default_ini_config():
    config = Config("")
    for key in DEFAULT_CONFIG:
        assert hasattr(config, key)
        assert getattr(config, key) == DEFAULT_CONFIG.get(key)


def test_default_env_config():
    config = Config()
    for key in DEFAULT_CONFIG:
        assert hasattr(config, key)
        assert getattr(config, key) == DEFAULT_CONFIG.get(key)


def test_config_set(temp_path: Path):
    config_path = Path(temp_path, "config.ini")
    config_path.touch(exist_ok=True)
    config = Config(config_path.absolute())

    assert config.set("MAIN", "debug", True)

    config_parser = configparser.ConfigParser()
    config_parser.read(config_path, encoding='utf-8')

    assert config_parser.getboolean("MAIN", "debug")


def test_save_tokens_to_ini(temp_path: Path):
    config_path = Path(temp_path, "config.ini")
    config_path.touch(exist_ok=True)
    config = Config(config_path.absolute())
    config.save_tokens("test_access_token", "test_refresh_token",
                       "test_user_id", "test_cookie")

    config_parser = configparser.ConfigParser()
    config_parser.read(config_path, encoding='utf-8')

    assert config_parser.get("TGTG", "AccessToken") == "test_access_token"
    assert config_parser.get("TGTG", "RefreshToken") == "test_refresh_token"
    assert config_parser.get("TGTG", "UserId") == "test_user_id"
    assert config_parser.get("TGTG", "Datadome") == "test_cookie"


def test_token_path(temp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TGTG_TOKEN_PATH", str(temp_path.absolute()))

    config = Config()
    config.save_tokens("test_access_token", "test_refresh_token",
                       "test_user_id", "test_cookie")
    config._load_tokens()

    assert config.tgtg.get("access_token") == "test_access_token"
    assert config.tgtg.get("refresh_token") == "test_refresh_token"
    assert config.tgtg.get("user_id") == "test_user_id"
    assert config.tgtg.get("datadome") == "test_cookie"
