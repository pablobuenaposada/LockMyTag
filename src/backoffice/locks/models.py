from django.core.exceptions import ValidationError
from django.db import models
from django_extensions.db.models import TimeStampedModel
from simple_history.models import HistoricalRecords

from locations.models import Tag


class Lock(TimeStampedModel):
    STATUS_ACTIVE = "active"
    STATUS_INACTIVE = "inactive"
    STATUS_CHOICES = [(STATUS_ACTIVE, "Active"), (STATUS_INACTIVE, "Inactive")]

    DAYS_OF_WEEK = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]

    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    latitude = models.FloatField(help_text="center latitude")
    longitude = models.FloatField(help_text="center longitude")
    radius = models.IntegerField(help_text="in meters")
    status = models.CharField(
        max_length=8, choices=STATUS_CHOICES, default=STATUS_ACTIVE
    )
    last_notified = models.DateTimeField(
        null=True, blank=True, help_text="last time that the lock has been notified"
    )
    schedule_day = models.IntegerField(choices=DAYS_OF_WEEK, null=True, blank=True)
    schedule_start_time = models.TimeField(null=True, blank=True)
    schedule_end_time = models.TimeField(null=True, blank=True)

    history = HistoricalRecords()

    def _check_schedule_field(self):
        """Ensure that if any schedule field is set, all must be set"""
        schedule_fields = [
            self.schedule_day,
            self.schedule_start_time,
            self.schedule_end_time,
        ]
        if any(field is not None for field in schedule_fields) and not all(
            field is not None for field in schedule_fields
        ):
            raise ValidationError(
                "All schedule fields (day, start time, end time) must be filled if any of them is set"
            )

    def _check_overlap(self):
        # only proceed if all schedule fields are set
        if not all(
            field is not None
            for field in [
                self.schedule_day,
                self.schedule_start_time,
                self.schedule_end_time,
            ]
        ):
            return

        # query for locks with the same tag and day
        qs = Lock.objects.filter(
            tag=self.tag,
            schedule_day=self.schedule_day,
        )

        # exclude the current lock if it's already saved
        if self.pk:
            qs = qs.exclude(pk=self.pk)

        for lock in qs:
            if (
                self.schedule_start_time < lock.schedule_end_time
                and self.schedule_end_time > lock.schedule_start_time
            ):
                raise ValidationError(
                    "Lock schedule times overlap with another lock for the same tag and day"
                )

    def clean(self):
        super().clean()
        self._check_schedule_field()
        self._check_overlap()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
