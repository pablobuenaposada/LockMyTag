from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from api.locations.serializers import TagLocationSerializer
from locations.models import TagLocation


class TagLocationCreateView(generics.CreateAPIView):
    queryset = TagLocation.objects.all()
    serializer_class = TagLocationSerializer


class LatestTagLocationView(generics.GenericAPIView):
    serializer_class = TagLocationSerializer

    def get(self, request, tag_id):
        if not (
            latest_location := TagLocation.objects.filter(tag_id=tag_id)
            .order_by("-timestamp")
            .first()
        ):
            raise NotFound()
        return Response(self.get_serializer(latest_location).data)
