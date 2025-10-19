import pytest
from django.utils import timezone
from model_bakery import baker

from api.locks.serializers import LockScheduleSerializer, LockSerializer
from locks.models import Lock, LockSchedule


@pytest.mark.django_db
class TestsLockScheduleSerializer:
    serializer_class = LockScheduleSerializer

    @pytest.fixture(autouse=True)
    def setup_class(self):
        self.lock = baker.make(Lock)
        self.schedule = baker.make(LockSchedule)

    def test_success(self):
        assert self.serializer_class(self.schedule).data == {
            "day": self.schedule.day,
            "end_time": self.schedule.end_time.isoformat(),
            "id": self.schedule.id,
            "lock": self.schedule.lock.id,
            "start_time": self.schedule.start_time.isoformat(),
        }


@pytest.mark.django_db
class TestsLockSerializer:
    serializer_class = LockSerializer

    @pytest.fixture(autouse=True)
    def setup_class(self):
        self.lock = baker.make(Lock)
        self.schedules = baker.make(LockSchedule, lock=self.lock, _quantity=2)

    def test_success(self):
        assert self.serializer_class(self.lock).data == {
            "id": self.lock.id,
            "latitude": self.lock.latitude,
            "longitude": self.lock.longitude,
            "radius": self.lock.radius,
            "status": self.lock.status,
            "tag": self.lock.tag.id,
            "modified": self.lock.modified.astimezone(
                timezone.get_current_timezone()
            ).isoformat(),
            "created": self.lock.created.astimezone(
                timezone.get_current_timezone()
            ).isoformat(),
            "schedules": [
                LockScheduleSerializer(schedule).data for schedule in self.schedules
            ],
        }
