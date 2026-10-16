import base64

import pytest
from django.contrib.auth import get_user_model
from django.shortcuts import resolve_url
from model_bakery import baker
from rest_framework import status

from locations.models import Tag, TagLocation
from locks.models import Lock

User = get_user_model()
PASSWORD = "password"


def auth(username):
    token = base64.b64encode(f"{username}:{PASSWORD}".encode()).decode()
    return {"HTTP_AUTHORIZATION": f"Basic {token}"}


@pytest.mark.django_db
class TestsTagVisibility:
    """A viewer sees the tags shared with them and nothing else."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.owner = User.objects.create_superuser(username="owner", password=PASSWORD)
        self.guest = User.objects.create_user(username="guest", password=PASSWORD)
        self.shared = baker.make(Tag, name="shared")
        self.private = baker.make(Tag, name="private")
        self.shared.viewers.add(self.guest)

    def test_the_list_only_holds_shared_tags(self, client):
        response = client.get(resolve_url("api:tags-list"), **auth("guest"))

        assert [tag["name"] for tag in response.data] == ["shared"]

    def test_the_owner_still_sees_everything(self, client):
        response = client.get(resolve_url("api:tags-list"), **auth("owner"))

        assert {tag["name"] for tag in response.data} == {"shared", "private"}

    def test_a_viewer_is_not_given_the_keys(self, client):
        response = client.get(resolve_url("api:tags-list"), **auth("guest"))

        assert set(response.data[0]) == {"id", "name", "emoji", "created"}

    def test_the_fetcher_still_gets_the_keys(self, client):
        response = client.get(resolve_url("api:tags-list"), **auth("owner"))

        assert "master_key" in response.data[0]

    def test_latest_location_of_a_tag_not_shared(self, client):
        baker.make(TagLocation, tag=self.private)

        response = client.get(
            resolve_url("api:latest-tag-location", self.private.id), **auth("guest")
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_latest_location_of_a_shared_tag(self, client):
        baker.make(TagLocation, tag=self.shared)

        response = client.get(
            resolve_url("api:latest-tag-location", self.shared.id), **auth("guest")
        )

        assert response.status_code == status.HTTP_200_OK

    def test_route_of_a_tag_not_shared(self, client):
        response = client.get(
            resolve_url("api:tag-location-route", self.private.id), **auth("guest")
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_locks_of_a_tag_not_shared(self, client):
        baker.make(Lock, tag=self.private)

        response = client.get(
            resolve_url("api:locks-by-tag", self.private.id), **auth("guest")
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_a_viewer_cannot_invent_a_location(self, client):
        """Read-only means read-only: the fetcher alone writes locations."""
        response = client.post(
            resolve_url("api:locations-create"),
            {
                "tag": str(self.shared.id),
                "latitude": "41.0000000",
                "longitude": "2.0000000",
                "timestamp": "2026-10-16T10:00:00Z",
            },
            **auth("guest"),
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not TagLocation.objects.exists()

    def test_a_viewer_cannot_reach_the_admin(self, client):
        client.force_login(self.guest)

        response = client.get("/admin/locks/lock/add/")

        assert response.status_code == status.HTTP_302_FOUND
        assert "/admin/login/" in response.url
