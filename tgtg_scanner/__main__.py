import argparse
import datetime
import http.client as http_client
import json
import logging
import os
import platform
import signal
import sys
from pathlib import Path
from typing import Any, NoReturn, Union

import colorlog
import requests
from packaging import version
from requests.exceptions import RequestException

from tgtg_scanner._version import __author__, __description__, __url__, __version__
from tgtg_scanner.errors import ConfigurationError, TgtgAPIError
from tgtg_scanner.models import Config
from tgtg_scanner.scanner import Scanner

VERSION_URL = "https://api.github.com/repos/Der-Henning/tgtg/releases/latest"

HEADER = (
    r"  ____  ___  ____  ___    ____   ___   __   __ _  __ _  ____  ____  ",
    r" (_  _)/ __)(_  _)/ __)  / ___) / __) / _\ (  ( \(  ( \(  __)(  _ \ ",
    r"   )( ( (_ \  )( ( (_ \  \___ \( (__ /    \/    //    / ) _)  )   / ",
    r"  (__) \___/ (__) \___/  (____/ \___)\_/\_/\_)__)\_)__)(____)(__\_) ",
)


# set to 1 to debug http headers
http_client.HTTPConnection.debuglevel = 0

SYS_PLATFORM = platform.system()
IS_WINDOWS = SYS_PLATFORM.lower() in {"windows", "cygwin"}
IS_EXECUTABLE = getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")
PROG_PATH = Path(sys.executable).parent if IS_EXECUTABLE else Path(os.getcwd())
IS_DOCKER = os.environ.get("DOCKER", "False").lower() in {"true", "1", "t", "y", "yes"}
LOGS_PATH = Path(os.environ.get("LOGS_PATH", PROG_PATH))


def main():
    """Wrapper for Scanner and Helper functions."""
    _register_signals()

    config_file = _get_config_file()
    log_file = Path(LOGS_PATH, "scanner.log")

    parser = argparse.ArgumentParser(description=__description__)
    parser.add_argument("-v", "--version", action="version", version=f"v{__version__}")
    parser.add_argument("-d", "--debug", action="store_true", help="activate debugging mode")
    parser.add_argument(
        "-c",
        "--config",
        metavar="config_file",
        type=Path,
        default=config_file,
        help="path to config file (default: config.ini)",
    )
    parser.add_argument(
        "-l",
        "--log_file",
        metavar="log_file",
        type=Path,
        default=log_file,
        help="path to log file (default: scanner.log)",
    )
    helper_group = parser.add_mutually_exclusive_group(required=False)
    helper_group.add_argument(
        "-t",
        "--tokens",
        action="store_true",
        help="display your current access tokens and exit",
    )
    helper_group.add_argument("-f", "--favorites", action="store_true", help="display your favorites and exit")
    helper_group.add_argument(
        "-F",
        "--favorite_ids",
        action="store_true",
        help="display the item ids of your favorites and exit",
    )
    helper_group.add_argument(
        "-a",
        "--add",
        nargs="+",
        metavar="item_id",
        help="add item ids to favorites and exit",
    )
    helper_group.add_argument(
        "-r",
        "--remove",
        nargs="+",
        metavar="item_id",
        help="remove item ids from favorites and exit",
    )
    helper_group.add_argument("-R", "--remove_all", action="store_true", help="remove all favorites and exit")
    json_group = parser.add_mutually_exclusive_group(required=False)
    json_group.add_argument("-j", "--json", action="store_true", help="output as plain json")
    json_group.add_argument("-J", "--json_pretty", action="store_true", help="output as pretty json")
    parser.add_argument("--base_url", default=None, help="Overwrite TGTG API URL for testing")
    args = parser.parse_args()

    # Disable logging for json output
    if args.json or args.json_pretty:
        logging.disable(logging.CRITICAL)

    # Remove all handlers
    for handler in logging.root.handlers:
        logging.root.removeHandler(handler)

    # Set all loggers to level Error
    for logger_name in logging.root.manager.loggerDict:
        logging.getLogger(logger_name).setLevel(logging.CRITICAL)

    # Define stream formatter and handler
    stream_formatter = colorlog.ColoredFormatter(
        fmt=("%(cyan)s%(asctime)s%(reset)s %(log_color)s%(levelname)-8s%(reset)s %(message)s"),
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "purple",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red",
        },
    )
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(stream_formatter)
    logging.root.addHandler(stream_handler)

    # Define file formatter and handler
    args.log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(args.log_file, mode="w", encoding="utf-8")
    file_formatter = logging.Formatter(
        fmt=("[%(asctime)s][%(name)s][%(filename)s:%(funcName)s:%(lineno)d][%(levelname)s] %(message)s"),
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logging.root.addHandler(file_handler)

    # Create tgtg logger
    log = logging.getLogger("tgtg")
    log.setLevel(logging.INFO)

    try:
        # Load config
        config = Config(args.config)
        config.docker = IS_DOCKER

        # Activate debugging mode
        if args.debug:
            config.debug = True
        if config.debug:
            for logger_name in logging.root.manager.loggerDict:
                logging.getLogger(logger_name).setLevel(logging.DEBUG)
            log.info("Debugging mode enabled")

        if args.base_url is not None:
            config.tgtg.base_url = args.base_url

        scanner = Scanner(config)
        if args.tokens:
            credentials = scanner.get_credentials()
            if args.json:
                print(json.dumps(credentials, sort_keys=True))
            elif args.json_pretty:
                print(json.dumps(credentials, sort_keys=True, indent=4))
            else:
                print("")
                print("Your TGTG credentials:")
                print("Email:          ", credentials.get("email"))
                print("Access Token:   ", credentials.get("access_token"))
                print("Refresh Token:  ", credentials.get("refresh_token"))
                print("Datadome Cookie:", credentials.get("datadome_cookie"))
                print("")
        elif args.favorites:
            favorites = scanner.get_favorites()
            if args.json:
                print(json.dumps(favorites, sort_keys=True))
            elif args.json_pretty:
                print(json.dumps(favorites, sort_keys=True, indent=4))
            else:
                print("")
                print("Your favorites:")
                print(json.dumps(favorites, sort_keys=True, indent=4))
                print("")
        elif args.favorite_ids:
            favorites = scanner.get_favorites()
            item_ids = [fav.get("item", {}).get("item_id") for fav in favorites]
            if args.json:
                print(json.dumps(item_ids, sort_keys=True))
            elif args.json_pretty:
                print(json.dumps(item_ids, sort_keys=True, indent=4))
            else:
                print("")
                print("Item IDs:")
                print(" ".join(item_ids))
                print("")
        elif args.add is not None:
            for item_id in args.add:
                scanner.set_favorite(item_id)
            print("done.")
        elif args.remove is not None:
            for item_id in args.remove:
                scanner.unset_favorite(item_id)
            print("done.")
        elif args.remove_all:
            if query_yes_no("Remove all favorites from your account?", default="no"):
                scanner.unset_all_favorites()
                print("done.")
        else:
            _run_scanner(scanner)
    except ConfigurationError as err:
        log.error("Configuration Error: %s", err)
        sys.exit(1)
    except TgtgAPIError as err:
        log.error("TGTG API Error: %s", err)
        sys.exit(1)
    except KeyboardInterrupt:
        log.info("Shutting down scanner ...")
        scanner.stop()
        sys.exit(0)
    except SystemExit:
        sys.exit(1)


def _get_config_file() -> Union[Path, None]:
    # Default: config.ini in current working directory or next to executable
    config_file = Path(PROG_PATH, "config.ini")
    if config_file.is_file():
        return config_file
    # config.ini in project folder (same place as config.sample.ini)
    config_file = Path(Path(__file__).parents[1], "config.ini")
    if config_file.is_file():
        return config_file
    # legacy: config.ini in src folder
    config_file = Path(Path(__file__).parents[1], "src", "config.ini")
    if config_file.is_file():
        return config_file
    return None


def _get_version_info() -> str:
    lastest_release = _get_new_version()
    if lastest_release is None:
        return __version__
    return f"{__version__} - Update available! See {lastest_release.get('html_url')}"


def _run_scanner(scanner: Scanner) -> NoReturn:
    _print_welcome_message()
    _print_version_check()
    if scanner.config.quiet and not scanner.config.debug:
        for logger_name in logging.root.manager.loggerDict:
            logging.getLogger(logger_name).setLevel(logging.ERROR)
    scanner.run()


def _get_new_version() -> Union[dict, None]:
    log = logging.getLogger("tgtg")
    try:
        res = requests.get(VERSION_URL, timeout=60)
        res.raise_for_status()
        lastest_release = res.json()
        if version.parse(__version__) < version.parse(lastest_release.get("tag_name")):
            return lastest_release
    except (RequestException, version.InvalidVersion, ValueError) as err:
        log.warning("Failed getting latest version! - %s", err)
    return None


def _print_version_check() -> None:
    log = logging.getLogger("tgtg")
    try:
        lastest_release = _get_new_version()
        if lastest_release is not None:
            log.info("New Version %s available!", version.parse(lastest_release.get("tag_name")))
            log.info("Please visit %s", lastest_release.get("html_url"))
            log.info("")
    except (version.InvalidVersion, ValueError) as err:
        log.warning("Failed checking for new Version! - %s", err)


def _print_welcome_message() -> None:
    log = logging.getLogger("tgtg")
    for line in HEADER:
        log.info(line)
    log.info("")
    log.info("Version %s", __version__)
    today = datetime.date.today()
    log.info("©%s, %s", today.year, __author__)
    log.info("For documentation and support please visit %s", __url__)
    log.info("")


def _register_signals() -> None:
    # TODO: Define SIGUSR1, SIGUSR2
    signal.signal(signal.SIGINT, _handle_exit_signal)
    signal.signal(signal.SIGTERM, _handle_exit_signal)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(getattr(signal, "SIGBREAK"), _handle_exit_signal)
    if not IS_WINDOWS:
        signal.signal(signal.SIGHUP, _handle_exit_signal)  # type: ignore[attr-defined]
        # TODO: SIGQUIT is ideally meant to terminate with core dumps
        signal.signal(signal.SIGQUIT, _handle_exit_signal)  # type: ignore[attr-defined]


def _handle_exit_signal(signum: int, _frame: Any) -> None:
    log = logging.getLogger("tgtg")
    log.debug("Received signal %d" % signum)
    raise KeyboardInterrupt


def query_yes_no(question, default="yes") -> bool:
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError(f"invalid default answer: '{default}'")

    while True:
        print(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        if choice in valid:
            return valid[choice]
        print("Please respond with 'yes' or 'no' (or 'y' or 'n').")


if __name__ == "__main__":
    main()
