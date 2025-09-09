from unittest.mock import ANY

import pytest
from django.db import IntegrityError
from faker import Faker
from model_bakery import baker

from locations.models import Tag
from locks.models import Lock


@pytest.mark.django_db
class TestLock:
    fake = Faker()
    latitude = round(fake.latitude(), 6)
    longitude = round(fake.longitude(), 6)
    radius = fake.pyint()

    def test_success(self):
        tag = baker.make(Tag)
        expected = {
            "id": ANY,
            "created": ANY,
            "modified": ANY,
            "tag": tag,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "radius": self.radius,
            "status": Lock.STATUS_ACTIVE,
            "last_notified": None,
        }
        lock = Lock.objects.create(
            tag=tag,
            latitude=self.latitude,
            longitude=self.longitude,
            radius=self.radius,
        )

        for field in [field.name for field in Lock._meta.get_fields()]:
            assert getattr(lock, field) == expected[field]

    @pytest.mark.parametrize(
        "fields, error",
        [
            ({}, IntegrityError),
            ({"latitude": 1}, IntegrityError),
            ({"latitude": 1, "longitude": 1}, IntegrityError),
        ],
    )
    def test_mandatory_fields(self, fields, error):
        fields["tag"] = baker.make(Tag)
        with pytest.raises(error):
            Lock.objects.create(**fields)

    def test_unique_tag_per_lock(self):
        tag = baker.make(Tag)
        Lock.objects.create(
            tag=tag,
            latitude=self.latitude,
            longitude=self.longitude,
            radius=self.radius,
        )
        with pytest.raises(IntegrityError):
            Lock.objects.create(
                tag=tag,
                latitude=self.latitude,
                longitude=self.longitude,
                radius=self.radius,
            )
