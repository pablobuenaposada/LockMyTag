import uuid

from django.core.validators import MinLengthValidator
from django.db import models
from django_extensions.db.models import TimeStampedModel

from locations.validators import validate_empty


class Tag(TimeStampedModel):
    id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, primary_key=True
    )
    name = models.CharField(max_length=255, help_text="Name for the AirTag")
    master_key = models.CharField(max_length=28, validators=[MinLengthValidator(28)])
    skn = models.CharField(max_length=44, validators=[MinLengthValidator(44)])
    paired_at = models.DateField()

    def save(self, **kwargs):
        validate_empty(self.master_key)
        validate_empty(self.skn)
        validate_empty(self.name)
        super().save(**kwargs)


class TagLocation(TimeStampedModel):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
