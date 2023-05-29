import shutil
from pathlib import Path

import pytest

from models import Item


@pytest.fixture
def item_properties():
    return {
        "GLOBAL_PROPERTIES": [
            "item",
            "store",
            "display_name",
            "pickup_location",
            "items_available",
            "favorite"
        ],
        "STORE_PROPERTIES": [
            "store_id"
        ],
        "ITEM_PROPERTIES": [
            "item_id",
            "price_including_taxes",
            "description"
        ],
        "PRICE_PROPERTIES": [
            "code",
            "minor_units",
            "decimals"
        ]
    }


@pytest.fixture
def temp_path():
    temp_path = Path("./pytest_tmp")
    temp_path.mkdir(exist_ok=True)
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def test_item(tgtg_item: dict):
    return Item(tgtg_item)


@pytest.fixture
def tgtg_item():
    return {
        'item': {
            'item_id': '774625',
            'sales_taxes': [
                {'tax_description': 'USt.', 'tax_percentage': 7.0}
            ],
            'tax_amount': {
                'code': 'EUR',
                'minor_units': 20,
                'decimals': 2
            },
            'price_excluding_taxes': {
                'code': 'EUR',
                'minor_units': 280,
                'decimals': 2
            },
            'price_including_taxes': {
                'code': 'EUR',
                'minor_units': 300,
                'decimals': 2
            },
            'value_excluding_taxes': {
                'code': 'EUR',
                'minor_units': 841,
                'decimals': 2
            },
            'value_including_taxes': {
                'code': 'EUR',
                'minor_units': 900,
                'decimals': 2
            },
            'taxation_policy': 'PRICE_INCLUDES_TAXES',
            'show_sales_taxes': False,
            'cover_picture': {
                'picture_id': '282115',
                'current_url': 'https://images.tgtg.ninja/standard_images'
                               '/Chinese/korean-food-1699781_1280.jpg',
                'is_automatically_created': False
            },
            'logo_picture': {
                'picture_id': '768433',
                'current_url': 'https://images.tgtg.ninja/store/e7fee96e-'
                               '318a-4056-aaff-496794906be1.png',
                'is_automatically_created': False
            },
            'name': '',
            'description': 'Rette eine Magic Bag mit leckerem '
                           'indischen Essen.',
            'food_handling_instructions': '',
            'can_user_supply_packaging': False,
            'packaging_option': 'BAG_ALLOWED',
            'collection_info': 'Wir befinden uns im 2. Obergeschoss '
                               'in der Europapassage.',
            'diet_categories': [],
            'item_category': 'MEAL',
            'buffet': False,
            'badges': [
                {
                    'badge_type': 'SERVICE_RATING_SCORE',
                    'rating_group': 'LIKED',
                    'percentage': 85,
                    'user_count': 162,
                    'month_count': 5
                }
            ],
            'positive_rating_reasons': [
                'POSITIVE_FEEDBACK_DELICIOUS_FOOD',
                'POSITIVE_FEEDBACK_GREAT_VALUE',
                'POSITIVE_FEEDBACK_QUICK_COLLECTION',
                'POSITIVE_FEEDBACK_FRIENDLY_STAFF',
                'POSITIVE_FEEDBACK_GREAT_QUANTITY',
                'POSITIVE_FEEDBACK_GREAT_VARIETY'
            ],
            'average_overall_rating': {
                'average_overall_rating': 3.3333333333333335,
                'rating_count': 162,
                'month_count': 6
            },
            'favorite_count': 0
        },
        'store': {
            'store_id': '758373',
            'store_name': 'Chutney Indian Food',
            'branch': 'Hamburg – Europapassage 2.OG',
            'description': '',
            'tax_identifier': 'DE252292855',
            'website': '',
            'store_location': {
                      'address': {
                        'country': {'iso_code': 'DE', 'name': 'Germany'},
                        'address_line': 'Ballindamm 40, 20095 Hamburg, '
                                        'Deutschland',
                        'city': '',
                        'postal_code': ''
                      },
                'location': {'longitude': 9.99532, 'latitude': 53.55182}},
            'logo_picture': {
                'picture_id': '768433',
                'current_url': 'https://images.tgtg.ninja/store/e7fee96e-'
                               '318a-4056-aaff-496794906be1.png',
                'is_automatically_created': False
            },
            'store_time_zone': 'Europe/Berlin',
            'hidden': False,
            'favorite_count': 0,
            'we_care': False,
            'distance': 0.13365150729215916,
            'cover_picture': {
                'picture_id': '282115',
                'current_url': 'https://images.tgtg.ninja/standard_images/'
                               'Chinese/korean-food-1699781_1280.jpg',
                'is_automatically_created': False
            },
            'is_manufacturer': False},
        'display_name': 'Chutney Indian Food - Hamburg – Europapassage 2.OG',
        'pickup_interval': {
            'start': '2022-12-30T19:00:00Z',
            'end': '2022-12-30T19:30:00Z'
        },
        'pickup_location': {
            'address': {
                'country': {'iso_code': 'DE', 'name': 'Germany'},
                'address_line': 'Ballindamm 40, 20095 Hamburg, Deutschland',
                'city': '',
                'postal_code': ''
            },
            'location': {'longitude': 9.99532, 'latitude': 53.55182}},
        'purchase_end': '2022-12-30T19:30:00Z',
        'items_available': 3,
        'distance': 0.13365150729215916,
        'favorite': False,
        'in_sales_window': True,
        'new_item': False,
        'item_type': 'MAGIC_BAG'}
