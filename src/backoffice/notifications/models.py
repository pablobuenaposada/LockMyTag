from django.db import models
from django_extensions.db.models import TimeStampedModel


class TelegramChat(TimeStampedModel):
    chat_id = models.BigIntegerField(unique=True)
