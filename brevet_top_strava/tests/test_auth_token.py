from datetime import datetime, timezone

import pytest

from brevet_top_strava.api import auth_token, tokens_expired


@pytest.mark.parametrize(
    ("strava", "token"),
    [
        ({}, "Bearer none"),
        ({"token_type": "any"}, "any none"),
        ({"access_token": "secret"}, "Bearer secret"),
        ({"token_type": "Bearer", "access_token": "secret"}, "Bearer secret"),
    ],
)
def test_auth_token(strava: dict, token: str):
    assert auth_token(strava) == token


@pytest.mark.parametrize(
    ("date", "tokens", "expected"),
    [
        (datetime(2022, 1, 2, 3, 4, 5, tzinfo=timezone.utc), {}, True),
        (
            datetime(2022, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
            {"expires_at": 1641092644},
            True,
        ),
        (
            datetime(2022, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
            {"expires_at": 1641092645},
            True,
        ),
        (
            datetime(2022, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
            {"expires_at": 1641092646},
            False,
        ),
    ],
)
def test_tokens_expired(date: datetime, tokens: dict, expected: bool):
    assert tokens_expired(date, tokens) == expected
