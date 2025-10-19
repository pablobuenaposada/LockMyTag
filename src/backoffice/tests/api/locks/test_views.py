import base64

import pytest
from django.contrib.auth import get_user_model
from django.shortcuts import resolve_url
from faker import Faker
from model_bakery import baker
from rest_framework import status
from rest_framework.exceptions import ErrorDetail

from api.locks.serializers import LockSerializer
from locations.models import Tag
from locks.models import Lock

User = get_user_model()
USERNAME = "admin"
PASSWORD = "password"


@pytest.mark.django_db
class TestsLockListByTagView:
    @pytest.fixture(autouse=True)
    def setup_class(self):
        self.tag = baker.make(Tag)
        User.objects.create_user(username=USERNAME, password=PASSWORD)
        self.auth_headers = {
            "HTTP_AUTHORIZATION": f"Basic {base64.b64encode(f'{USERNAME}:{PASSWORD}'.encode('utf-8')).decode('utf-8')}"
        }

    def test_url(self):
        assert (
            resolve_url("api:locks-by-tag", self.tag.id) == f"/api/locks/{self.tag.id}"
        )

    def test_missing_authentication(self, client):
        response = client.get(resolve_url("api:locks-by-tag", self.tag.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_success(self, client):
        lock = baker.make(Lock, tag=self.tag)
        response = client.get(
            resolve_url("api:locks-by-tag", self.tag.id), **self.auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data == [LockSerializer(lock).data]

    def test_not_found(self, client):
        response = client.get(
            resolve_url("api:locks-by-tag", Faker().uuid4()), **self.auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data == {
            "detail": ErrorDetail(string="Not found.", code="not_found")
        }
