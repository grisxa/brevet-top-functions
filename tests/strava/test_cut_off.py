import numpy as np

from strava import cut_off_prolog, cut_off_epilog


def test_cut_off_prolog_empty():
    # setup
    track = np.empty(shape=(0, 4), dtype=float)
    start = (60.0, 30.0, 1234567890.0, 0.0)

    # action
    a = cut_off_prolog(track, start)
    b = cut_off_prolog(track, None)

    # verification
    assert a.tolist() == []
    assert b.tolist() == []


def test_cut_off_prolog_single():
    # setup
    start = (60.0, 30.0, 1234567890.0, 0.0)
    track = np.array([start], dtype=float)
    expected = [[60.0, 30.0, 1234567890.0, 0.0]]

    # action
    a = cut_off_prolog(track, start)
    b = cut_off_prolog(track, None)

    # verification
    assert a.tolist() == expected
    assert b.tolist() == expected


def test_cut_off_prolog_double():
    # setup
    start = (60.1, 30.1, 1234567890.1, 0.0)
    track = np.array([(60.0, 30.0, 1234567890.0, 0.0), start], dtype=float)
    expected = [[60.1, 30.1, 1234567890.1, 0.0]]

    # action
    a = cut_off_prolog(track, start)

    # verification
    assert a.tolist() == expected


def test_cut_off_prolog_keep():
    # setup
    start = (60.1, 30.1, 1234567890.0, 0.0)
    track = np.array(
        [
            start,
            (60.2, 30.2, 1234567890.2, 100.0),
            (60.3, 30.3, 1234567890.3, 200.0),
        ],
        dtype=float,
    )
    expected = [
        [60.1, 30.1, 1234567890.0, 0.0],
        [60.2, 30.2, 1234567890.2, 100.0],
        [60.3, 30.3, 1234567890.3, 200.0],
    ]

    # action
    a = cut_off_prolog(track, start)

    # verification
    assert a.tolist() == expected


def test_cut_off_epilog_empty():
    # setup
    track = np.empty(shape=(0, 4), dtype=float)
    end = (60.0, 30.0, 1234567890.0, 0.0)

    # action
    a = cut_off_epilog(track, end)
    b = cut_off_epilog(track, None)

    # verification
    assert a.tolist() == []
    assert b.tolist() == []


def test_cut_off_epilog_single():
    # setup
    end = (60.0, 30.0, 1234567890.0, 0.0)
    track = np.array([end], dtype=float)
    expected = [[60.0, 30.0, 1234567890.0, 0.0]]

    # action
    a = cut_off_epilog(track, end)
    b = cut_off_epilog(track, None)

    # verification
    assert a.tolist() == expected
    assert b.tolist() == expected


def test_cut_off_epilog_double():
    # setup
    end = (60.1, 30.1, 1234567890.1, 0.0)
    track = np.array([end, (60.0, 30.0, 1234567890.0, 0.0)], dtype=float)
    expected = [[60.1, 30.1, 1234567890.1, 0.0]]

    # action
    a = cut_off_epilog(track, end)

    # verification
    assert a.tolist() == expected


def test_cut_off_epilog_keep():
    # setup
    end = (60.1, 30.1, 1234567890.0, 0.0)
    track = np.array(
        [
            (60.2, 30.2, 1234567890.2, 100.0),
            (60.3, 30.3, 1234567890.3, 200.0),
            end,
        ],
        dtype=float,
    )
    expected = [
        [60.2, 30.2, 1234567890.2, 100.0],
        [60.3, 30.3, 1234567890.3, 200.0],
        [60.1, 30.1, 1234567890.0, 0.0],
    ]

    # action
    a = cut_off_epilog(track, end)

    # verification
    assert a.tolist() == expected
