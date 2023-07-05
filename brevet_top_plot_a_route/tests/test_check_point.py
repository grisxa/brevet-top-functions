from brevet_top_plot_a_route.check_point import CheckPoint


def test_check_point():
    # setup
    a = CheckPoint()
    b = CheckPoint(lat=60, lng=30, distance=100)
    c = CheckPoint(lat=60, lng=30, distance=100, labtxt="start")

    # verification
    assert str(a) == "<CheckPoint lat=0 lng=0 name='' distance=0>"
    assert str(b) == "<CheckPoint lat=60 lng=30 name='' distance=100>"
    assert str(c) == "<CheckPoint lat=60 lng=30 name='start' distance=100>"


def test_check_point_fix_name():
    # setup
    a = CheckPoint(lat=60, lng=30, distance=100, name="CP1")
    b = CheckPoint(lat=60, lng=30, distance=100, dir="right")
    c = CheckPoint(lat=60, lng=30, distance=100, labtxt="start")
    d = CheckPoint(lat=60, lng=30, distance=100)

    # action
    d.fix_name(" CP2 ")

    # verification
    assert a.name == "CP1"
    assert b.name == "right"
    assert c.name == "start"
    # no leading/trailing spaces
    assert d.name == "CP2"
