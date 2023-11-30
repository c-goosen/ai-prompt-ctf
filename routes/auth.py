from fastapi import APIRouter
import contextlib
from database.users import (
    auth_backend,
    fastapi_users,
)
from fastapi import FastAPI, Form, Request, Depends
from starlette.responses import RedirectResponse
from typing import Annotated

from fastapi.templating import Jinja2Templates

from database.db import (
    User,
    get_async_session,
    get_user_db,
)
from database.users import (
    current_active_user_opt,
)
import logging
from database.schemas import UserCreate, UserRead
from app_config import settings

app = APIRouter()
templates = Jinja2Templates(directory="templates")

get_async_session_context = contextlib.asynccontextmanager(get_async_session)


app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)


@app.get("/signup")
async def signup(request: Request, user: User = Depends(current_active_user_opt)):
    if user:
        return RedirectResponse("/level/0")
    return templates.TemplateResponse(
        "signup.html",
        {
            "request": request,
        },
    )


@app.get("/logout")
async def login(request: Request):
    response = RedirectResponse(url="/login")
    response.delete_cookie("fastapiusersauth", domain=settings.COOKIE_DOMAIN)
    return response
@app.get("/login")
async def login(request: Request, user: User = Depends(current_active_user_opt)):
    if user is not None:
        response = RedirectResponse(url="/level/0")
        return response
    response = templates.TemplateResponse(
        "login.html",
        {
            "request": request,
        },
    )

    return response


@app.post("/auth/signup")
async def signup(
    request: Request, email: Annotated[str, Form()], password: Annotated[str, Form()]
):
    from database.schemas import UserCreate
    from database.users import get_user_manager
    from fastapi_users.exceptions import UserAlreadyExists

    get_user_db_context = contextlib.asynccontextmanager(get_user_db)
    get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)
    try:
        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    user = await user_manager.create(
                        UserCreate(email=email, password=password, is_superuser=False)
                    )
                    logging.info(f"User created {user}")
                    return RedirectResponse(url="/login", status_code=303)
    except UserAlreadyExists:
        logging.info(f"User {email} already exists")
        return RedirectResponse(url="/signup", status_code=303)
