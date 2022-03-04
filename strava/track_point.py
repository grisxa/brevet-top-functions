from datetime import datetime


class StravaTrackPoint:
    def __init__(
        self,
        lat: float = None,
        lng: float = None,
        distance: float = None,
        date: datetime = None,
    ):
        self.lat = lat
        self.lng = lng
        self.distance = distance
        self.date = date

    def __eq__(self, other: object):
        if not isinstance(other, StravaTrackPoint):
            return NotImplemented
        return (
            self.lat == other.lat
            and self.lng == other.lng
            and self.distance == other.distance
            and self.date == other.date
        )

    def __repr__(self):
        return (
            # f"{self.__class__} lat={self.lat} lng={self.lng}"
            f"SP lat={self.lat} lng={self.lng}"
            f" distance={self.distance} date={self.date}"
        )
