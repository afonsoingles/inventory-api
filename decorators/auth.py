from functools import wraps
from fastapi import Request, HTTPException
import jwt
import os
from errors.user import InvalidOrExpiredTokenError, UserSuspendedError, UnsufficientPermissionsError
from tools.sessions import SessionTools
from tools.users import UserTools

def require_auth(func=None, *, permissions=[], require_admin=False):
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            session_tools = SessionTools()
            user_tools = UserTools()
            jwt_secret = os.environ.get("JWT_SECRET")

            request = kwargs.get("request", Request)
            if request is None:
                for a in args:
                    if isinstance(a, Request):
                        request = a
                        break

            auth_token = None
            if request is not None:
                auth_token = request.headers.get("Authorization", None)

            if auth_token is None or not auth_token.startswith("Bearer "):
                raise InvalidOrExpiredTokenError

            auth_token = auth_token.split(" ")[1]

            try:
                payload = jwt.decode(auth_token, jwt_secret, algorithms=["HS256"])
            except:
                raise InvalidOrExpiredTokenError

            if not session_tools.is_valid_session(auth_token):
                raise InvalidOrExpiredTokenError

            
            user = user_tools.get_user_by_id(payload["sub"])

            

            if not user.active:
                raise UserSuspendedError
            
            if not user.admin and require_admin:
                raise UnsufficientPermissionsError
            
            

            request.state.user = user
            request.state.token = auth_token

            return await fn(*args, **kwargs)
        return wrapper

    if callable(func):
        return decorator(func)
    return decorator