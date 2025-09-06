from django.core.exceptions import ValidationError
from django.db import models
from django_extensions.db.models import TimeStampedModel


class Account(TimeStampedModel):
    data = models.JSONField()

    def save(self, *args, **kwargs):
        if not self.pk and Account.objects.exists():
            raise ValidationError("Only one Account instance allowed")
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Account"