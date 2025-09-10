import pytest

from locks.utils import is_within_radius


class TestIsWithinRadius:
    @pytest.mark.parametrize(
        "lat1, lon1, lat2, lon2, radius, expected",
        [
            (0, 0, 0, 0, 100, True),  # same point
            (0, 0, 0.0009, 0, 100, True),  # within radius
            (0, 0, 0.001, 0, 100, False),  # outside radius
            (
                51.5074,
                -0.1278,
                51.5075,
                -0.1279,
                15,
                True,
            ),  # London points within radius
            (
                51.5074,
                -0.1278,
                51.5075,
                -0.1279,
                13,
                False,
            ),  # London points outside radius
        ],
    )
    def test_success(self, lat1, lon1, lat2, lon2, radius, expected):
        assert is_within_radius(lat1, lon1, lat2, lon2, radius) == expected
