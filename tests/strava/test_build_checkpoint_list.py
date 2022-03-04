import numpy as np

from strava.build import build_checkpoint_list

CHECK_POINTS = [
    {
        "coordinates": (60.0, 30.0, 0, 0),
        "distance": 0,
        "uid": "a12",
    },
    {
        "coordinates": (60.1, 30.1, 10, 0),
        "distance": 10,
        "uid": "b34",
    },
    {
        "coordinates": (60.2, 30.2, 20, 0),
        "distance": 20,
        "uid": "c56",
    },
]


def test_build_checkpoint_list_empty():
    # action
    points, ids = build_checkpoint_list([])

    # verification
    assert np.array_equal(points, [])
    assert ids == []


def test_build_checkpoint_list_single():
    # setup
    expected_points = [
        (60.0, 30.0, 0, 0),
    ]
    expected_ids = ["a12"]

    # action
    points, ids = build_checkpoint_list([CHECK_POINTS[0]])

    # verification
    assert np.array_equal(points, expected_points)
    assert ids == expected_ids


def test_build_checkpoint_list_pair():
    # setup
    expected_points = [(60.0, 30.0, 0, 0), (60.1, 30.1, 10000, 0)]
    expected_ids = ["a12", "b34"]

    # action
    points, ids = build_checkpoint_list(CHECK_POINTS[0:2])

    # verification
    assert np.array_equal(points, expected_points)
    assert ids == expected_ids


def test_build_checkpoint_list():
    # setup
    expected_points = [
        (60.0, 30.0, 0, 0),
        (60.1, 30.1, 10000, 0),
        (60.1, 30.1, 10000, 0),
        (60.2, 30.2, 20000, 0),
    ]
    expected_ids = ["a12", "b34", "b34", "c56"]
    # action
    points, ids = build_checkpoint_list(CHECK_POINTS)

    # verification
    assert np.array_equal(points, expected_points)
    assert ids == expected_ids
