from database.db import LeaderBoard, get_async_session, User
import contextlib
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import CursorResult
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
async def get_leaderboard_data():
    get_async_session_context = contextlib.asynccontextmanager(get_async_session)
    stmt = select(LeaderBoard).group_by('level', 'last_update', 'user_id').order_by(
        LeaderBoard.level.desc()).order_by(
        LeaderBoard.last_update.asc())
    async with get_async_session_context() as session:
        return [user for user in await session.scalars(stmt)]

async def leader_exists(session: AsyncSession, user_id:str):
    leader = await session.get(LeaderBoard, user_id)
    print(leader)
    print(leader.user_id)
    return leader


async def update_leaderboard_user(user: User, level: int, password_hash: str)-> None:
    get_async_session_context = contextlib.asynccontextmanager(get_async_session)

    async with get_async_session_context() as session:
        # Check if leaderboard has user on it already
        leader = await leader_exists(session, user_id=user.id)
        if leader.user_id:
            # Update existing Leaderboard item
            leader.level = level
            await session.commit()
        else:
            # Create new Item on LeaderBoard
            leader = LeaderBoard(user_id=user.id,
                email=user.email,
                level=level,
                password_hash=password_hash)
            session.add(leader)
            await session.commit()
            await session.refresh(leader)
    return None

