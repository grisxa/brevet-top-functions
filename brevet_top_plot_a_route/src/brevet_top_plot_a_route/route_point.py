from dataclasses import dataclass, field, fields, MISSING
from typing import Optional, List


@dataclass
class PlotARoutePoint:
    lat: float = 0
    lng: float = 0
    dir: Optional[str] = ""
    labtxt: Optional[str] = ""
    symlabs: List[dict] = field(default_factory=list)

    def __init__(self, **kwargs):
        # Initialize attributes with default factories, if any
        for _field in fields(self.__class__):
            if _field.default_factory is not MISSING:
                setattr(self, _field.name, _field.default_factory())

        # Keep known attributes only
        names = set([_field.name for _field in fields(self.__class__)])
        for key, value in kwargs.items():
            if key in names:
                setattr(self, key, value)

    def __repr__(self):
        return f"<PlotARoutePoint lat={self.lat} lng={self.lng}>"


@dataclass
class RoutePoint(PlotARoutePoint):
    distance: float = 0

    def __init__(self, **kwargs):
        distance: float = kwargs.pop("distance", 0)
        super().__init__(**kwargs)
        self.distance = distance

    @classmethod
    def from_plot_a_route(cls, point: PlotARoutePoint, distance: float = 0):
        return cls(**point.__dict__, distance=distance)

    def __eq__(self, other: object):
        if not isinstance(other, self.__class__):
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
