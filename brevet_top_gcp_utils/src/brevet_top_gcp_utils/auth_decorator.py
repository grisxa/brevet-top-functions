from functools import wraps

from firebase_admin import auth


def authenticated(func):
    @wraps(func)
    def wrapped(request):
        try:
            # Validate the firebase token in the HTTP header
            token = auth.verify_id_token(
                request.headers["Authorization"].replace("Bearer ", "")
            )
        except Exception as e:
            return f"Invalid Credentials: {e}", 401
        # Pass the token contents to the underlying function
        return func(request, token)

    return wrapped
