import base64
import datetime
import logging
import time

import requests
from colorama import Fore
from findmy import FindMyAccessory
from findmy.errors import UnhandledProtocolError

from apple.account import login
from constants import (
    ACCOUNT_ENDPOINT,
    LOCATIONS_ENDPOINT,
    PASSWORD,
    SLEEP_SECONDS,
    TAGS_ENDPOINT,
    TAGS_REFRESH_SECONDS,
    USERNAME,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)


def fetch_account_and_login():
    account_response = requests.get(ACCOUNT_ENDPOINT, auth=(USERNAME, PASSWORD))
    account_response.raise_for_status()
    if not account_response.json():
        logger.error(f"{Fore.RED}No apple account found, exiting...{Fore.RESET}")
        exit(1)
    return login(account_response.json()[0]["data"])


def fetch_tags():
    tags_response = requests.get(TAGS_ENDPOINT, auth=(USERNAME, PASSWORD))
    tags_response.raise_for_status()
    tags = tags_response.json()
    if not tags:
        logger.error(f"{Fore.RED}No tags found, exiting...{Fore.RESET}")
        return []
    logger.info(
        f"{Fore.GREEN}Found {len(tags)} tag(s): {', '.join(tag['name'] for tag in tags)}{Fore.RESET}"
    )
    return tags


account = fetch_account_and_login()
last_tags_refresh = 0

while True:
    now = time.time()
    if now - last_tags_refresh > TAGS_REFRESH_SECONDS:
        tags = fetch_tags()
        last_tags_refresh = now

    for tag in tags:
        accessory = FindMyAccessory(
            master_key=base64.b64decode(tag["master_key"])[-28:],
            skn=base64.b64decode(tag["skn"]),
            sks=base64.b64decode(tag["sks"]),
            paired_at=datetime.datetime.fromisoformat(tag["paired_at"]),
            name=None,
            model=None,
            identifier=None,
        )

        try:
            reports = account.fetch_last_reports(accessory)
        except UnhandledProtocolError:
            logger.error(
                f"{Fore.RED}Failed to fetch reports due to UnhandledProtocolError for {tag['name']}, skipping...{Fore.RESET}"
            )
            continue
        logger.info(
            f"{Fore.MAGENTA}Found {len(reports)} report(s) for {tag['name']}{Fore.RESET}"
        )
        for report in reports:
            response = requests.post(
                LOCATIONS_ENDPOINT,
                json={
                    "tag": tag["id"],
                    "latitude": report.latitude,
                    "longitude": report.longitude,
                    "timestamp": report.timestamp.isoformat(),
                },
                auth=(USERNAME, PASSWORD),
            )

            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                if (
                    response.content
                    == b'{"non_field_errors":["The fields tag, latitude, longitude, timestamp must make a unique set."]}'
                ):
                    logger.info(
                        f"{Fore.LIGHTYELLOW_EX}Location for {tag['name']} already exists in the system{Fore.RESET}"
                    )
                else:
                    raise
            else:
                logger.info(
                    f"{Fore.GREEN}New location for {tag['name']} at {report.timestamp} lat:{report.latitude} lon:{report.longitude} saved{Fore.RESET}"
                )

            logger.info(f"Location report: {report.hashed_adv_key_b64} sent to api")

        time.sleep(SLEEP_SECONDS)
