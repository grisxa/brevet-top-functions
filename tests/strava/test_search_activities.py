from unittest.mock import MagicMock

import pytest
from flask import Request

from main import search_activities


@pytest.fixture
def mock_brevet() -> dict:
    return {"uid": "bGJa6nII0SDo521Imv6M", "startDate": "", "endDate": "", "track": ""}


@pytest.fixture
def mock_user() -> dict:
    return {"uid": "78HM3eyMTqhEelqc7gBP5Sv4pPG2"}


@pytest.fixture
def mock_request() -> Request:
    return Request({})


def x_test_search_activities(mock_request):
    # setup
    mock_request.get_json = MagicMock(
        return_value={
            "data": {
                "brevetUid": "bGJa6nII0SDo521Imv6M",
                "userId": "78HM3eyMTqhEelqc7gBP5Sv4pPG2",
            }
        }
    )
    # action
    result = search_activities(mock_request)
    # verification
    assert result == (
        '{"data": {"result": "OK"}}',
        200,
        {"Access-Control-Allow-Origin": "*"},
    )
    # assert False
