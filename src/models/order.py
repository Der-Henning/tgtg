class Order:
    def __init__(self, data: dict):
        self.order_id = data.get("order_id")
        self.state = data.get("state")
        self.cancel_until = data.get("cancel_until")

        redeem_interval = data.get("redeem_interval", {})
        self.redeem_interval_start = redeem_interval.get("start")
        self.redeem_interval_end = redeem_interval.get("end")

        pickup_interval = data.get("pickup_interval", {})
        self.pickup_interval_start = pickup_interval.get("start")
        self.pickup_interval_end = pickup_interval.get("end")

        self.store_time_zone = data.get("store_time_zone")
        self.quantity = data.get("quantity")

        price_including_taxes = data.get("price_including_taxes", {})
        self.price_including_taxes_code = price_including_taxes.get("code")
        self.price_including_taxes_minor_units = price_including_taxes.get("minor_units")
        self.price_including_taxes_decimals = price_including_taxes.get("decimals")

        price_excluding_taxes = data.get("price_excluding_taxes", {})
        self.price_excluding_taxes_code = price_excluding_taxes.get("code")
        self.price_excluding_taxes_minor_units = price_excluding_taxes.get("minor_units")
        self.price_excluding_taxes_decimals = price_excluding_taxes.get("decimals")

        total_applied_taxes = data.get("total_applied_taxes", {})
        self.total_applied_taxes_code = total_applied_taxes.get("code")
        self.total_applied_taxes_minor_units = total_applied_taxes.get("minor_units")
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

        pickup_location = data.get("pickup_location", {})
        address = pickup_location.get("address", {})
        country = address.get("country", {})
        self.pickup_location_country_iso_code = country.get("iso_code")
        self.pickup_location_country_name = country.get("name")
        self.pickup_location_address_line = address.get("address_line")
        self.pickup_location_city = address.get("city")
        self.pickup_location_postal_code = address.get("postal_code")

        location = pickup_location.get("location", {})
        self.pickup_location_longitude = location.get("longitude")
        self.pickup_location_latitude = location.get("latitude")

        self.can_be_rated = data.get("can_be_rated")
        self.payment_method_display_name = data.get("payment_method_display_name")
        self.is_rated = data.get("is_rated")
        self.time_of_purchase = data.get("time_of_purchase")
        self.store_id = data.get("store_id")
        self.store_name = data.get("store_name")
        self.store_branch = data.get("store_branch")

        store_logo = data.get("store_logo", {})
        self.store_logo_picture_id = store_logo.get("picture_id")
        self.store_logo_current_url = store_logo.get("current_url")
        self.store_logo_is_automatically_created = store_logo.get("is_automatically_created")

        self.item_id = data.get("item_id")

        item_cover_image = data.get("item_cover_image", {})
        self.item_cover_image_picture_id = item_cover_image.get("picture_id")
        self.item_cover_image_current_url = item_cover_image.get("current_url")
        self.item_cover_image_is_automatically_created = item_cover_image.get("is_automatically_created")

        self.is_buffet = data.get("is_buffet")
        self.can_user_supply_packaging = data.get("can_user_supply_packaging")
        self.packaging_option = data.get("packaging_option")
        self.pickup_window_changed = data.get("pickup_window_changed")
        self.is_store_we_care = data.get("is_store_we_care")
        self.can_show_best_before_explainer = data.get("can_show_best_before_explainer")
        self.show_sales_taxes = data.get("show_sales_taxes")
        self.order_type = data.get("order_type")
        self.is_support_available = data.get("is_support_available")
        self.last_updated_at_utc = data.get("last_updated_at_utc")
