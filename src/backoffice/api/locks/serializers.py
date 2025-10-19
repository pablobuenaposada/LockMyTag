from rest_framework import serializers

from locks.models import Lock, LockSchedule


class LockScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = LockSchedule
        fields = "__all__"


class LockSerializer(serializers.ModelSerializer):
    schedules = LockScheduleSerializer(many=True, read_only=True)

    class Meta:
        model = Lock
        fields = "__all__"
