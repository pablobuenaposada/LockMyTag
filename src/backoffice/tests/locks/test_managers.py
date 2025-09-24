import datetime

import pytest
from freezegun import freeze_time
from model_bakery import baker

from locations.models import Tag
from locks.models import Lock, LockSchedule


@pytest.mark.django_db
class TestLockManager:
    @pytest.mark.parametrize(
        "lock_status, schedule_args, is_lock_found",
        [
            (Lock.STATUS_ACTIVE, None, True),  # no schedule, always applicable
            (
                Lock.STATUS_ACTIVE,
                {
                    "day": 2,
                    "start_time": datetime.time(0, 0),
                    "end_time": datetime.time(0, 1),
                },
                True,
            ),  # schedule matches current time
            (
                Lock.STATUS_INACTIVE,
                {
                    "day": 2,
                    "start_time": datetime.time(0, 0),
                    "end_time": datetime.time(0, 1),
                },
                False,
            ),  # schedule matches current time but it's inactive
            (
                Lock.STATUS_ACTIVE,
                {
                    "day": 2,
                    "start_time": datetime.time(1, 0),
                    "end_time": datetime.time(2, 0),
                },
                False,
            ),  # schedule does not match current time
        ],
    )
    @freeze_time(
        "2024-12-31 22:00:00", tz_offset=1
    )  # 2025-01-01 00:00:00 in Europe/Madrid, weekday=2 (Wednesday)
    def test_success(self, lock_status, schedule_args, is_lock_found):
        tag = baker.make(Tag)
        lock = baker.make(Lock, tag=tag, status=lock_status)
        if schedule_args:
            LockSchedule.objects.create(lock=lock, **schedule_args)
        lock_found = Lock.objects.get_active_applicable_locks(tag)

        if is_lock_found:
            assert lock_found == lock
        else:
            assert lock_found is None
