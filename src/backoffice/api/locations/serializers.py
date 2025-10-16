from rest_framework import serializers

from locations.models import TagLocation


class TagLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TagLocation
        fields = "__all__"
