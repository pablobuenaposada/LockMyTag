import base64

import pytest
from django.shortcuts import resolve_url
from faker import Faker
from model_bakery import baker
from rest_framework import status

from api.locations.serializers import TagLocationInputSerializer
from locations.models import Tag, TagLocation


@pytest.mark.django_db
class TestsTagLocationCreateView:
    endpoint = resolve_url("api:locations-create")

    @pytest.fixture(autouse=True)
    def setup_class(self):
        fake = Faker()
        self.latitude = round(fake.latitude(), 7)
        self.longitude = round(fake.longitude(), 7)
        self.hash = base64.b64encode(fake.binary(length=33)).decode("utf-8")
        self.timestamp = fake.date_time()
        self.tag = baker.make(Tag)

    def test_url(self):
        assert self.endpoint == "/api/locations/"

    def test_success(self, client):
        assert not TagLocation.objects.exists()
        response = client.post(
            self.endpoint,
            {
                "tag": str(self.tag.id),
                "hash": self.hash,
                "latitude": self.latitude,
                "longitude": self.longitude,
                "timestamp": self.timestamp,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        location = TagLocation.objects.get()
        assert response.data == TagLocationInputSerializer(location).data
