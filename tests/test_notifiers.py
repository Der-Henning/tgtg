import json
import platform
from time import sleep
from unittest.mock import MagicMock

import pytest
import responses

from tgtg_scanner.models import Config, Favorites, Reservations
from tgtg_scanner.models.item import Item
from tgtg_scanner.notifiers.apprise import Apprise
from tgtg_scanner.notifiers.console import Console
from tgtg_scanner.notifiers.ifttt import IFTTT
from tgtg_scanner.notifiers.ntfy import Ntfy
from tgtg_scanner.notifiers.script import Script
from tgtg_scanner.notifiers.webhook import WebHook

SYS_PLATFORM = platform.system()
IS_WINDOWS = SYS_PLATFORM.lower() in {'windows', 'cygwin'}


@pytest.fixture
def reservations() -> Reservations:
    return MagicMock()


@pytest.fixture
def favorites() -> Favorites:
    return MagicMock()


@responses.activate
def test_webhook_json(test_item: Item, reservations: Reservations,
                      favorites: Favorites):
    config = Config("")
    config._setattr("webhook.enabled", True)
    config._setattr("webhook.method", "POST")
    config._setattr("webhook.url", "https://api.example.com")
    config._setattr("webhook.type", "application/json")
    config._setattr("webhook.headers", {"Accept": "json"})
    config._setattr("webhook.body",
                    '{"content": "${{items_available}} panier(s) '
                    'disponible(s) à ${{price}} € \nÀ récupérer '
                    '${{pickupdate}}\n'
                    'https://toogoodtogo.com/item/${{item_id}}"'
                    ', "username": "${{display_name}}"}')
    responses.add(
        responses.POST,
        "https://api.example.com",
        status=200)

    webhook = WebHook(config, reservations, favorites)
    webhook.start()
    webhook.send(test_item)
    webhook.stop()

    request = responses.calls[0].request
    body = json.loads(request.body)

    assert request.headers.get("Accept") == "json"
    assert request.headers.get(
        "Content-Type") == "application/json"
    assert body == {
        "content": (f"{test_item.items_available} panier(s) disponible(s) à "
                    f"{test_item.price} € \nÀ récupérer {test_item.pickupdate}"
                    f"\nhttps://toogoodtogo.com/item/{test_item.item_id}"),
        "username": f"{test_item.display_name}"}


@responses.activate
def test_webhook_text(test_item: Item, reservations: Reservations,
                      favorites: Favorites):
    config = Config("")
    config._setattr("webhook.enabled", True)
    config._setattr("webhook.method", "POST")
    config._setattr("webhook.url", "https://api.example.com")
    config._setattr("webhook.type", "text/plain")
    config._setattr("webhook.headers", {"Accept": "json"})
    config._setattr("webhook.body",
                    '${{items_available}} panier(s) '
                    'disponible(s) à ${{price}} € \nÀ récupérer '
                    '${{pickupdate}}\n'
                    'https://toogoodtogo.com/item/${{item_id}}')
    responses.add(
        responses.POST,
        "https://api.example.com",
        status=200)

    webhook = WebHook(config, reservations, favorites)
    webhook.start()
    webhook.send(test_item)
    webhook.stop()

    request = responses.calls[0].request

    assert request.headers.get("Accept") == "json"
    assert request.headers.get("Content-Type") == "text/plain"
    assert request.body.decode('utf-8') == (
        f"{test_item.items_available} panier(s) disponible(s) à "
        f"{test_item.price} € \nÀ récupérer {test_item.pickupdate}"
        f"\nhttps://toogoodtogo.com/item/{test_item.item_id}")


@responses.activate
def test_ifttt(test_item: Item, reservations: Reservations,
               favorites: Favorites):
    config = Config("")
    config._setattr("ifttt.enabled", True)
    config._setattr("ifttt.event", "tgtg_notification")
    config._setattr("ifttt.key", "secret_key")
    config._setattr("ifttt.body",
                    '{"value1": "${{display_name}}", '
                    '"value2": ${{items_available}}, '
                    '"value3": "https://share.toogoodtogo.com/'
                    'item/${{item_id}}"}')
    responses.add(
        responses.POST,
        f"https://maker.ifttt.com/trigger/"
        f"{config.ifttt.get('event')}"
        f"/with/key/{config.ifttt.get('key')}",
        body="Congratulations! You've fired the tgtg_notification event",
        content_type="text/plain",
        status=200)

    ifttt = IFTTT(config, reservations, favorites)
    ifttt.start()
    ifttt.send(test_item)
    ifttt.stop()

    request = responses.calls[0].request
    body = json.loads(request.body)

    assert request.headers.get("Content-Type") == "application/json"
    assert body == {
        "value1": test_item.display_name,
        "value2": test_item.items_available,
        "value3": f"https://share.toogoodtogo.com/item/{test_item.item_id}"}


@responses.activate
def test_ntfy(test_item: Item, reservations: Reservations,
              favorites: Favorites):
    config = Config("")
    config._setattr("ntfy.enabled", True)
    config._setattr("ntfy.server", "https://ntfy.sh")
    config._setattr("ntfy.topic", "tgtg_test")
    config._setattr("ntfy.title", "New Items - ${{display_name}}")
    config._setattr("ntfy.body",
                    '${{display_name}} - New Amount: ${{items_available}} - '
                    'https://share.toogoodtogo.com/item/${{item_id}}')
    responses.add(
        responses.POST,
        f"{config.ntfy.get('server')}/{config.ntfy.get('topic')}",
        status=200)

    ntfy = Ntfy(config, reservations, favorites)
    ntfy.start()
    ntfy.send(test_item)
    ntfy.stop()

    request = responses.calls[0].request

    assert request.url == (
        f"{config.ntfy.get('server')}/"
        f"{config.ntfy.get('topic')}")
    assert request.headers.get('X-Message').decode('utf-8') == (
        f'{test_item.display_name} - New Amount: {test_item.items_available} '
        f'- https://share.toogoodtogo.com/item/{test_item.item_id}')
    assert request.headers.get('X-Title').decode('utf-8') == (
        f'New Items - {test_item.display_name}')


@responses.activate
def test_apprise(test_item: Item, reservations: Reservations,
                 favorites: Favorites):
    config = Config("")
    config._setattr("apprise.enabled", True)
    config._setattr("apprise.url", "ntfy://tgtg_test")
    config._setattr("apprise.title", "New Items - ${{display_name}}")
    config._setattr("apprise.body",
                    '${{display_name}} - New Amount: ${{items_available}} - '
                    'https://share.toogoodtogo.com/item/${{item_id}}')
    responses.add(
        responses.POST,
        "https://ntfy.sh/",
        status=200)

    apprise = Apprise(config, reservations, favorites)
    apprise.start()
    apprise.send(test_item)
    apprise.stop()

    request = responses.calls[0].request
    body = json.loads(request.body)

    assert request.url == "https://ntfy.sh/"
    assert body.get('topic') == "tgtg_test"
    assert body.get('message') == (
        f'{test_item.display_name} - New Amount: {test_item.items_available} '
        f'- https://share.toogoodtogo.com/item/{test_item.item_id}')


def test_console(test_item: Item, reservations: Reservations,
                 favorites: Favorites, capsys: pytest.CaptureFixture):
    config = Config("")
    config._setattr("console.enabled", True)
    config._setattr("console.body", "${{display_name}} - "
                    "new amount: ${{items_available}}")

    console = Console(config, reservations, favorites)
    console.start()
    console.send(test_item)
    sleep(0.5)
    captured = capsys.readouterr()
    console.stop()

    assert captured.out.rstrip() == (
        f"{test_item.display_name} - "
        f"new amount: {test_item.items_available}")


def test_script(test_item: Item, reservations: Reservations,
                favorites: Favorites, capfdbinary: pytest.CaptureFixture):
    config = Config("")
    config._setattr("script.enabled", True)
    config._setattr("script.command", "echo ${{display_name}}")

    script = Script(config, reservations, favorites)
    script.start()
    script.send(test_item)
    sleep(0.5)
    captured = capfdbinary.readouterr()
    script.stop()

    encoding = "cp1252" if IS_WINDOWS else "utf-8"
    assert captured.out.decode(encoding).rstrip() == test_item.display_name
