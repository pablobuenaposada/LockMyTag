from rest_framework import generics

from api.locations.serializers import TagLocationInputSerializer
from locations.models import TagLocation


class TagLocationCreateView(generics.CreateAPIView):
    queryset = TagLocation.objects.all()
    serializer_class = TagLocationInputSerializer
