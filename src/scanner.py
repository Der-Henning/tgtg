from tgtg import TgtgClient
from time import sleep
import sys
import logging as log
from os import path
from notifiers import Notifier
from models import Item, Config


class Scanner():
    def __init__(self):
        config_file = path.join(path.dirname(sys.executable), 'config.ini') if getattr(
            sys, '_MEIPASS', False) else path.join(path.dirname(path.abspath(__file__)), 'config.ini')
        self.config = Config() if not path.isfile(config_file) else Config(config_file)
        log.basicConfig(
            format='%(asctime)s %(levelname)-8s %(message)s',
            level=log.DEBUG if self.config.debug else log.INFO,
            datefmt='%Y-%m-%d %H:%M:%S')
        if self.config.debug:
            log.info("Debugging mode")
        self.item_ids = self.config.item_ids
        self.amounts = {}
        self.tgtg_client = TgtgClient(
            email=self.config.tgtg["username"], password=self.config.tgtg["password"])
        self.notifiers = Notifier(self.config)

    def _job(self):
        for item_id in self.item_ids:
            try:
                if item_id != "":
                    data = self.tgtg_client.get_item(item_id)
                    self._checkItem(Item(data))
            except:
                log.error(
                    "itemId {0} - Fehler! - {1}".format(item_id, sys.exc_info()))
        for data in self.tgtg_client.get_items(favorites_only=True):
            try:
                self._checkItem(Item(data))
            except:
                log.error("checkItem Fehler! - {0}".format(sys.exc_info()))
        log.debug("new State: {0}".format(self.amounts))

    def _checkItem(self, item: Item):
        try:
            if self.amounts[item.id] == 0 and item.items_available > self.amounts[item.id]:
                self._sendMessages(item)
        except:
            self.amounts[item.id] = item.items_available
        finally:
            if self.amounts[item.id] != item.items_available:
                log.info(
                    "{0} - New amount: {1}".format(item.display_name, item.items_available))
                self.amounts[item.id] = item.items_available

    def _sendMessages(self, item: Item):
        log.info(
            "Sending {0} - new Amount {1}".format(item.display_name, item.items_available))

    def _timeoutHandler(self, signum, frame):
        log.warning("Job timeout")
        raise Exception("Timeout")

    def run(self):
        log.info("Scanner started ...")
        while True:
            try:
                self._job()
            except:
                log.error(sys.exc_info())
            finally:
                sleep(self.config.sleep_time)


def main():
    scanner = Scanner()
    scanner.run()


if __name__ == "__main__":
    main()
