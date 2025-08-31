from datetime import timezone

import pytest
from faker import Faker
from model_bakery import baker
from rest_framework.exceptions import ErrorDetail

from api.locations.serializers import TagLocationInputSerializer
from locations.models import Tag


@pytest.mark.django_db
class TestsTagLocationInputSerializer:
    serializer_class = TagLocationInputSerializer

    @pytest.fixture(autouse=True)
    def setup_class(self):
        fake = Faker()
        self.latitude = round(fake.latitude(), 7)
        self.longitude = round(fake.longitude(), 7)
        self.hash = fake.random_int()
        self.timestamp = fake.date_time()
        self.tag = baker.make(Tag)

    def test_mandatory(self):
        serializer = self.serializer_class(data={})

        assert not serializer.is_valid()
        assert serializer.errors == {
            "tag": [ErrorDetail(string="This field is required.", code="required")],
            "hash": [ErrorDetail(string="This field is required.", code="required")],
            "latitude": [
                ErrorDetail(string="This field is required.", code="required")
            ],
            "longitude": [
                ErrorDetail(string="This field is required.", code="required")
            ],
            "timestamp": [
                ErrorDetail(string="This field is required.", code="required")
            ],
        }

    def test_success(self):
        serializer = self.serializer_class(
            data={
                "tag": str(self.tag.id),
                "hash": self.hash,
                "latitude": self.latitude,
                "longitude": self.longitude,
                "timestamp": self.timestamp,
            }
        )

        assert serializer.is_valid()
        assert serializer.validated_data == {
            "tag": self.tag,
            "hash": self.hash,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timestamp": self.timestamp.replace(tzinfo=timezone.utc),
        }
