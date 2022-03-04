class StravaTokens:
    def __init__(self, **kwargs):
        access_token: str
        # the only field to copy from the athlete's profile
        athlete_id: int
        expires_at: int
        expires_in: int
        refresh_token: str
        token_type: str

        for key in kwargs.keys():
            self.__setattr__(key, kwargs[key])
