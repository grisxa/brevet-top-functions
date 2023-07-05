from typing import Optional


class PlotARoutePoint:
    def __init__(self):
        self.lat: float = 0
        self.lng: float = 0
        self.dir: Optional[str] = None
        self.labtxt: Optional[str] = None

    def __repr__(self):
        return f"<PlotARoutePoint lat={self.lat} lng={self.lng}>"


class RoutePoint(PlotARoutePoint):
    def __init__(self, **kwargs):
        super().__init__()

        self.distance: float = 0

        for key in kwargs.keys():
            self.__setattr__(key, kwargs[key])

    def __eq__(self, other: object):
        if not isinstance(other, RoutePoint):
            return NotImplemented
        return (
            self.lat == other.lat
            and self.lng == other.lng
            and self.distance == other.distance
        )

    def is_control(self) -> bool:
        """
        Decide if the route point is a control - by the name prefix

        :return: True or False
        """
        direction: str = self.dir or ""
        label: str = self.labtxt or ""
        return (
            direction.startswith("КП")
            or direction.startswith("CP")
            or label.startswith("КП")
            or label.startswith("CP")
        )

    def __repr__(self):
        return f"<RoutePoint lat={self.lat} lng={self.lng} distance={self.distance}>"
