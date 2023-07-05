from datetime import datetime

from brevet_top_strava.track_point import StravaTrackPoint


class PointTestClass:
    def __init__(self, *args):
        self.args = args

    def __repr__(self):
        """Use the same signature as of the target class"""
        return (
            f"SP lat={self.args[0]} lng={self.args[1]}"
            f" distance={self.args[2]} date={self.args[3]}"
        )

    def __eq__(self, other):
        return repr(self) == repr(other)


def test_compare_equal():
    # setup
    a = StravaTrackPoint(60, 30, 100, None)
    b = StravaTrackPoint(60, 30, 100, None)

    # verification
    assert a == b


def test_compare_latitude_fail():
    # setup
    a = StravaTrackPoint(60, 30, 100, None)
    b = StravaTrackPoint(70, 30, 100, None)

    # verification
    assert a != b


def test_compare_longitude_fail():
    # setup
    a = StravaTrackPoint(60, 30, 100, None)
    b = StravaTrackPoint(60, 40, 100, None)

    # verification
    assert a != b


def test_compare_distance_fail():
    # setup
    a = StravaTrackPoint(60, 30, 0, None)
    b = StravaTrackPoint(60, 30, 100, None)

    # verification
    assert a != b


def test_compare_date_fail():
    # setup
    a = StravaTrackPoint(60, 30, 100, datetime(2021, 12, 13, 14, 15, 16))
    b = StravaTrackPoint(60, 30, 100, datetime(2021, 11, 12, 13, 14, 15))

    # verification
    assert a != b


def test_compare_convert_fail():
    # setup
    a = StravaTrackPoint(60, 30, 0, None)

    # verification
    assert a != "any"


def test_compare_convert_ok():
    # setup
    a = StravaTrackPoint(60, 30, 100, datetime(2021, 12, 13, 14, 15, 16))
    b = PointTestClass(60, 30, 100, "2021-12-13 14:15:16")

    # verification
    assert a == b


def test_repr():
    # setup
    a = StravaTrackPoint(60, 30, 100, datetime(2021, 12, 13, 14, 15, 16))

    # verification
    assert repr(a) == "SP lat=60 lng=30 distance=100 date=2021-12-13 14:15:16"
