
import pytest

from models.cron import Cron
from models.errors import ConfigurationError


def test_description():
    assert Cron().get_description() == "Every minute"
    assert Cron("0 0 * * *").get_description() == "At 00:00"
    assert Cron("0 0 * * 0").get_description() == \
        "At 00:00, only on Sunday"
    assert Cron("0 0 * * 0-1").get_description() == \
        "At 00:00, Sunday through Monday"
    assert Cron("0 0 * * 0-1").get_description("de_DE") == \
        "Um 00:00, Sunday bis Monday"
    assert Cron("0 0 * * 0-1").get_description("fr_FR") == \
        "À 00:00, de Sunday à Monday"
    assert Cron("0 0 * * 0-1").get_description("it_IT") == \
        "Alle 00:00, Sunday al Monday"
    assert Cron("* * * * 0-6").get_description() == \
        "Every minute, Sunday through Saturday"
    assert Cron("* * * * 1-5").get_description() == \
        "Every minute, Monday through Friday"
    assert Cron("* 6-22 * * *").get_description() == \
        "Every minute, between 06:00 and 22:59"
    assert Cron("* 6-22 * * 1-5; * 19-22 * * 0,6").get_description() == \
        ("Every minute, between 06:00 and 22:59, Monday through Friday; "
         "Every minute, between 19:00 and 22:59, only on Sunday and Saturday")
    with pytest.raises(ConfigurationError):
        Cron("* * * * 0-7")
    with pytest.raises(ConfigurationError):
        Cron("* * * * 7")


def test_is_now():
    assert Cron("* * * * *").is_now is True


def test_eq():
    assert Cron("0 0 * * *") == Cron("0 0 * * *")
    assert Cron("0 0 * * *") != Cron("0 0 * * 0")
    assert Cron() == Cron("* * * * *")
    assert Cron() == Cron(" * * * * * ")
    assert Cron("* * * * *; * * * * *") == Cron("* * * * *")


def test_repr():
    assert repr(Cron("0 0 * * *")) == "Cron(['0 0 * * *'])"
