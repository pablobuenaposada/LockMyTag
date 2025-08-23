import pytest

from locations.models import Tag
from faker import Faker
from unittest.mock import ANY


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
            "modified": ANY
        }
        tag = Tag.objects.create(
            name=expected["name"],
            master_key=expected["master_key"],
            skn=expected["skn"],
            paired_at=expected["paired_at"]
        )

        for field in [
            field.name
            for field in Tag._meta.get_fields()
            if field.name not in ["taglocation"]
        ]:
            assert getattr(tag, field) == expected[field]
