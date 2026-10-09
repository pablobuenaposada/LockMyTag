from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.shortcuts import resolve_url
from model_bakery import baker
from rest_framework import status

from account.admin import SESSION_KEY
from account.apple import ReauthError
from account.models import Account

User = get_user_model()
STORED = {
    "type": "account",
    "account": {"username": "pablo@example.com", "password": "hunter2"},
}
RENEWED = {
    "type": "account",
    "account": {"username": "pablo@example.com", "password": "hunter2"},
}
METHODS = [(0, "Trusted device"), (1, "SMS to +34 •• 12")]


@pytest.mark.django_db
class TestsReauthenticate:
    endpoint = resolve_url("admin:account_account_reauthenticate")
    changelist = resolve_url("admin:account_account_changelist")

    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.admin = User.objects.create_superuser(username="admin", password="admin")
        client.force_login(self.admin)
        self.client = client

    def test_url(self):
        assert self.endpoint == "/admin/account/account/reauthenticate/"

    def test_requires_staff(self, client):
        client.logout()
        response = client.get(self.endpoint)

        assert response.status_code == status.HTTP_302_FOUND
        assert "/admin/login/" in response.url

    def test_button_on_changelist(self):
        baker.make(Account, data=STORED)

        response = self.client.get(self.changelist)

        assert self.endpoint in response.content.decode()

    def test_it_always_asks_for_credentials(self):
        response = self.client.get(self.endpoint)

        assert response.status_code == status.HTTP_200_OK
        assert "Apple Account" in response.content.decode()

    def test_first_login_from_scratch(self):
        with patch(
            "account.admin.start_fresh", return_value=(STORED, METHODS)
        ) as start_fresh:
            response = self.client.post(
                self.endpoint, {"username": "pablo@example.com", "password": "hunter2"}
            )

        start_fresh.assert_called_once_with("pablo@example.com", "hunter2")
        assert "Trusted device" in response.content.decode()
        assert self.client.session[SESSION_KEY]["state"] == STORED

    def test_first_login_creates_the_account(self):
        assert not Account.objects.exists()
        session = self.client.session
        session[SESSION_KEY] = {
            "state": STORED,
            "methods": METHODS,
            "method": 0,
            "sent_by": "Trusted device",
        }
        session.save()

        with patch("account.admin.submit_code", return_value=RENEWED):
            response = self.client.post(self.endpoint, {"code": "123456"})

        assert response.status_code == status.HTTP_302_FOUND
        assert Account.objects.get().data == RENEWED

    def test_credentials_apple_rejects(self):
        with patch(
            "account.admin.start_fresh", side_effect=ReauthError("Apple refused it")
        ):
            response = self.client.post(
                self.endpoint, {"username": "pablo@example.com", "password": "wrong"}
            )

        assert response.status_code == status.HTTP_200_OK
        assert "Apple refused it" in response.content.decode()
        assert not Account.objects.exists()

    def test_choosing_a_method_sends_a_code(self):
        baker.make(Account, data=STORED)
        session = self.client.session
        session[SESSION_KEY] = {"state": STORED, "methods": METHODS}
        session.save()

        with patch(
            "account.admin.request_code", return_value=(STORED, "Trusted device")
        ) as request_code:
            response = self.client.post(self.endpoint, {"method": "1"})

        request_code.assert_called_once_with(STORED, 1)
        assert response.status_code == status.HTTP_200_OK
        assert "Code from Apple" in response.content.decode()
        assert self.client.session[SESSION_KEY]["method"] == 1

    def test_the_code_renews_the_account(self):
        account = baker.make(Account, data=STORED)
        session = self.client.session
        session[SESSION_KEY] = {
            "state": STORED,
            "methods": METHODS,
            "method": 0,
            "sent_by": "Trusted device",
        }
        session.save()

        with patch("account.admin.submit_code", return_value=RENEWED) as submit:
            response = self.client.post(self.endpoint, {"code": "123456"})

        submit.assert_called_once_with(STORED, 0, "123456")
        account.refresh_from_db()
        assert account.data == RENEWED
        assert response.status_code == status.HTTP_302_FOUND
        assert response.url == self.changelist
        assert SESSION_KEY not in self.client.session
        assert Account.objects.count() == 1  # re-login replaces, never adds

    def test_a_rejected_code_keeps_the_form(self):
        account = baker.make(Account, data=STORED)
        session = self.client.session
        session[SESSION_KEY] = {
            "state": STORED,
            "methods": METHODS,
            "method": 0,
            "sent_by": "Trusted device",
        }
        session.save()

        with patch(
            "account.admin.submit_code",
            side_effect=ReauthError("Apple rejected that code"),
        ):
            response = self.client.post(self.endpoint, {"code": "000000"})

        account.refresh_from_db()
        assert account.data == STORED
        assert response.status_code == status.HTTP_200_OK
        assert "Apple rejected that code" in response.content.decode()

    def test_a_code_without_a_pending_login(self):
        baker.make(Account, data=STORED)

        response = self.client.post(self.endpoint, {"code": "123456"})

        assert response.status_code == status.HTTP_302_FOUND
        assert response.url == self.endpoint

    def test_asks_even_with_a_working_session(self):
        """The stored password is never used, so every login is typed in."""
        baker.make(Account, data=STORED)

        response = self.client.get(self.endpoint)

        assert response.status_code == status.HTTP_200_OK
        assert "Apple Account" in response.content.decode()
        assert 'value="pablo@example.com"' in response.content.decode()
