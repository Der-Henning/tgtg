import logging

import pycron
from cron_descriptor import get_description

from models.errors import ConfigurationError

log = logging.getLogger('tgtg')


class Cron():
    def __init__(self, cron_str: str = None) -> None:
        _cron_str = cron_str.strip()
        self.cron = _cron_str if _cron_str else '* * * * *'
        try:
            self.is_now
        except ValueError as err:
            raise ConfigurationError(f"Schedule cron expression parsing error - {err}") from err

    @property
    def is_now(self) -> bool:
        return pycron.is_now(self.cron)

    @property
    def description(self) -> str:
        return get_description(self.cron)

    def __eq__(self, __o: object) -> bool:
        return getattr(__o, "cron") == self.cron

    def __repr__(self) -> str:
        return f"Cron('{self.cron}')"
