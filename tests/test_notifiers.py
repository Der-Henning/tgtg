import json
import platform
from importlib import reload
from time import sleep

import pytest
import responses

import models.config
from models.item import Item
from notifiers.apprise import Apprise
from notifiers.console import Console
from notifiers.ifttt import IFTTT
from notifiers.ntfy import Ntfy
from notifiers.script import Script
from notifiers.webhook import WebHook

SYS_PLATFORM = platform.system()
IS_WINDOWS = SYS_PLATFORM.lower() in ('windows', 'cygwin')


@responses.activate
def test_webhook_json(test_item: Item):
    reload(models.config)
    config = models.config.Config("")
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
        status=200
    )

    webhook = WebHook(config)
    webhook.send(test_item)

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
def test_webhook_text(test_item: Item):
    reload(models.config)
    config = models.config.Config("")
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
        status=200
    )

    webhook = WebHook(config)
    webhook.send(test_item)

    request = responses.calls[0].request

    assert request.headers.get("Accept") == "json"
    assert request.headers.get("Content-Type") == "text/plain"
    assert request.body.decode('utf-8') == (
        f"{test_item.items_available} panier(s) disponible(s) à "
        f"{test_item.price} € \nÀ récupérer {test_item.pickupdate}"
        f"\nhttps://toogoodtogo.com/item/{test_item.item_id}")


@responses.activate
def test_ifttt(test_item: Item):
    reload(models.config)
    config = models.config.Config("")
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
        status=200
    )

    ifttt = IFTTT(config)
    ifttt.send(test_item)

    request = responses.calls[0].request
    body = json.loads(request.body)

    assert request.headers.get("Content-Type") == "application/json"
    assert body == {
        "value1": test_item.display_name,
        "value2": test_item.items_available,
        "value3": f"https://share.toogoodtogo.com/item/{test_item.item_id}"}


@responses.activate
def test_ntfy(test_item: Item):
    reload(models.config)
    config = models.config.Config("")
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
        status=200
    )

    ntfy = Ntfy(config)
    ntfy.send(test_item)

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
def test_apprise(test_item: Item):
    reload(models.config)
    config = models.config.Config("")
    config._setattr("apprise.enabled", True)
    config._setattr("apprise.url", "ntfy://tgtg_test")
    config._setattr("apprise.title", "New Items - ${{display_name}}")
    config._setattr("apprise.body",
                    '${{display_name}} - New Amount: ${{items_available}} - '
                    'https://share.toogoodtogo.com/item/${{item_id}}')
    responses.add(
        responses.POST,
        "https://ntfy.sh/",
        status=200
    )

    apprise = Apprise(config)
    apprise.send(test_item)

    request = responses.calls[0].request
    body = json.loads(request.body)

    assert request.url == "https://ntfy.sh/"
    assert body.get('topic') == "tgtg_test"
    assert body.get('message') == (
        f'{test_item.display_name} - New Amount: {test_item.items_available} '
        f'- https://share.toogoodtogo.com/item/{test_item.item_id}')


def test_console(test_item: Item, capsys: pytest.CaptureFixture):
    reload(models.config)
    config = models.config.Config("")
    config._setattr("console.enabled", True)
    config._setattr("console.body", "${{display_name}} - "
                    "new amount: ${{items_available}}")

    console = Console(config)
    console.send(test_item)
    captured = capsys.readouterr()

    assert captured.out.rstrip() == (
        f"{test_item.display_name} - "
        f"new amount: {test_item.items_available}")


def test_script(test_item: Item, capfdbinary: pytest.CaptureFixture):
    reload(models.config)
    config = models.config.Config("")
    config._setattr("script.enabled", True)
    config._setattr("script.command", "echo ${{display_name}}")

    script = Script(config)
    script.send(test_item)
    sleep(0.1)
    captured = capfdbinary.readouterr()

    encoding = "cp1252" if IS_WINDOWS else "utf-8"
    assert captured.out.decode(encoding).rstrip() == test_item.display_name
