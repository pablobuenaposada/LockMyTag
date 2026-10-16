from rest_framework import serializers

from locations.models import Tag


class TagOutputSerializer(serializers.ModelSerializer):
    """Everything about a tag, including the keys only the fetcher needs."""

    class Meta:
        model = Tag
        fields = "__all__"


class TagSummarySerializer(serializers.ModelSerializer):
    """What the map needs. No keys: a browser has no use for them."""

    class Meta:
        model = Tag
        fields = ("id", "name", "emoji", "created")
