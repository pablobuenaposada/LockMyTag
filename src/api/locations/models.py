from django_extensions.db.models import TimeStampedModel
from django.db import models
from django.core.validators import MinLengthValidator


class Tag(TimeStampedModel):
    id = models.CharField(max_length=255, unique=True, primary_key=True, help_text="Unique identifier for the AirTag")
    name = models.CharField(max_length=255, help_text="Name for the AirTag")
    master_key = models.CharField(max_length=28, validators=[MinLengthValidator(28)])
    skn = models.CharField(max_length=44, validators=[MinLengthValidator(44)])
    paired_at = models.DateField(help_text="Date when the AirTag was paired")


class TagLocation(TimeStampedModel):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, help_text="Associated AirTag")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, help_text="Latitude of the location")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, help_text="Longitude of the location")
