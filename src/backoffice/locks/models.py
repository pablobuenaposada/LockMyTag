from django.db import models
from django_extensions.db.models import TimeStampedModel
from simple_history.models import HistoricalRecords

from locations.models import Tag


class Lock(TimeStampedModel):
    STATUS_ACTIVE = "active"
    STATUS_INACTIVE = "inactive"
    STATUS_CHOICES = [(STATUS_ACTIVE, "Active"), (STATUS_INACTIVE, "Inactive")]

    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    latitude = models.FloatField(help_text="center latitude")
    longitude = models.FloatField(help_text="center longitude")
    radius = models.IntegerField()  # in meters
    status = models.CharField(
        max_length=8, choices=STATUS_CHOICES, default=STATUS_ACTIVE
    )
    last_notified = models.DateTimeField(
        null=True, blank=True, help_text="last time that the lock has been notified"
    )

    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tag"], name="unique_tag_per_lock")
        ]
