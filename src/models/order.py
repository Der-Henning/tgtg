import re
from datetime import datetime, timedelta

from helpers.distance_time_calculator import DistanceTimeCalculator
from models.errors import MaskConfigurationError
from shared_variables import (BIKING_MODE, DATETIME_FORMAT, DRIVING_MODE,
                              PUBLIC_TRANSPORT_MODE, WALKING_MODE)

ATTRS = [
    "order_id", "state", "cancel_until", "redeem_interval_start",
    "redeem_interval_end", "pickup_interval_start", "pickup_interval_end",
    "store_time_zone", "quantity", "price_including_taxes_code",
    "price_including_taxes_minor_units", "price_including_taxes_decimals",
    "price_excluding_taxes_code", "price_excluding_taxes_minor_units",
    "price_excluding_taxes_decimals", "total_applied_taxes_code",
    "total_applied_taxes_minor_units", "total_applied_taxes_decimals",
    "sales_tax_description", "sales_tax_percentage", "sales_tax_amount_code",
    "sales_tax_amount_minor_units", "sales_tax_amount_decimals",
    "pickup_location", "can_be_rated", "payment_method_display_name",
    "is_rated", "time_of_purchase", "store_id", "store_name", "store_branch",
    "store_logo_picture_id", "store_logo_current_url",
    "store_logo_is_automatically_created", "item_id",
    "item_cover_image_picture_id", "item_cover_image_current_url",
    "item_cover_image_is_automatically_created", "is_buffet",
    "can_user_supply_packaging", "packaging_option", "pickup_window_changed",
    "is_store_we_care", "can_show_best_before_explainer", "show_sales_taxes",
    "order_type", "is_support_available", "last_updated_at_utc"
]


class Order:
    """
    Takes the raw data from the TGTG API and
    returns well formated data for notifications.
    """

    def __init__(self, data: dict, dt_calculator: DistanceTimeCalculator):
        self.order_id = data.get("order_id")
        self.state = data.get("state")
        self.cancel_until = data.get("cancel_until")

        redeem_interval = data.get("redeem_interval", {})
        self.redeem_interval_start = redeem_interval.get("start")
        self.redeem_interval_end = redeem_interval.get("end")

        self.pickup_interval_start = data.get(
            "pickup_interval", {}).get("start", None)
        self.pickup_interval_end = data.get(
            "pickup_interval", {}).get("end", None)

        self.store_time_zone = data.get("store_time_zone")
        self.quantity = data.get("quantity")

        price_including_taxes = data.get("price_including_taxes", {})
        self.price_including_taxes_code = price_including_taxes.get("code")
        self.price_including_taxes_minor_units = price_including_taxes.get(
            "minor_units")
        self.price_including_taxes_decimals = price_including_taxes.get(
            "decimals")

        price_excluding_taxes = data.get("price_excluding_taxes", {})
        self.price_excluding_taxes_code = price_excluding_taxes.get("code")
        self.price_excluding_taxes_minor_units = price_excluding_taxes.get(
            "minor_units")
        self.price_excluding_taxes_decimals = price_excluding_taxes.get(
            "decimals")

        total_applied_taxes = data.get("total_applied_taxes", {})
        self.total_applied_taxes_code = total_applied_taxes.get("code")
        self.total_applied_taxes_minor_units = total_applied_taxes.get(
            "minor_units")
        self.total_applied_taxes_decimals = total_applied_taxes.get("decimals")

        sales_taxes = data.get("sales_taxes", [])
        if sales_taxes:
            sales_tax = sales_taxes[0]
            self.sales_tax_description = sales_tax.get("tax_description")
            self.sales_tax_percentage = sales_tax.get("tax_percentage")
            tax_amount = sales_tax.get("tax_amount", {})
            self.sales_tax_amount_code = tax_amount.get("code")
            self.sales_tax_amount_minor_units = tax_amount.get("minor_units")
            self.sales_tax_amount_decimals = tax_amount.get("decimals")

        self.pickup_location = data.get("pickup_location", {}).get(
            "address", {}).get("address_line", "-")

        self.can_be_rated = data.get("can_be_rated")
        self.payment_method_display_name = data.get(
            "payment_method_display_name")
        self.is_rated = data.get("is_rated")
        self.time_of_purchase = data.get("time_of_purchase")
        self.store_id = data.get("store_id")
        self.store_name = data.get("store_name")
        self.store_branch = data.get("store_branch")

        store_logo = data.get("store_logo", {})
        self.store_logo_picture_id = store_logo.get("picture_id")
        self.store_logo_current_url = store_logo.get("current_url")
        self.store_logo_is_automatically_created = store_logo.get(
            "is_automatically_created")

        self.item_id = data.get("item_id")

        item_cover_image = data.get("item_cover_image", {})
        self.item_cover_image_picture_id = item_cover_image.get("picture_id")
        self.item_cover_image_current_url = item_cover_image.get("current_url")
        self.item_cover_image_is_automatically_created = item_cover_image.get(
            "is_automatically_created")

        self.is_buffet = data.get("is_buffet")
        self.can_user_supply_packaging = data.get("can_user_supply_packaging")
        self.packaging_option = data.get("packaging_option")
        self.pickup_window_changed = data.get("pickup_window_changed")
        self.is_store_we_care = data.get("is_store_we_care")
        self.can_show_best_before_explainer = data.get(
            "can_show_best_before_explainer")
        self.show_sales_taxes = data.get("show_sales_taxes")
        self.order_type = data.get("order_type")
        self.is_support_available = data.get("is_support_available")
        self.last_updated_at_utc = data.get("last_updated_at_utc")

        self.dt_calculator = dt_calculator

    @staticmethod
    def check_mask(text: str) -> None:
        """
        Checks whether the variables in the provided string are available

        Raises MaskConfigurationError
        """
        for match in re.finditer(r"\${{([a-zA-Z0-9_]+)}}", text):
            if not match.group(1) in ATTRS:
                raise MaskConfigurationError(match.group(0))

    def unmask(self, text: str) -> str:
        """
        Replaces variables with the current values.
        """
        if text in ["${{item_logo_bytes}}", "${{item_cover_bytes}}"]:
            matches = re.findall(r"\${{([a-zA-Z0-9_]+)}}", text)
            return getattr(self, matches[0])
        for match in re.finditer(r"\${{([a-zA-Z0-9_]+)}}", text):
            if hasattr(self, match.group(1)):
                val = getattr(self, match.group(1))
                text = text.replace(match.group(0), str(val))
        return text

    @property
    def remaining_pickup_time(self):
        pickup_interval_end = datetime.strptime(self.pickup_interval_end,
                                                DATETIME_FORMAT)
        return int((pickup_interval_end + timedelta(hours=2) - datetime.now()
                    ).total_seconds() // 60)

    @property
    def remaining_cancellation_time(self):
        cancel_until = datetime.strptime(self.cancel_until,
                                         DATETIME_FORMAT)
        return int((cancel_until + timedelta(hours=2) - datetime.now()
                    ).total_seconds() // 60)

    @property
    def remaining_time_until_pickup_start(self):
        pickup_interval_start = datetime.strptime(self.pickup_interval_start,
                                                  DATETIME_FORMAT)
        return int((pickup_interval_start + timedelta(hours=2) - datetime.now()
                    ).total_seconds() // 60)

    @property
    def link(self) -> str:
        return f"https://share.toogoodtogo.com/item/{self.item_id}"

    def _get_distance_time_with_traffic(self, mode):
        return self.dt_calculator.calculate_time_with_traffic(
            self.pickup_location, mode, self.item_id)

    @property
    def driving_ct(self) -> int:
        return self._get_distance_time_with_traffic(DRIVING_MODE)

    @property
    def walking_ct(self) -> int:
        return self._get_distance_time_with_traffic(WALKING_MODE)

    @property
    def biking_ct(self) -> int:
        return self._get_distance_time_with_traffic(BIKING_MODE)

    @property
    def transit_ct(self) -> int:
        return self._get_distance_time_with_traffic(PUBLIC_TRANSPORT_MODE)

    @property
    def formatted_driving_ct(self) -> str:
        return f'{self.driving_ct} min'

    @property
    def formatted_walking_ct(self) -> str:
        return f'{self.walking_ct} min'

    @property
    def formatted_biking_ct(self) -> str:
        return f'{self.biking_ct} min'

    @property
    def formatted_transit_ct(self) -> str:
        return f'{self.transit_ct} min'

    def _exceeds_pickup_time_by(self, ct) -> int:
        return self.remaining_pickup_time - ct

    def _get_ct_with_exceeds(self, ct):
        exceeds_by = self._exceeds_pickup_time_by(ct)
        if exceeds_by > 0:
            return f'{ct} min'
        return f'{ct} min - ({exceeds_by} min too late)'

    @property
    def driving_ct_with_exceeds(self) -> str:
        return self._get_ct_with_exceeds(self.driving_ct)

    @property
    def walking_ct_with_exceeds(self) -> str:
        return self._get_ct_with_exceeds(self.walking_ct)

    @property
    def biking_ct_with_exceeds(self) -> str:
        return self._get_ct_with_exceeds(self.biking_ct)

    @property
    def transit_ct_with_exceeds(self) -> str:
        return self._get_ct_with_exceeds(self.transit_ct)
