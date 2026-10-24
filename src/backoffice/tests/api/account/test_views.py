import base64

import pytest
from django.contrib.auth import get_user_model
from django.shortcuts import resolve_url
from django.test import Client
from model_bakery import baker
from rest_framework import status

from account.models import Account
from api.account.serializers import AccountOutputSerializer

User = get_user_model()
USERNAME = "admin"
PASSWORD = "password"


@pytest.mark.django_db
class TestsAccountListView:
    endpoint = resolve_url("api:account-list")

    def test_url(self):
        assert self.endpoint == "/api/account/"

    def test_missing_authentication(self, client):
        response = client.get(self.endpoint)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_an_ordinary_user_cannot_read_the_session(self, client):
        """A map login must not be enough to read the Apple credentials."""
        User.objects.create_user(username="mapuser", password=PASSWORD)
        headers = {
            "HTTP_AUTHORIZATION": f"Basic {base64.b64encode(f'mapuser:{PASSWORD}'.encode('utf-8')).decode('utf-8')}"
        }
        baker.make(Account)

        response = client.get(self.endpoint, **headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_not_even_a_superuser_can_read_the_session(self, client):
        """Only the fetcher's token opens it, not an admin login."""
        User.objects.create_superuser(username=USERNAME, password=PASSWORD)
        headers = {
            "HTTP_AUTHORIZATION": f"Basic {base64.b64encode(f'{USERNAME}:{PASSWORD}'.encode('utf-8')).decode('utf-8')}"
        }
        baker.make(Account)

        response = client.get(self.endpoint, **headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_success(self, client, fetcher_headers):
        tag = baker.make(Account)
        response = client.get(self.endpoint, **fetcher_headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == [AccountOutputSerializer(tag).data]


@pytest.mark.django_db
class TestsSessionLogoutView:
    endpoint = resolve_url("api:session-logout")

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = User.objects.create_user(username="mapuser", password=PASSWORD)

    def test_url(self):
        assert self.endpoint == "/api/account/logout/"

    def test_ends_the_session(self, client):
        client.force_login(self.user)
        assert (
            client.get(resolve_url("api:tags-list")).status_code == status.HTTP_200_OK
        )

        response = client.post(self.endpoint)

        assert response.status_code == status.HTTP_302_FOUND
        assert "_auth_user_id" not in client.session
        tags = client.get(resolve_url("api:tags-list"))
        assert tags.status_code == status.HTTP_401_UNAUTHORIZED

    def test_without_a_session_is_harmless(self, client):
        response = client.post(self.endpoint)

        assert response.status_code == status.HTTP_302_FOUND

    def test_another_site_cannot_log_you_out(self):
        """No CSRF token, so the session survives."""
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)

        response = client.post(self.endpoint)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "_auth_user_id" in client.session

    def test_the_map_can_log_out_with_the_csrf_cookie(self):
        """The same steps as the map: fetch the cookie, send it back."""
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)

        client.get(resolve_url("api:session-login"))
        token = client.cookies["csrftoken"].value
        response = client.post(self.endpoint, HTTP_X_CSRFTOKEN=token)

        assert response.status_code == status.HTTP_302_FOUND
        assert "_auth_user_id" not in client.session
