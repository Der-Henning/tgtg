import logging

import pycron
from cron_descriptor import Options, get_description

from models.errors import ConfigurationError

log = logging.getLogger('tgtg')


class Cron():
    def __init__(self, cron_str: str = None) -> None:
        self.cron = cron_str.strip() if cron_str else '* * * * *'
        self.options = Options()
        self.options.use_24hour_time_format = True
        self.options.day_of_week_start_index_zero = True
        try:
            self.is_now
        except ValueError as err:
            raise ConfigurationError(
                f"Cron expression parsing error - {err}") from err
        _, _, _, _, dow = self.cron.split()
        if any(int(day) > 6 for day in dow.split("-") if day.isdigit()):
            raise ConfigurationError(
                "Cron expression parsing error - "
                "day of week must be between 0 and 6 (Sunday=0)")

    @property
    def is_now(self) -> bool:
        """ Returns True if the cron expression matches the current time """
        return pycron.is_now(self.cron)

    @property
    def minutes(self) -> str:
        return self.cron[:2]

    def get_description(self, locale: str = "en") -> str:
        """ Returns a human-readable description of the cron expression """
        self.options.locale_code = locale
        return get_description(self.cron, options=self.options)

    def __eq__(self, __o: object) -> bool:
        return getattr(__o, "cron") == self.cron

    def __repr__(self) -> str:
        return f"Cron('{self.cron}')"
