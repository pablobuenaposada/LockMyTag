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

        while True:
            last_location_per_tag = TagLocation.objects.filter(
                pk=Subquery(
                    TagLocation.objects.filter(tag=OuterRef("tag"))
                    .order_by("-created")
                    .values("pk")[:1]
                )
            )

            for location in last_location_per_tag:
                try:
                    lock = Lock.objects.get(tag=location.tag, status=Lock.STATUS_ACTIVE)
                    logger.info(f"Lock found for tag {location.tag.name}")
                except Lock.DoesNotExist:
                    logger.info(f"No lock found for tag {location.tag.name}")
                    lock = None

                if lock:
                    if not is_within_radius(
                        lock.latitude,
                        lock.longitude,
                        location.latitude,
                        location.longitude,
                        lock.radius,
                    ):
                        if (
                            not lock.last_notified
                            or lock.last_notified
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
                                    f"Tag {location.tag.name} is out of bounds! seen <a href='https://www.google.com/maps?q={location.latitude},{location.longitude}'>here</a> at {location.timestamp}"
                                )
                            )
                            lock.last_notified = timezone.now()
                            lock.save()
                        else:
                            logger.info(
                                f"{Fore.LIGHTRED_EX}Tag {location.tag.name} is out of bounds! but already notified so skipping...{Fore.RESET}"
                            )
                    else:
                        if lock.last_notified is not None:
                            lock.last_notified = None
                            lock.save()
                            logger.info(
                                f"{Fore.GREEN}Tag {location.tag.name} is back within bounds, notifying ...{Fore.RESET}"
                            )
                            asyncio.run(
                                send_message(
                                    f"Tag {location.tag.name} is back within bounds seen <a href='https://www.google.com/maps?q={location.latitude},{location.longitude}'>here</a> at {location.timestamp}"
                                )
                            )
                        else:
                            logger.info(
                                f"{Fore.GREEN}Tag {location.tag.name} is within bounds{Fore.RESET}"
                            )

                time.sleep(settings.NOTIFIER_SLEEP_SECONDS)
