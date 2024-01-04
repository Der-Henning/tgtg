import pytest

from tgtg_scanner.models import Item


@pytest.fixture
def item_properties():
    return {
        "GLOBAL_PROPERTIES": [
            "item",
            "store",
            "display_name",
            "pickup_location",
            "items_available",
            "favorite",
        ],
        "STORE_PROPERTIES": ["store_id"],
        "ITEM_PROPERTIES": ["item_id", "price_including_taxes", "description"],
        "PRICE_PROPERTIES": ["code", "minor_units", "decimals"],
    }


@pytest.fixture
def test_item(tgtg_item: dict):
    return Item(tgtg_item)


@pytest.fixture
def tgtg_item():
    return {
        "display_name": "Chutney Indian Food - Hamburg – Europapassage 2.OG",
        "distance": 6025.8258209576325,
        "favorite": False,
        "in_sales_window": True,
        "item": {
            "average_overall_rating": {"average_overall_rating": 3.6324786324786325, "month_count": 6, "rating_count": 117},
            "badges": [
                {
                    "badge_type": "OVERALL_RATING_TRUST_SCORE",
                    "month_count": 6,
                    "percentage": 81,
                    "rating_group": "LIKED",
                    "user_count": 124,
                },
                {
                    "badge_type": "SERVICE_RATING_SCORE",
                    "month_count": 6,
                    "percentage": 82,
                    "rating_group": "LIKED",
                    "user_count": 124,
                },
            ],
            "buffet": False,
            "can_user_supply_packaging": False,
            "collection_info": "Wir befinden uns im 2. Obergeschoss in der Europapassage.",
            "cover_picture": {
                "current_url": "https://images.tgtg.ninja/standard_images/Chinese/korean-food-1699781_1280.jpg",
                "is_automatically_created": False,
                "picture_id": "282115",
            },
            "description": "Rette eine Überraschungstüte mit leckerem indischen Essen.",
            "diet_categories": [],
            "favorite_count": 0,
            "food_handling_instructions": "",
            "item_category": "MEAL",
            "item_id": "774625",
            "item_price": {"code": "EUR", "decimals": 2, "minor_units": 300},
            "item_value": {"code": "EUR", "decimals": 2, "minor_units": 900},
            "logo_picture": {
                "current_url": "https://images.tgtg.ninja/store/e7fee96e-318a-4056-aaff-496794906be1.png",
                "is_automatically_created": False,
                "picture_id": "768433",
            },
            "name": "",
            "packaging_option": "BAG_ALLOWED",
            "positive_rating_reasons": [
                "POSITIVE_FEEDBACK_DELICIOUS_FOOD",
                "POSITIVE_FEEDBACK_QUICK_COLLECTION",
                "POSITIVE_FEEDBACK_FRIENDLY_STAFF",
                "POSITIVE_FEEDBACK_GREAT_VALUE",
                "POSITIVE_FEEDBACK_GREAT_QUANTITY",
                "POSITIVE_FEEDBACK_GREAT_VARIETY",
            ],
        },
        "item_tags": [{"id": "SOLD_OUT", "short_text": "Sold out"}],
        "item_type": "MAGIC_BAG",
        "items_available": 3,
        "matches_filters": True,
        "new_item": False,
        "pickup_interval": {"end": "2021-01-04T19:30:00Z", "start": "2021-01-04T19:00:00Z"},
        "pickup_location": {
            "address": {
                "address_line": "Ballindamm 40, 20095 Hamburg, Deutschland",
                "city": "",
                "country": {"iso_code": "DE", "name": "Germany"},
                "postal_code": "",
            },
            "location": {"latitude": 53.55182, "longitude": 9.99532},
        },
        "purchase_end": "2024-01-04T19:30:00Z",
        "sold_out_at": "2024-01-04T13:00:43Z",
        "store": {
            "branch": "Hamburg \u2013 Europapassage 2.OG",
            "cover_picture": {
                "current_url": "https://images.tgtg.ninja/standard_images/Chinese/korean-food-1699781_1280.jpg",
                "is_automatically_created": False,
                "picture_id": "282115",
            },
            "description": "",
            "distance": 6025.8258209576325,
            "favorite_count": 0,
            "hidden": False,
            "is_manufacturer": False,
            "logo_picture": {
                "current_url": "https://images.tgtg.ninja/store/e7fee96e-318a-4056-aaff-496794906be1.png",
                "is_automatically_created": False,
                "picture_id": "768433",
            },
            "store_id": "758373",
            "store_location": {
                "address": {
                    "address_line": "Ballindamm 40, 20095 Hamburg, Deutschland",
                    "city": "",
                    "country": {"iso_code": "DE", "name": "Germany"},
                    "postal_code": "",
                },
                "location": {"latitude": 53.55182, "longitude": 9.99532},
            },
            "store_name": "Chutney Indian Food",
            "store_time_zone": "Europe/Berlin",
            "tax_identifier": "DE252292855",
            "we_care": False,
            "website": "",
        },
    }
