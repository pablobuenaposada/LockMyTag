from django.db import models
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone


class LockManager(models.Manager):
    def get_active_applicable_locks(self, tag):
        """
        Get active locks for a specific tag that are currently applicable:
        - Either no schedules (which means the lock applies for the entire day)
        - Or at least one schedule for current day and time is within schedule window
        """
        now = timezone.localtime(timezone.now())
        current_day = now.weekday()
        current_time = now.time()

        # import here to avoid circular import
        from .models import LockSchedule

        # subquery: is there a schedule for this lock, today, and now within window?
        applicable_schedule = LockSchedule.objects.filter(
            lock=OuterRef("pk"),
            day=current_day,
            start_time__lte=current_time,
            end_time__gt=current_time,
        )
        # locks with no schedules or with at least one applicable schedule
        qs = self.filter(tag=tag, status=self.model.STATUS_ACTIVE).filter(
            Q(~Exists(LockSchedule.objects.filter(lock=OuterRef("pk"))))
            | Exists(applicable_schedule)
        )
        try:
            return qs.get()
        except self.model.DoesNotExist:
            return None
