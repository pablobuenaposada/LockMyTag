import pytest
from django.shortcuts import resolve_url
from model_bakery import baker
from rest_framework import status

from api.tags.serializers import TagOutputSerializer
from locations.models import Tag


@pytest.mark.django_db
class TestsTagListView:
    endpoint = resolve_url("api:tags-list")

    def test_url(self):
        assert self.endpoint == "/api/tags/"

    def test_success(self, client):
        tag = baker.make(Tag)
        response = client.get(self.endpoint)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == [TagOutputSerializer(tag).data]
