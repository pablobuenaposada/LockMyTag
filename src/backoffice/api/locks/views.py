from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.exceptions import NotFound

from api.locks.serializers import LockSerializer
from locations.models import Tag
from locks.models import Lock


class LockListByTagView(generics.ListAPIView):
    serializer_class = LockSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status"]

    def get_queryset(self):
        tag_id = self.kwargs.get("tag_id")
        if not tag_id:
            raise NotFound()
        if not Tag.objects.filter(id=tag_id).exists():
            raise NotFound()
        return Lock.objects.filter(tag__id=tag_id)
