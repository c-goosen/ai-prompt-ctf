from database.db import LeaderBoard, get_async_session, User
import contextlib
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import CursorResult
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from utils import return_hash
from app_config import settings

async def get_leaderboard_data():
    get_async_session_context = contextlib.asynccontextmanager(get_async_session)
    stmt = (
        select(LeaderBoard)
        .group_by("level", "last_update", "user_id")
        .order_by(LeaderBoard.level.desc())
        .order_by(LeaderBoard.last_update.asc())
    )
    async with get_async_session_context() as session:
        return [user for user in await session.scalars(stmt)]


async def leader_exists(session: AsyncSession, user_id: str):
    leader = await session.get(LeaderBoard, user_id)
    print(leader)
    # print(leader.user_id)
    return leader


async def update_leaderboard_user(user: User, level: int, password_hash: str) -> None:
    get_async_session_context = contextlib.asynccontextmanager(get_async_session)

    async with get_async_session_context() as session:
        # Check if leaderboard has user on it already
        leader = await leader_exists(session, user_id=user.id)
        if leader:
        # if leader.user_id:
            # Update existing Leaderboard item
            leader.level = level
            leader.password_hash = password_hash
            await session.commit()
        else:
            # Create new Item on LeaderBoard
            leader = LeaderBoard(
                user_id=user.id,
                email=user.email,
                level=level,
                password_hash=password_hash,
            )
            session.add(leader)
            await session.commit()
            await session.refresh(leader)
    return None

async def cookies_after_login(user: User) -> list:
    get_async_session_context = contextlib.asynccontextmanager(get_async_session)
    cookie_list = []
    async with get_async_session_context() as session:
        leader = await leader_exists(session, user_id=user.id)
        if leader:
            cookie_list.append({"level": f"ctf_level_{1}", "hash": return_hash(settings.PASSWORDS.get(1, " "))})
            for x in range(2, int(leader.level+1)):
                cookie_list.append({"level": f"ctf_level_{x}", "hash": return_hash(settings.PASSWORDS.get(x-1, ""))})
    return cookie_list




