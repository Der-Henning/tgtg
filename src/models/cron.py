import logging
import pycron
# from cron_descriptor import get_description

from models.errors import ConfigurationError

log = logging.getLogger('tgtg')


class Cron():
    def __init__(self, cron_str: str) -> None:
        self.cron = (cron_str if cron_str is not None else '* * * * *').strip()
        try:
            self.is_now
        except ValueError as err:
            raise ConfigurationError(f"Schedule cron expression parsing error - {err}") from err
        if self.cron != '* * * * *':
            log.info("Active on schedule: %s", self.description)

    @property
    def is_now(self) -> bool:
        return pycron.is_now(self.cron)

    @property
    def description(self) -> str:
        return self.cron
        # return get_description(self.cron)
