import pytest

from plot_a_route import attach_labels
from plot_a_route.check_point import CheckPoint


@pytest.fixture()
def labels():
    return [
        CheckPoint(lat=60.0164, lng=30.278, name="CP1"),
        CheckPoint(lat=60.0229, lng=30.282, name="CP2"),
    ]


def test_attach_labels_empty():
    labels = []
    expected = []

    attach_labels(labels, [(60.016743, 30.26922, 0.0, 0.0)])
    assert labels == expected


def test_attach_labels(labels):
    # action
    attach_labels(
        labels,
        [
            (60.016743, 30.26922, 0.0, 1234.56),
            (60.0169, 30.279, 0.0, 3456.78),
            (60.0226, 30.284, 0.0, 5678.9),
        ],
    )

    # verification
    assert [label.distance for label in labels] == [3, 6]
