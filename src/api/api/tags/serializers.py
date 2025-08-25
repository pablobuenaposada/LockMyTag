from rest_framework import serializers

from locations.models import Tag


class TagOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"
