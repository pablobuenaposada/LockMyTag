import pytest
from django.contrib.auth import get_user_model
from django.shortcuts import resolve_url
from model_bakery import baker
from rest_framework import status

from account.models import Account
from locations.models import Tag

User = get_user_model()


@pytest.mark.django_db
class TestsFetcherToken:
    endpoint = resolve_url("api:account-list")

    @pytest.fixture(autouse=True)
    def setup(self):
        baker.make(Account)

    def test_the_right_token(self, client, fetcher_headers):
        response = client.get(self.endpoint, **fetcher_headers)

        assert response.status_code == status.HTTP_200_OK

    def test_a_wrong_token(self, client, fetcher_headers):
        response = client.get(self.endpoint, HTTP_AUTHORIZATION="Bearer nope")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_an_unset_token_lets_nobody_in(self, client, settings):
        """An empty FETCHER_TOKEN must not be matched by an empty bearer."""
        settings.FETCHER_TOKEN = ""

        for header in ("Bearer ", "Bearer", "Bearer  "):
            response = client.get(self.endpoint, HTTP_AUTHORIZATION=header)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_the_token_opens_nothing_else(self, client, fetcher_headers):
        """It is not a login: the map's endpoints and the admin ignore it."""
        tag = baker.make(Tag)

        for url in (
            resolve_url("api:latest-tag-location", tag.id),
            resolve_url("api:tag-location-route", tag.id),
        ):
            response = client.get(url, **fetcher_headers)
            assert response.status_code == status.HTTP_403_FORBIDDEN

        response = client.get(resolve_url("admin:index"), **fetcher_headers)
        assert response.status_code == status.HTTP_302_FOUND  # to the login page
