import base64
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
            "sks": fake.bothify("?" * 44),
            "paired_at": "2025-07-23",
            "created": ANY,
            "modified": ANY,
        }
        tag = Tag.objects.create(
            name=expected["name"],
            master_key=expected["master_key"],
            skn=expected["skn"],
            sks=expected["sks"],
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
            (
                {
                    "name": "foo",
                    "master_key": "0" * 28,
                    "skn": "0" * 44,
                    "sks": "0" * 44,
                },
                IntegrityError,
            ),
            (
                {"name": "foo", "master_key": "0" * 28, "paired_at": "2025-07-23"},
                ValidationError,
            ),
            (
                {
                    "name": "foo",
                    "skn": "0" * 44,
                    "sks": "0" * 44,
                    "paired_at": "2025-07-23",
                },
                ValidationError,
            ),
            (
                {
                    "master_key": "0" * 28,
                    "skn": "0" * 44,
                    "sks": "0" * 44,
                    "paired_at": "2025-07-23",
                },
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
    latitude = round(fake.latitude(), 6)
    longitude = round(fake.longitude(), 6)
    hash = base64.b64encode(fake.binary(length=33)).decode("utf-8")
    timestamp = fake.date_time()

    def test_success(self):
        tag = baker.make(Tag)
        expected = {
            "id": ANY,
            "created": ANY,
            "modified": ANY,
            "tag": tag,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "hash": ANY,
            "timestamp": ANY,
        }
        tag_location = TagLocation.objects.create(
            tag=tag,
            latitude=self.latitude,
            longitude=self.longitude,
            hash=hash,
            timestamp=self.timestamp,
        )

        for field in [field.name for field in TagLocation._meta.get_fields()]:
            assert getattr(tag_location, field) == expected[field]

    @pytest.mark.parametrize(
        "fields, error",
        [
            ({}, ValidationError),
            ({"hash": "abc"}, IntegrityError),
            ({"hash": "abc", "latitude": 1}, IntegrityError),
            ({"hash": "abc", "latitude": 1, "longitude": 1}, IntegrityError),
            (
                {
                    "timestamp": "2023-09-13",
                },
                ValidationError,
            ),
        ],
    )
    def test_mandatory_fields(self, fields, error):
        with pytest.raises(error):
            TagLocation.objects.create(**{**fields, "tag": baker.make(Tag)})
