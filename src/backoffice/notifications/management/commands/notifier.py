import asyncio
import datetime
import logging
import time

from colorama import Fore
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import OuterRef, Subquery
from django.utils import timezone

from locations.models import TagLocation
from locks.models import Lock
from locks.utils import is_within_radius
from notifications.telegram import send_message, start_telegram_bot

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Runs the lock notifier service"

    def handle(self, *args, **options):
        logger.info("Starting lock notifier service...")

        start_telegram_bot()
        last_notified = {}  # here we will store the last notified time per tag to avoid spamming

        while True:
            last_location_per_tag = TagLocation.objects.filter(
                pk=Subquery(
                    TagLocation.objects.filter(tag=OuterRef("tag"))
                    .order_by("-timestamp")
                    .values("pk")[:1]
                )
            )

            for location in last_location_per_tag:
                lock = Lock.objects.get_active_applicable_locks(location.tag)

                if lock:
                    logger.info(f"Lock found for tag {location.tag.name}")
                    if not is_within_radius(
                        lock.latitude,
                        lock.longitude,
                        location.latitude,
                        location.longitude,
                        lock.radius,
                    ):
                        if (
                            location.tag.id not in last_notified
                            or last_notified[location.tag.id]
                            + datetime.timedelta(
                                minutes=settings.NOTIFY_COOLDOWN_MINUTES
                            )
                            < timezone.now()
                        ):
                            logger.info(
                                f"{Fore.LIGHTRED_EX}Tag {location.tag.name} is out of bounds! notifying ...{Fore.RESET}"
                            )
                            asyncio.run(
                                send_message(
                                    f"❌ Tag {location.tag.name} is out of bounds! seen <a href='https://www.google.com/maps?q={location.latitude},{location.longitude}'>here</a> at {location.timestamp}"
                                )
                            )
                            last_notified[location.tag.id] = timezone.now()
                        else:
                            logger.info(
                                f"{Fore.LIGHTRED_EX}Tag {location.tag.name} is out of bounds! but already notified so skipping...{Fore.RESET}"
                            )
                    else:  # tag is within bounds
                        if location.tag.id in last_notified:
                            # was previously out of bounds
                            del last_notified[location.tag.id]
                            logger.info(
                                f"{Fore.GREEN}Tag {location.tag.name} is back within bounds, notifying ...{Fore.RESET}"
                            )
                            asyncio.run(
                                send_message(
                                    f"✅ Tag {location.tag.name} is back within bounds seen <a href='https://www.google.com/maps?q={location.latitude},{location.longitude}'>here</a> at {location.timestamp}"
                                )
                            )
                        else:
                            logger.info(
                                f"{Fore.GREEN}Tag {location.tag.name} is within bounds{Fore.RESET}"
                            )
                else:
                    # no lock found, treat as "back within bounds" if previously notified
                    if location.tag.id in last_notified:
                        del last_notified[location.tag.id]
                        logger.info(
                            f"{Fore.GREEN}Tag {location.tag.name} is back within bounds because lock has expired, notifying ...{Fore.RESET}"
                        )
                        asyncio.run(
                            send_message(
                                f"✅ Tag {location.tag.name} is back within bounds because lock has expired, seen <a href='https://www.google.com/maps?q={location.latitude},{location.longitude}'>here</a> at {location.timestamp}"
                            )
                        )
                    else:
                        logger.info(f"No lock found for tag {location.tag.name}")

            time.sleep(settings.NOTIFIER_SLEEP_SECONDS)
