from typing import Optional

from .route_point import RoutePoint


class CheckPoint(RoutePoint):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.name: Optional[str] = None

        for key in kwargs.keys():
            self.__setattr__(key, kwargs[key])

        self.fix_name()

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
        self.name = (self.name or self.dir or self.labtxt or replacement or "").strip()
        return self.name
