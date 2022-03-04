import numpy as np

from strava.simplify import clear_stops

TRACK = np.array(
    [
        (60.0, 30.0, 1234567890.0, 0.0),
        (60.1, 30.1, 1234567891.0, 1000.0),
        (60.1001, 30.1001, 1234567892.0, 1001.0),
        (60.1002, 30.1002, 1234567893.0, 1002.0),
        (60.2, 30.2, 1234567894.0, 2000.0),
        (60.2001, 30.2001, 1234567895.0, 2001.0),
        (60.2002, 30.2002, 1234567896.0, 2002.0),
        (60.3, 30.3, 1234567897.0, 3000.0),
    ]
)


def test_clear_stops_empty():
    # setup
    checkpoints = []

    # action
    reduced = clear_stops(TRACK, checkpoints)

    # verification
    assert reduced.tolist() == TRACK.tolist()


def test_clear_stops_single():
    # setup
    checkpoints = [(60.1, 30.1, 0.0, 0.0)]
    expected = [
        [60.0, 30.0, 1234567890.0, 0.0],
        [60.2, 30.2, 1234567894.0, 2000.0],
        [60.2001, 30.2001, 1234567895.0, 2001.0],
        [60.2002, 30.2002, 1234567896.0, 2002.0],
        [60.3, 30.3, 1234567897.0, 3000.0],
    ]

    # action
    reduced = clear_stops(TRACK, checkpoints)

    # verification
    assert reduced.tolist() == expected


def test_clear_stops_double():
    # setup
    checkpoints = [
        (60.1, 30.1, 0.0, 0.0),
        (60.2, 30.2, 0.0, 0.0),
    ]
    expected = [
        [60.0, 30.0, 1234567890.0, 0.0],
        [60.3, 30.3, 1234567897.0, 3000.0],
    ]

    # action
    reduced = clear_stops(TRACK, checkpoints)

    # verification
    assert reduced.tolist() == expected
