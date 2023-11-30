import uuid
from typing import Optional
from starlette.responses import RedirectResponse
from fastapi import Response, status
from fastapi import Depends, Request, Response
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase

from database.db import User, get_user_db

from fastapi_users.authentication import CookieTransport
from app_config import settings
import logging

SECRET = settings.APP_SECRET

logger = logging.getLogger(__name__)


class RedirectCookieAuthentication(CookieTransport):
    async def get_login_response(self, token: str) -> Response:
        await super().get_login_response(token)
        response = RedirectResponse(url="/level/0", status_code=303)
        response.status_code = 303
        response.headers["Location"] = "/level/0"
        return self._set_login_cookie(response, token)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(
        self,
        user: User,
        request: Optional[Request] = None,
        response: Optional[Response] = None,
    ):
        logger.info(f"User {user.id} has registered.")
        return RedirectResponse(url="/login", status_code=303)

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


# bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")
cookie_transport = RedirectCookieAuthentication(
    cookie_max_age=settings.COOKIE_TIMEOUT, cookie_domain=settings.COOKIE_DOMAIN
)


class RedirectCookieAuthentication(CookieTransport):
    async def get_login_response(self, token: str) -> Response:
        await super().get_login_response(self, token)
        response = RedirectResponse(
            status_code=status.HTTP_303_SEE_OTHER, url="/level/0"
        )
        response = self._set_login_cookie(response, token)
        # response.set_cookie()
        return response

    async def get_logout_response(self) -> Response:
        await super().get_logout_response(self)
        response = RedirectResponse(status_code=status.HTTP_204_NO_CONTENT, url="/")
        return self._set_logout_cookie(response)


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=settings.COOKIE_TIMEOUT)


auth_backend = AuthenticationBackend(
    name="cookie_jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
current_active_user_opt = fastapi_users.current_user(optional=True, active=True)
