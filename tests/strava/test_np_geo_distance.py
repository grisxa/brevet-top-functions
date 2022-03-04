import numpy as np

from strava.math import np_geo_distance


def test_np_geo_distance():
    track = np.array(
        [
            (50, 20, 0, 0),
            (60, 20, 0, 0),
            (60, 20, 0, 150),
            (60, 20, 0, 1150),
            (60, 30, 0, 200),
            (0, 0, 0, 0),
        ]
    )
    point = (60, 20, 0, 150)
    expected = [1111949.416, 0.15, 0.0, 1.0, 555445.183, 6891381.266]

    distance = np_geo_distance(point, track)

    assert np.around(distance, 3).tolist() == expected
