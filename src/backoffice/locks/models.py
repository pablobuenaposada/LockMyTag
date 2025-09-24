from django.core.exceptions import ValidationError
from django.db import models
from django_extensions.db.models import TimeStampedModel
from simple_history.models import HistoricalRecords

from locations.models import Tag
from locks.managers import LockManager


class Lock(TimeStampedModel):
    STATUS_ACTIVE = "active"
    STATUS_INACTIVE = "inactive"
    STATUS_CHOICES = [(STATUS_ACTIVE, "Active"), (STATUS_INACTIVE, "Inactive")]

    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    latitude = models.FloatField(help_text="center latitude")
    longitude = models.FloatField(help_text="center longitude")
    radius = models.IntegerField(help_text="in meters")
    status = models.CharField(
        max_length=8, choices=STATUS_CHOICES, default=STATUS_ACTIVE
    )

    history = HistoricalRecords()
    objects = LockManager()


class LockSchedule(models.Model):
    DAYS_OF_WEEK = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]
    lock = models.ForeignKey(Lock, related_name="schedules", on_delete=models.CASCADE)
    day = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def _intervals_overlap(self, other_start, other_end):
        """check if two time intervals overlap with current one"""
        return self.start_time < other_end and self.end_time > other_start

    def _check_overlap(self):
        qs = LockSchedule.objects.filter(
            lock=self.lock,
            day=self.day,
        )
        if self.pk:
            # exclude self to avoid false positive overlap with itself in case of editing an existing schedule
            qs = qs.exclude(pk=self.pk)
        for schedule in qs:
            if self._intervals_overlap(schedule.start_time, schedule.end_time):
                raise ValidationError(
                    "Lock schedule times overlap with another schedule for the same lock and day"
                )

    def clean(self):
        super().clean()
        # only run custom validation if both times are present
        if self.start_time is not None and self.end_time is not None:
            if self.start_time >= self.end_time:
                raise ValidationError("Start time must be before end time")
            self._check_overlap()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
