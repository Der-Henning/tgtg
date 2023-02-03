import json

import responses

from models.config import Config
from models.item import Item
from notifiers.ifttt import IFTTT


@responses.activate
def test_ifttt(test_item: Item, default_config: Config):
    default_config._setattr("ifttt.enabled", True)
    default_config._setattr("ifttt.event", "tgtg_notification")
    default_config._setattr("ifttt.key", "secret_key")
    default_config._setattr("ifttt.body",
                            '{"value1": "${{display_name}}", '
                            '"value2": ${{items_available}}, '
                            '"value3": "https://share.toogoodtogo.com/'
                            'item/${{item_id}}"}')
    responses.add(
        responses.POST,
        f"https://maker.ifttt.com/trigger/"
        f"{default_config.ifttt.get('event')}"
        f"/with/key/{default_config.ifttt.get('key')}",
        body="Congratulations! You've fired the tgtg_notification event",
        content_type="text/plain",
        status=200
    )

    ifttt = IFTTT(default_config)

    ifttt.send(test_item)

    assert responses.calls[0].request.headers.get(
        "Content-Type") == "application/json"
    assert responses.calls[0].request.body == json.dumps(
        {"value1": test_item.display_name,
         "value2": test_item.items_available,
         "value3": f"https://share.toogoodtogo.com/item/{test_item.item_id}"})
