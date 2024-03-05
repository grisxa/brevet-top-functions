import pathlib
from datetime import datetime
from typing import Tuple, List, Iterable

import gpxpy
import pytest
from brevet_top_plot_a_route import RoutePoint


def pytest_assertrepr_compare(op, left, right):
    if isinstance(left, datetime) and isinstance(right, datetime) and op == "<=":
        return [
            "Datetime comparison has failed:",
            f"    {left.isoformat()} <= {right.isoformat()}",
        ]
