from rest_framework import serializers

from locations.models import TagLocation


class TagLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TagLocation
        fields = "__all__"


class TagLocationRouteSerializer(serializers.ModelSerializer):
    """Slim representation for routes, where thousands of points may be returned."""

    class Meta:
        model = TagLocation
        fields = ("latitude", "longitude", "timestamp")
