import json
import logging
from dataclasses import dataclass, field
from itertools import accumulate
from typing import Union, List, Optional, Tuple

import numpy as np
from dataclasses_json import dataclass_json, LetterCase, config

from brevet_top_numpy_utils import FloatArray, np_geo_distance
from brevet_top_plot_a_route.check_point import CheckPoint
from brevet_top_plot_a_route.route_point import PlotARoutePoint, RoutePoint
from brevet_top_plot_a_route.utils import geo_distance, simplify_route, route_down_sample_factor

EPILOG_MAX_LENGTH = 500  # meters


@dataclass_json(letter_case=LetterCase.PASCAL)
@dataclass
class Route:
    route_id: int = field(metadata=config(field_name="RouteID"), default=-1)
    route_data: Union[str, List[PlotARoutePoint]] = ""
    route_name: str = ""
    distance: float = 0
    track: Optional[List[RoutePoint]] = None
    short_track: Optional[List[RoutePoint]] = None
    checkpoints: Optional[List[CheckPoint]] = None

    def __post_init__(self):
        if self.route_data and type(self.route_data) is str:
            self.route_data = [PlotARoutePoint(**p) for p in json.loads(self.route_data)]
        else:
            self.route_data = []

    def __repr__(self):
        return f"<Route name={self.route_name} distance={self.distance}>"

    def make_tracks(self):
        """
        Transform a route from Plot A Route format to internal one adding distance.
        Create a short (simplified) version too.
        """
        if len(self.route_data) == 0:
            return []
        first_point = RoutePoint.from_plot_a_route(self.route_data.pop(0), distance=0)

        self.track = list(accumulate(self.route_data, self._build_point, initial=first_point))
        if len(self.track) < 1:
            raise ValueError("Empty route")

        route = simplify_route(self.track)
        self.short_track = simplify_route(
            self.track, factor=route_down_sample_factor(len(self.track), len(route))
        )
        logging.info(
            f"The route has been simplified from {len(self.track)}"
            f" points to {len(route)} / {len(self.short_track)}"
        )

    @staticmethod
    def _build_point(route: RoutePoint, point: PlotARoutePoint) -> RoutePoint:
        try:
            distance = geo_distance(
                route.lat,
                route.lng,
                point.lat,
                point.lng,
            )
            return RoutePoint.from_plot_a_route(point, distance=route.distance + distance)
        except ValueError:
            # points are way too close, skip one
            return route

    def find_checkpoints(self):
        """
        Trace the route and find checkpoints.
        """
        if type(self.track) is not list or len(self.track) < 1:
            raise ValueError("Empty route")

        checkpoints: List[CheckPoint] = []

        first_point = CheckPoint.from_route_point(self.track.pop(0), name="Start")
        checkpoints.append(first_point)

        # search along other route points
        for point in self.track:
            if point.is_control():
                checkpoints.append(CheckPoint.from_route_point(point))

        labels: List[CheckPoint] = []
        # search for symlabs checkpoints
        labels.extend(label for label in first_point.find_labels() if label.is_control())
        self._attach_labels(labels, [(p.lat, p.lng, 0, p.distance) for p in self.track])

        checkpoints.extend(labels)
        self._add_last_checkpoint()
        return checkpoints

    @staticmethod
    def _attach_labels(labels: List[CheckPoint], points: List[Tuple[float, float, float, float]]):
        """
        Find best matching route points and update distance from the route start.

        :param labels: a list of CheckPoint
        :param points: a list of route points to compare
        """
        for label in labels:
            step_away: FloatArray = np_geo_distance(
                np.array([label.lat, label.lng, 0.0, 0.0], dtype=np.float64),
                np.array(points, dtype=np.float64),
            )
            offset: int = np.argmin(step_away)  # noqa: E711
            if not label.distance:
                label.distance = int(points[offset][3] / 1000)

    def _add_last_checkpoint(self):
        """
        Compare the route and checkpoint list and add a new CheckPoint if the route is longer.
        """
        if not self.track:
            return
        finish = self.track[-1]
        # add the last point from the route if too far from the last control
        if (
                self.checkpoints is not None
                and len(self.checkpoints) > 0
                and finish.distance > self.checkpoints[-1].distance + EPILOG_MAX_LENGTH
        ):
            checkpoint = CheckPoint.from_route_point(finish, name="End")
            self.checkpoints.append(checkpoint)
