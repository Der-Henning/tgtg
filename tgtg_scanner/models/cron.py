import logging
from typing import Union

import pycron
from cron_descriptor import Options, get_description

log = logging.getLogger("tgtg")


class Cron:
    def __init__(self, cron_str: Union[str, None] = None) -> None:
        self.crons = list(dict.fromkeys([cron.strip() for cron in cron_str.split(";")])) if cron_str else ["* * * * *"]
        self.options = Options()
        self.options.use_24hour_time_format = True
        self.options.day_of_week_start_index_zero = True
        try:
            self.is_now
        except ValueError as err:
            raise ValueError(f"Cron expression parsing error - {err}") from err
        for cron in self.crons:
            _, _, _, _, dow = cron.split()
            if any(int(day) > 6 for day in dow.split("-") if day.isdigit()):
                raise ValueError("Cron expression parsing error - day of week must be between 0 and 6 (Sunday=0)")

    @property
    def is_now(self) -> bool:
        """Returns True if the cron expression matches the current time"""
        return any(pycron.is_now(cron) for cron in self.crons)

    def get_description(self, locale: str = "en") -> str:
        """Returns a human-readable description of the cron expression"""
        self.options.locale_code = locale
        return "; ".join(get_description(cron, options=self.options) for cron in self.crons)

    def __eq__(self, __o: object) -> bool:
        return getattr(__o, "crons") == self.crons

    def __repr__(self) -> str:
        return f"Cron({self.crons})"
