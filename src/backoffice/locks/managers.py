from django.db import models
from django.db.models import Q
from django.utils import timezone


class LockManager(models.Manager):
    def get_active_applicable_locks(self, tag):
        """
        Get active locks for a specific tag that are currently applicable:
        - Either no schedule (schedule_day is None)
        - Or scheduled for current day and time is within schedule window
        """
        now = timezone.localtime(timezone.now())
        current_day = now.weekday()
        current_time = now.time()

        try:
            return (
                self.filter(tag=tag, status=self.model.STATUS_ACTIVE)
                .filter(
                    Q(schedule_day__isnull=True)
                    | (
                        Q(schedule_day=current_day)
                        & Q(schedule_start_time__lte=current_time)
                        & Q(schedule_end_time__gt=current_time)
                    )
                )
                .get()
            )
        except self.model.DoesNotExist:
            return None
