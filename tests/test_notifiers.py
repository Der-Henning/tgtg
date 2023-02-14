import json
from importlib import reload

import pytest
import responses

import models.config
from models.item import Item
from notifiers.console import Console
from notifiers.ifttt import IFTTT
from notifiers.webhook import WebHook


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

    assert responses.calls[0].request.headers.get("Accept") == "json"
    assert responses.calls[0].request.headers.get(
        "Content-Type") == "application/json"
    assert json.loads(responses.calls[0].request.body) == {
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

    assert responses.calls[0].request.headers.get("Accept") == "json"
    assert responses.calls[0].request.headers.get(
        "Content-Type") == "text/plain"
    assert responses.calls[0].request.body.decode('utf-8') == (
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

    assert responses.calls[0].request.headers.get(
        "Content-Type") == "application/json"
    assert json.loads(responses.calls[0].request.body) == {
        "value1": test_item.display_name,
        "value2": test_item.items_available,
        "value3": f"https://share.toogoodtogo.com/item/{test_item.item_id}"}


def test_console(test_item: Item, capsys: pytest.CaptureFixture):
    reload(models.config)
    config = models.config.Config("")
    config._setattr("console.enabled", True)
    config._setattr("console.body", "${{display_name}} - "
                    "new amount: ${{items_available}}")

    console = Console(config)
    console.send(test_item)
    captured = capsys.readouterr()

    assert captured.out == (f"{test_item.display_name} - "
                            f"new amount: {test_item.items_available}\n")
