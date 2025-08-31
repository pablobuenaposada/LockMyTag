import base64
import datetime
import logging
import time

import requests
from colorama import Fore
from findmy import FindMyAccessory

from apple.account import login
from constants import ACCOUNT_ENDPOINT, LOCATIONS_ENDPOINT, SLEEP_SECONDS, TAGS_ENDPOINT

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)
account = requests.get(ACCOUNT_ENDPOINT)
account.raise_for_status()
account = login(account.json()[0]["data"])
tags = requests.get(TAGS_ENDPOINT)
tags.raise_for_status()
tags = tags.json()

logger.info(
    f"{Fore.GREEN}Found {len(tags)} tag(s): {', '.join(tag['name'] for tag in tags)}{Fore.RESET}"
)

while True:
    for tag in tags:
        accessory = FindMyAccessory(
            master_key=base64.b64decode(tag["master_key"])[-28:],
            skn=base64.b64decode(tag["skn"]),
            sks=base64.b64decode(tag["sks"]),
            paired_at=datetime.datetime.strptime(tag["paired_at"], "%Y-%m-%d"),
            name=None,
            model=None,
            identifier=None,
        )

        reports = account.fetch_last_reports(accessory)
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
