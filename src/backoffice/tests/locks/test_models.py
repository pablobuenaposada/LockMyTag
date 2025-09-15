from datetime import time
from unittest.mock import ANY

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from faker import Faker
from model_bakery import baker

from locations.models import Tag
from locks.models import Lock


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
            "schedule_day": None,
            "schedule_start_time": None,
            "schedule_end_time": None,
        }
        lock = Lock.objects.create(
            tag=tag,
            latitude=self.latitude,
            longitude=self.longitude,
            radius=self.radius,
        )

        for field in [field.name for field in Lock._meta.get_fields()]:
            assert getattr(lock, field) == expected[field]

    @pytest.mark.parametrize(
        "fields, error",
        [
            (
                {},
                {
                    "tag": ["This field cannot be null."],
                    "latitude": ["This field cannot be null."],
                    "longitude": ["This field cannot be null."],
                    "radius": ["This field cannot be null."],
                },
            ),
            (
                {
                    "tag": "foo",
                    "latitude": 1,
                    "longitude": 1,
                    "radius": 1,
                    "schedule_day": 1,
                },
                {
                    "__all__": [
                        "All schedule fields (day, start time, end time) must be filled if any of them is set"
                    ]
                },
            ),
            (
                {
                    "tag": "foo",
                    "latitude": 1,
                    "longitude": 1,
                    "radius": 1,
                    "schedule_start_time": time(12, 0),
                },
                {
                    "__all__": [
                        "All schedule fields (day, start time, end time) must be filled if any of them is set"
                    ]
                },
            ),
            (
                {
                    "tag": "foo",
                    "latitude": 1,
                    "longitude": 1,
                    "radius": 1,
                    "schedule_end_time": time(12, 0),
                },
                {
                    "__all__": [
                        "All schedule fields (day, start time, end time) must be filled if any of them is set"
                    ]
                },
            ),
        ],
    )
    def test_mandatory_fields(self, fields, error):
        if "tag" in fields:
            fields["tag"] = baker.make(Tag)
        with pytest.raises(ValidationError) as e:
            Lock.objects.create(**fields)

        assert str(e.value) == str(error)

    @pytest.mark.parametrize(
        "fields",
        [
            {"schedule_day": 0, "schedule_start_time": None, "schedule_end_time": None},
            {
                "schedule_day": None,
                "schedule_start_time": timezone.now().time(),
                "schedule_end_time": None,
            },
            {
                "schedule_day": None,
                "schedule_start_time": None,
                "schedule_end_time": timezone.now().time(),
            },
            {
                "schedule_day": 0,
                "schedule_start_time": timezone.now().time(),
                "schedule_end_time": None,
            },
            {
                "schedule_day": 0,
                "schedule_start_time": None,
                "schedule_end_time": timezone.now().time(),
            },
            {
                "schedule_day": None,
                "schedule_start_time": timezone.now().time(),
                "schedule_end_time": timezone.now().time(),
            },
        ],
    )
    def test_schedule_fields_validation(self, fields):
        fields.update(
            {
                "tag": baker.make(Tag),
                "latitude": self.latitude,
                "longitude": self.longitude,
                "radius": self.radius,
            }
        )
        with pytest.raises(ValidationError) as exc:
            Lock.objects.create(**fields)
        assert (
            "All schedule fields (day, start time, end time) must be filled if any of them is set"
            in str(exc.value)
        )

    @pytest.mark.parametrize(
        "first_schedule, second_schedule, should_overlap",
        [
            # complete overlap - second lock inside first lock
            (
                {"start": time(10, 0), "end": time(14, 0)},
                {"start": time(11, 0), "end": time(13, 0)},
                True,
            ),
            # partial overlap - second lock starts before first ends
            (
                {"start": time(10, 0), "end": time(14, 0)},
                {"start": time(13, 0), "end": time(15, 0)},
                True,
            ),
            # partial overlap - second lock ends after first starts
            (
                {"start": time(10, 0), "end": time(14, 0)},
                {"start": time(9, 0), "end": time(11, 0)},
                True,
            ),
            # no overlap - second lock after first
            (
                {"start": time(10, 0), "end": time(12, 0)},
                {"start": time(12, 0), "end": time(14, 0)},
                False,
            ),
            # no overlap - second lock before first
            (
                {"start": time(12, 0), "end": time(14, 0)},
                {"start": time(9, 0), "end": time(12, 0)},
                False,
            ),
        ],
    )
    def test_schedule_overlap(self, first_schedule, second_schedule, should_overlap):
        tag = baker.make(Tag)
        day = 0  # Monday

        # create first lock
        Lock.objects.create(
            tag=tag,
            latitude=self.latitude,
            longitude=self.longitude,
            radius=self.radius,
            schedule_day=day,
            schedule_start_time=first_schedule["start"],
            schedule_end_time=first_schedule["end"],
        )

        # try to create second lock
        second_lock_data = {
            "tag": tag,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "radius": self.radius,
            "schedule_day": day,
            "schedule_start_time": second_schedule["start"],
            "schedule_end_time": second_schedule["end"],
        }

        if should_overlap:
            with pytest.raises(ValidationError) as exc:
                Lock.objects.create(**second_lock_data)
            assert "overlap" in str(exc.value).lower()
        else:
            # should create without error
            Lock.objects.create(**second_lock_data)
