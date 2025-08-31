import base64
import datetime
import logging
import time

import requests
from findmy import FindMyAccessory

from apple.account import login
from constants import LOCATIONS_ENDPOINT, SLEEP_SECONDS, TAGS_ENDPOINT

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)
account = login()
tags = requests.get(TAGS_ENDPOINT)
tags.raise_for_status()

while True:
    for tag in tags.json():
        accessory = FindMyAccessory(
            master_key=base64.b64decode(tag["master_key"])[-28:],
            skn=base64.b64decode(tag["skn"]),
            sks=base64.b64decode(tag["sks"]),
            paired_at=datetime.datetime.strptime(tag["paired_at"], "%Y-%m-%d"),
            name=None,
            model=None,
            identifier=None,
        )
        logger.info(f"{tag['name']} airtag found")

        reports = account.fetch_last_reports(accessory)
        unique_reports = {r.hashed_adv_key_b64: r for r in reports}

        for report in unique_reports.values():
            response = requests.post(
                LOCATIONS_ENDPOINT,
                json={
                    "tag": tag["id"],
                    "hash": report.hashed_adv_key_b64,
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
                    == b'{"hash":["tag location with this hash already exists."]}'
                ):
                    pass
                else:
                    raise

            logger.info(f"Location report: {report.hashed_adv_key_b64} sent to api")

    time.sleep(SLEEP_SECONDS)
