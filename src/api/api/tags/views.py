from rest_framework import generics

from api.tags.serializers import TagOutputSerializer
from locations.models import Tag


class TagListView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagOutputSerializer
