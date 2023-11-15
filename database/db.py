from typing import AsyncGenerator
from sqlalchemy import PrimaryKeyConstraint
from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app_config import settings
from sqlalchemy import Column, ForeignKey, Integer, DateTime, UnicodeText, String
import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID

UUID_ID = uuid.UUID

DATABASE_URL = settings.SUPABASE_PG_URI_ASYNC


class Base(DeclarativeBase):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    pass


class LeaderBoard(Base):
    __tablename__ = "leaderboard"
    __table_args__ = (
        PrimaryKeyConstraint("user_id", name="pk_leaderboard"),

    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), default=uuid.uuid4, unique=True, primary_key=True, index=True)
    level = Column(Integer, index=True)
    last_update = Column(DateTime, index=True, default=datetime.datetime.utcnow())
    email = Column(String, ForeignKey("user.email"), index=True)
    password_hash = Column(UnicodeText, index=True)



class UserPrompts(Base):
    __tablename__ = "user_prompts"


    id = Column(Integer, primary_key=True, index=True)
    level = Column(Integer, index=True)
    last_update = Column(DateTime, index=True, default=datetime.datetime.utcnow())
    user = Column(UUID(as_uuid=True), ForeignKey("user.id"), default=uuid.uuid4)
    prompt = Column(UnicodeText, index=True)
    answer = Column(UnicodeText, index=True)

    # owner = relationship("user", back_populates="leaderboard")


engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)
