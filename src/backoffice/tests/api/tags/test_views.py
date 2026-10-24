import base64

import pytest
from django.contrib.auth import get_user_model
from django.shortcuts import resolve_url
from model_bakery import baker
from rest_framework import status

from api.tags.serializers import TagOutputSerializer, TagSummarySerializer
from locations.models import Tag

User = get_user_model()
USERNAME = "admin"
PASSWORD = "password"


@pytest.mark.django_db
class TestsTagListView:
    endpoint = resolve_url("api:tags-list")

    @pytest.fixture(autouse=True)
    def setup_class(self):
        User.objects.create_superuser(username=USERNAME, password=PASSWORD)
        self.auth_headers = {
            "HTTP_AUTHORIZATION": f"Basic {base64.b64encode(f'{USERNAME}:{PASSWORD}'.encode('utf-8')).decode('utf-8')}"
        }

    def test_url(self):
        assert self.endpoint == "/api/tags/"

    def test_missing_authentication(self, client):
        response = client.get(self.endpoint)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_success(self, client):
        tag = baker.make(Tag)
        response = client.get(self.endpoint, **self.auth_headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == [TagSummarySerializer(tag).data]

    def test_the_fetcher_gets_every_tag_with_its_keys(self, client, fetcher_headers):
        tag = baker.make(Tag)
        response = client.get(self.endpoint, **fetcher_headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == [TagOutputSerializer(tag).data]
