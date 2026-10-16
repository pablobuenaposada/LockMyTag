from rest_framework import generics

from api.tags.serializers import TagOutputSerializer, TagSummarySerializer
from locations.models import Tag


class TagListView(generics.ListAPIView):
    def get_queryset(self):
        return Tag.objects.visible_to(self.request.user)

    def get_serializer_class(self):
        # The fetcher authenticates as staff and needs the keys to decrypt
        # reports; nobody else has any use for them
        if self.request.user.is_staff:
            return TagOutputSerializer
        return TagSummarySerializer
