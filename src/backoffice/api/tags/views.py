from rest_framework import generics

from api.fetcher import FETCHER_OR_USER_AUTHENTICATION, is_fetcher
from api.tags.serializers import TagOutputSerializer, TagSummarySerializer
from locations.models import Tag


class TagListView(generics.ListAPIView):
    authentication_classes = FETCHER_OR_USER_AUTHENTICATION

    def get_queryset(self):
        # The fetcher tracks every tag, whoever it is shared with
        if is_fetcher(self.request):
            return Tag.objects.all()
        return Tag.objects.visible_to(self.request.user)

    def get_serializer_class(self):
        # The fetcher needs the keys to decrypt reports; nobody else has any
        # use for them
        if is_fetcher(self.request):
            return TagOutputSerializer
        return TagSummarySerializer
