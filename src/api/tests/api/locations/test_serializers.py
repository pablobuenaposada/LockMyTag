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
        self.latitude = round(fake.latitude(), 6)
        self.longitude = round(fake.longitude(), 6)
        self.tag = baker.make(Tag)

    def test_mandatory(self):
        serializer = self.serializer_class(data={})

        assert not serializer.is_valid()
        assert serializer.errors == {
            "tag": [ErrorDetail(string="This field is required.", code="required")],
            "latitude": [
                ErrorDetail(string="This field is required.", code="required")
            ],
            "longitude": [
                ErrorDetail(string="This field is required.", code="required")
            ],
        }

    def test_success(self):
        serializer = self.serializer_class(
            data={
                "tag": str(self.tag.id),
                "latitude": self.latitude,
                "longitude": self.longitude,
            }
        )

        assert serializer.is_valid()
        assert serializer.validated_data == {
            "tag": self.tag,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }
