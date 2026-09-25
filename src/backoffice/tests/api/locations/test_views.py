import base64
from datetime import datetime

import pytest
from django.contrib.auth import get_user_model
from django.shortcuts import resolve_url
from django.utils.timezone import make_aware
from faker import Faker
from model_bakery import baker
from rest_framework import status
from rest_framework.exceptions import ErrorDetail

from api.locations.serializers import (
    TagLocationRouteSerializer,
    TagLocationSerializer,
)
from locations.models import Tag, TagLocation

User = get_user_model()
USERNAME = "admin"
PASSWORD = "password"


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
        User.objects.create_user(username=USERNAME, password=PASSWORD)
        self.auth_headers = {
            "HTTP_AUTHORIZATION": f"Basic {base64.b64encode(f'{USERNAME}:{PASSWORD}'.encode('utf-8')).decode('utf-8')}"
        }

    def test_url(self):
        assert self.endpoint == "/api/locations/"

    def test_missing_authentication(self, client):
        response = client.post(self.endpoint)

        assert response.status_code == status.HTTP_403_FORBIDDEN

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
            **self.auth_headers,
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
        User.objects.create_user(username=USERNAME, password=PASSWORD)
        self.auth_headers = {
            "HTTP_AUTHORIZATION": f"Basic {base64.b64encode(f'{USERNAME}:{PASSWORD}'.encode('utf-8')).decode('utf-8')}"
        }

    def test_url(self):
        assert (
            resolve_url("api:latest-tag-location", self.tag.id)
            == f"/api/locations/latest/{self.tag.id}"
        )

    def test_missing_authentication(self, client):
        response = client.get(resolve_url("api:latest-tag-location", self.tag.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_success(self, client):
        baker.make(TagLocation, tag=self.tag)
        location = baker.make(TagLocation, tag=self.tag)
        response = client.get(
            resolve_url("api:latest-tag-location", self.tag.id), **self.auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data == TagLocationSerializer(location).data

    def test_not_found(self, client):
        response = client.get(
            resolve_url("api:latest-tag-location", Faker().uuid4()), **self.auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data == {
            "detail": ErrorDetail(string="Not found.", code="not_found")
        }


@pytest.mark.django_db
class TestsTagLocationRouteView:
    @pytest.fixture(autouse=True)
    def setup_class(self):
        self.tag = baker.make(Tag)
        User.objects.create_user(username=USERNAME, password=PASSWORD)
        self.auth_headers = {
            "HTTP_AUTHORIZATION": f"Basic {base64.b64encode(f'{USERNAME}:{PASSWORD}'.encode('utf-8')).decode('utf-8')}"
        }

    def _make_location(self, timestamp):
        fake = Faker()
        return baker.make(
            TagLocation,
            tag=self.tag,
            timestamp=timestamp,
            latitude=round(fake.latitude(), 7),
            longitude=round(fake.longitude(), 7),
        )

    def test_url(self):
        assert (
            resolve_url("api:tag-location-route", self.tag.id)
            == f"/api/locations/route/{self.tag.id}"
        )

    def test_missing_authentication(self, client):
        response = client.get(resolve_url("api:tag-location-route", self.tag.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unknown_tag(self, client):
        response = client.get(
            resolve_url("api:tag-location-route", Faker().uuid4()), **self.auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_points_ordered_by_timestamp(self, client):
        newest = self._make_location(make_aware(datetime(2026, 9, 3)))
        oldest = self._make_location(make_aware(datetime(2026, 9, 1)))

        response = client.get(
            resolve_url("api:tag-location-route", self.tag.id), **self.auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        assert response.data["truncated"] is False
        assert [point["timestamp"] for point in response.data["points"]] == [
            TagLocationRouteSerializer(oldest).data["timestamp"],
            TagLocationRouteSerializer(newest).data["timestamp"],
        ]

    def test_filters_by_date_range_inclusive_of_whole_end_day(self, client):
        self._make_location(make_aware(datetime(2026, 8, 31, 23, 59)))
        inside = self._make_location(make_aware(datetime(2026, 9, 1, 12, 0)))
        end_of_day = self._make_location(make_aware(datetime(2026, 9, 2, 23, 30)))
        self._make_location(make_aware(datetime(2026, 9, 3, 0, 30)))

        response = client.get(
            f"{resolve_url('api:tag-location-route', self.tag.id)}"
            "?start=2026-09-01&end=2026-09-02",
            **self.auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        assert [point["timestamp"] for point in response.data["points"]] == [
            TagLocationRouteSerializer(inside).data["timestamp"],
            TagLocationRouteSerializer(end_of_day).data["timestamp"],
        ]

    def test_excludes_other_tags(self, client):
        self._make_location(make_aware(datetime(2026, 9, 1)))
        baker.make(TagLocation, tag=baker.make(Tag))

        response = client.get(
            resolve_url("api:tag-location-route", self.tag.id), **self.auth_headers
        )

        assert response.data["count"] == 1

    def test_truncates_and_flags(self, client, monkeypatch):
        monkeypatch.setattr("api.locations.views.ROUTE_MAX_POINTS", 2)
        for day in (1, 2, 3):
            self._make_location(make_aware(datetime(2026, 9, day)))

        response = client.get(
            resolve_url("api:tag-location-route", self.tag.id), **self.auth_headers
        )

        assert response.data["count"] == 2
        assert response.data["truncated"] is True

    @pytest.mark.parametrize(
        "query",
        ["?start=not-a-date", "?end=not-a-date", "?start=2026-09-05&end=2026-09-01"],
    )
    def test_invalid_range(self, client, query):
        response = client.get(
            f"{resolve_url('api:tag-location-route', self.tag.id)}{query}",
            **self.auth_headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
