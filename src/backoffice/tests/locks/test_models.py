import datetime
from unittest.mock import ANY

import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from faker import Faker
from model_bakery import baker

from locations.models import Tag
from locks.models import Lock, LockSchedule


@pytest.mark.django_db
class TestLock:
    fake = Faker()
    latitude = float(round(fake.latitude(), 6))
    longitude = float(round(fake.longitude(), 6))
    radius = fake.pyint()

    def test_success(self):
        tag = baker.make(Tag)
        expected = {
            "id": ANY,
            "created": ANY,
            "modified": ANY,
            "tag": tag,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "radius": self.radius,
            "status": Lock.STATUS_ACTIVE,
            "last_notified": None,
        }
        lock = Lock.objects.create(
            tag=tag,
            latitude=self.latitude,
            longitude=self.longitude,
            radius=self.radius,
        )

        for field in [
            field.name
            for field in Lock._meta.get_fields()
            if field.name not in ["schedules"]
        ]:
            assert getattr(lock, field) == expected[field]

    @pytest.mark.parametrize(
        "fields, error",
        [
            ({}, 'null value in column "latitude"'),
            ({"latitude": 1}, 'null value in column "longitude"'),
            ({"longitude": 1}, 'null value in column "latitude"'),
            ({"latitude": 1, "longitude": 1}, 'null value in column "radius"'),
            (
                {"latitude": 1, "longitude": 1, "radius": 1},
                'null value in column "tag_id"',
            ),
        ],
    )
    def test_mandatory_fields(self, fields, error):
        with pytest.raises(IntegrityError) as e:
            Lock.objects.create(**fields)

        assert error in str(e.value)


@pytest.mark.django_db
class TestLockSchedule:
    def test_success(self):
        lock = baker.make(Lock)
        day = 0
        start_time = datetime.time(0, 0, 0)
        end_time = datetime.time(23, 59, 59)
        expected = {
            "id": ANY,
            "created": ANY,
            "modified": ANY,
            "lock": lock,
            "day": day,
            "start_time": start_time,
            "end_time": end_time,
        }
        schedule = LockSchedule.objects.create(
            lock=lock,
            day=day,
            start_time=start_time,
            end_time=end_time,
        )

        for field in [field.name for field in LockSchedule._meta.get_fields()]:
            assert getattr(schedule, field) == expected[field]

    def test_mandatory_fields(self):
        with pytest.raises(ValidationError) as e:
            LockSchedule.objects.create()

        assert str(
            {
                "lock": ["This field cannot be null."],
                "day": ["This field cannot be null."],
                "start_time": ["This field cannot be null."],
                "end_time": ["This field cannot be null."],
            }
        ) in str(e.value)

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "first_schedule, second_schedule, should_overlap",
        [
            # complete overlap - second schedule inside first schedule
            (
                {"start": datetime.time(10, 0), "end": datetime.time(14, 0)},
                {"start": datetime.time(11, 0), "end": datetime.time(13, 0)},
                True,
            ),
            # partial overlap - second schedule starts before first ends
            (
                {"start": datetime.time(10, 0), "end": datetime.time(14, 0)},
                {"start": datetime.time(13, 0), "end": datetime.time(15, 0)},
                True,
            ),
            # partial overlap - second schedule ends after first starts
            (
                {"start": datetime.time(10, 0), "end": datetime.time(14, 0)},
                {"start": datetime.time(9, 0), "end": datetime.time(11, 0)},
                True,
            ),
            # no overlap - second schedule after first
            (
                {"start": datetime.time(10, 0), "end": datetime.time(12, 0)},
                {"start": datetime.time(12, 0), "end": datetime.time(14, 0)},
                False,
            ),
            # no overlap - second schedule before first
            (
                {"start": datetime.time(12, 0), "end": datetime.time(14, 0)},
                {"start": datetime.time(9, 0), "end": datetime.time(12, 0)},
                False,
            ),
        ],
    )
    def test_overlap(self, first_schedule, second_schedule, should_overlap):
        lock = baker.make(Lock)
        day = 0  # Monday
        LockSchedule.objects.create(
            lock=lock,
            day=day,
            start_time=first_schedule["start"],
            end_time=first_schedule["end"],
        )
        if should_overlap:
            with pytest.raises(ValidationError) as exc:
                LockSchedule.objects.create(
                    lock=lock,
                    day=day,
                    start_time=second_schedule["start"],
                    end_time=second_schedule["end"],
                )
            assert "overlap" in str(exc.value).lower()
        else:
            LockSchedule.objects.create(
                lock=lock,
                day=day,
                start_time=second_schedule["start"],
                end_time=second_schedule["end"],
            )
