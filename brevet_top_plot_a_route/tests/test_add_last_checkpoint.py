from brevet_top_plot_a_route import add_last_checkpoint, RoutePoint, CheckPoint


def test_add_last_checkpoint_empty():
    checkpoints = []

    add_last_checkpoint(checkpoints)

    assert checkpoints == []


def test_add_last_checkpoint_single_near():
    checkpoints = [CheckPoint(lat=60, lng=30, distance=0)]

    add_last_checkpoint(checkpoints)

    assert len(checkpoints) == 1


def test_add_last_checkpoint_single_far():
    checkpoints = [CheckPoint(lat=60, lng=30, distance=0)]
    expected = [
        CheckPoint(lat=60, lng=30, distance=0),
        CheckPoint(lat=61, lng=31, distance=2, name="End"),
    ]

    add_last_checkpoint(checkpoints, RoutePoint(lat=61, lng=31, distance=2000))

    assert checkpoints == expected


def test_add_last_checkpoint_many_near():
    checkpoints = [
        CheckPoint(lat=60.1, lng=30.1, distance=0),
        CheckPoint(lat=60.3, lng=30.3, distance=100),
        CheckPoint(lat=60.2, lng=30.2, distance=200),
    ]
    expected = [
        CheckPoint(lat=60.1, lng=30.1, distance=0),
        CheckPoint(lat=60.3, lng=30.3, distance=100),
        CheckPoint(lat=60.2, lng=30.2, distance=200),
    ]

    add_last_checkpoint(checkpoints, RoutePoint(lat=60.4, lng=30.4, distance=200.5))

    assert checkpoints == expected


def test_add_last_checkpoint_many_far():
    checkpoints = [
        CheckPoint(lat=60.1, lng=30.1, distance=0),
        CheckPoint(lat=60.3, lng=30.3, distance=100),
        CheckPoint(lat=60.2, lng=30.2, distance=200),
    ]
    expected = [
        CheckPoint(lat=60.1, lng=30.1, distance=0),
        CheckPoint(lat=60.3, lng=30.3, distance=100),
        CheckPoint(lat=60.2, lng=30.2, distance=200),
        CheckPoint(lat=60.4, lng=30.4, distance=201, name="End"),
    ]

    add_last_checkpoint(checkpoints, RoutePoint(lat=60.4, lng=30.4, distance=201000))

    assert checkpoints == expected
