from dataclasses import dataclass
from typing import Optional

from brevet_top_plot_a_route.route_point import RoutePoint


@dataclass
class CheckPoint(RoutePoint):
    name: str = None

    def __init__(self, **kwargs):
        name: str = kwargs.pop("name", "")
        super().__init__(**kwargs)
        self.name = name
        self.fix_name()

    @classmethod
    def from_route_point(cls, point: RoutePoint, name: str = ""):
        return cls(**point.__dict__, name=name)

    def __repr__(self):
        return (
            f"<CheckPoint lat={self.lat} lng={self.lng}"
            f" name='{self.name}' distance={self.distance}>"
        )

    def fix_name(self, replacement: Optional[str] = None) -> Optional[str]:
        """
        Copy the point description to the name property

        :param replacement: optional control name if not specified in the route
        :return: the name
        """
        self.name = (self.name or self.labtxt or self.dir or replacement or "").strip()
        return self.name

    def find_labels(self) -> list:
        """
        Find checkpoints defined in symlabs/lab/labtxt tags.

        :return: a list of new CheckPoints
        """
        return [
            CheckPoint(**label, labtxt=label.get("lab", {}).get("labtxt"))
            for label in self.symlabs
        ]
