import pytest
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
            "paired_at": tag.paired_at.isoformat(),
            "created": tag.created.isoformat().replace("+00:00", "Z"),
            "modified": tag.modified.isoformat().replace("+00:00", "Z"),
        }
