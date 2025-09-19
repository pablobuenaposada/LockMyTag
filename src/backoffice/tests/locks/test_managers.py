from datetime import time

import pytest
from freezegun import freeze_time
from model_bakery import baker

from locations.models import Tag
from locks.models import Lock


@pytest.mark.django_db
class TestLockManager:
    @pytest.mark.parametrize(
        "lock_args, is_lock_found",
        [
            ({}, True),  # no schedule, always applicable
            (
                {
                    "schedule_day": 2,
                    "schedule_start_time": time(0, 0),
                    "schedule_end_time": time(0, 1),
                },
                True,
            ),  # schedule matches current time
            (
                {
                    "status": Lock.STATUS_INACTIVE,
                    "schedule_day": 2,
                    "schedule_start_time": time(0, 0),
                    "schedule_end_time": time(0, 1),
                },
                False,
            ),  # schedule matches current time but it's inactive
            (
                {
                    "schedule_day": 2,
                    "schedule_start_time": time(1, 0),
                    "schedule_end_time": time(2, 0),
                },
                False,
            ),  # schedule does not match current time
        ],
    )
    @freeze_time(
        "2024-12-31 22:00:00", tz_offset=1
    )  # 2025-01-01 00:00:00 in Europe/Madrid
    def test_success(self, lock_args, is_lock_found):
        tag = baker.make(Tag)
        lock = baker.make(Lock, tag=tag, **lock_args)
        lock_found = Lock.objects.get_active_applicable_locks(tag)

        if is_lock_found:
            assert lock_found == lock
        else:
            assert lock_found is None
