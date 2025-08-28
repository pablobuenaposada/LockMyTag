import base64
import datetime
import logging
import os
import time

import requests
from findmy import FindMyAccessory

from apple.account import login

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
SLEEP_SECONDS = int(os.environ.get("SLEEP_SECONDS"))

logger = logging.getLogger(__name__)
account = login()
response = requests.get(f"{os.environ.get('API_URL')}/api/tags/")
response.raise_for_status()

while True:
    for tag in response.json():
        accessory = FindMyAccessory(
            master_key=base64.b64decode(tag["master_key"])[-28:],
            skn=base64.b64decode(tag["skn"]),
            sks=bytes(32),
            paired_at=datetime.datetime.strptime(tag["paired_at"], "%Y-%m-%d"),
            name=None,
            model=None,
            identifier=None,
        )
        logger.info(f"{tag['name']} airtag found")

        reports = account.fetch_last_reports(accessory)
        for report in sorted(reports):
            print(f" - {report}")

        time.sleep(SLEEP_SECONDS)
