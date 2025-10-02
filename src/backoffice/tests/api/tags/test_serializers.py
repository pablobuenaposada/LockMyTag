import pytest
from django.utils import timezone
from model_bakery import baker

from api.tags.serializers import TagOutputSerializer
from locations.models import Tag


@pytest.mark.django_db
class TestsTagOutputSerializer:
    serializer_class = TagOutputSerializer

    def test_success(self):
        tag = baker.make(Tag)

        assert self.serializer_class(tag).data == {
            "id": str(tag.id),
            "name": tag.name,
            "master_key": tag.master_key,
            "skn": tag.skn,
            "sks": tag.sks,
            "paired_at": tag.paired_at.astimezone(
                timezone.get_current_timezone()
            ).isoformat(),
            "created": tag.created.astimezone(
                timezone.get_current_timezone()
            ).isoformat(),
            "modified": tag.modified.astimezone(
                timezone.get_current_timezone()
            ).isoformat(),
        }
