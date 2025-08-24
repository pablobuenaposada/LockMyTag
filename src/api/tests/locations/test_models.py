from unittest.mock import ANY

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from faker import Faker
from model_bakery import baker

from locations.models import Tag, TagLocation


@pytest.mark.django_db
class TestTag:
    def test_success(self):
        fake = Faker()
        expected = {
            "id": ANY,
            "name": "Test Tag",
            "master_key": fake.bothify("?" * 28),
            "skn": fake.bothify("?" * 44),
            "paired_at": "2025-07-23",
            "created": ANY,
            "modified": ANY,
        }
        tag = Tag.objects.create(
            name=expected["name"],
            master_key=expected["master_key"],
            skn=expected["skn"],
            paired_at=expected["paired_at"],
        )

        for field in [
            field.name
            for field in Tag._meta.get_fields()
            if field.name not in ["taglocation"]
        ]:
            assert getattr(tag, field) == expected[field]

    @pytest.mark.parametrize(
        "fields, error",
        [
            ({"name": "foo", "master_key": "0" * 28, "skn": "0" * 44}, IntegrityError),
            (
                {"name": "foo", "master_key": "0" * 28, "paired_at": "2025-07-23"},
                ValidationError,
            ),
            (
                {"name": "foo", "skn": "0" * 44, "paired_at": "2025-07-23"},
                ValidationError,
            ),
            (
                {"master_key": "0" * 28, "skn": "0" * 44, "paired_at": "2025-07-23"},
                ValidationError,
            ),
        ],
    )
    def test_mandatory_fields(self, fields, error):
        with pytest.raises(error):
            Tag.objects.create(**fields)


@pytest.mark.django_db
class TestTagLocation:
    fake = Faker()
    latitude = fake.latitude()
    longitude = fake.longitude()

    def test_success(self):
        tag = baker.make(Tag)
        expected = {
            "id": ANY,
            "created": ANY,
            "modified": ANY,
            "tag": tag,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }
        tag_location = TagLocation.objects.create(
            tag=tag, latitude=self.latitude, longitude=self.longitude
        )

        for field in [field.name for field in TagLocation._meta.get_fields()]:
            assert getattr(tag_location, field) == expected[field]

    @pytest.mark.parametrize(
        "fields, error",
        [({"latitude": 1}, IntegrityError), ({"longitude": 1}, IntegrityError)],
    )
    def test_mandatory_fields(self, fields, error):
        with pytest.raises(error):
            TagLocation.objects.create(**{**fields, "tag": baker.make(Tag)})
