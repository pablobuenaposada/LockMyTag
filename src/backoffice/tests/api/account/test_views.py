import pytest
from django.shortcuts import resolve_url
from model_bakery import baker
from rest_framework import status

from account.models import Account
from api.account.serializers import AccountOutputSerializer


@pytest.mark.django_db
class TestsAccountListView:
    endpoint = resolve_url("api:account-list")

    def test_url(self):
        assert self.endpoint == "/api/account/"

    def test_success(self, client):
        tag = baker.make(Account)
        response = client.get(self.endpoint)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == [AccountOutputSerializer(tag).data]
