import pytest
from django.shortcuts import resolve_url
from faker import Faker
from model_bakery import baker
from rest_framework import status
from rest_framework.exceptions import ErrorDetail

from api.locations.serializers import TagLocationSerializer
from locations.models import Tag, TagLocation


@pytest.mark.django_db
class TestsTagLocationCreateView:
    endpoint = resolve_url("api:locations-create")

    @pytest.fixture(autouse=True)
    def setup_class(self):
        fake = Faker()
        self.latitude = round(fake.latitude(), 7)
        self.longitude = round(fake.longitude(), 7)
        self.hash = fake.random_int()
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
        assert response.data == TagLocationSerializer(location).data


@pytest.mark.django_db
class TestsLatestTagLocationView:
    @pytest.fixture(autouse=True)
    def setup_class(self):
        fake = Faker()
        self.latitude = round(fake.latitude(), 7)
        self.longitude = round(fake.longitude(), 7)
        self.hash = fake.random_int()
        self.timestamp = fake.date_time()
        self.tag = baker.make(Tag)

    def test_url(self):
        assert (
            resolve_url("api:latest-tag-location", self.tag.id)
            == f"/api/locations/latest/{self.tag.id}"
        )

    def test_success(self, client):
        baker.make(TagLocation, tag=self.tag)
        location = baker.make(TagLocation, tag=self.tag)
        response = client.get(resolve_url("api:latest-tag-location", self.tag.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data == TagLocationSerializer(location).data

    def test_not_found(self, client):
        response = client.get(resolve_url("api:latest-tag-location", Faker().uuid4()))

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data == {
            "detail": ErrorDetail(string="Not found.", code="not_found")
        }
