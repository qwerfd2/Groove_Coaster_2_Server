from starlette.responses import JSONResponse, Response
from starlette.requests import Request

import sqlalchemy
from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select, update

import os
import databases
import datetime

DB_NAME = "player.db"
DB_PATH = os.path.join(os.getcwd(), DB_NAME)
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

user = Table(
    "user",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("username", String(20), unique=True, nullable=False),
    Column("password_hash", String(255), nullable=False),
    Column("device_id", String(512)),
    Column("data", String, nullable=True),
    Column("save_id", String, nullable=True),
    Column("crc", Integer, nullable=True),
    Column("timestamp", DateTime, default=datetime.datetime.utcnow),
    Column("coin_mp", Integer, default=1),
)

daily_reward = Table(
    "daily_reward",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("device_id", String(512)),
    Column("timestamp", DateTime, default=datetime.datetime.utcnow),
    Column("my_stage", String),
    Column("my_avatar", String),
    Column("item", String),
    Column("day", Integer),
    Column("coin", Integer),
    Column("lvl", Integer),
    Column("title", Integer),
    Column("avatar", Integer),
)

result = Table(
    "result",
    metadata,
    Column("rid", Integer, primary_key=True, autoincrement=True),
    Column("vid", String(512), nullable=False),
    Column("tid", String(512), nullable=False),
    Column("sid", String(512), nullable=False),
    Column("stts", String(64)),
    Column("id", String(8)),
    Column("mode", String(4)),
    Column("avatar", String(4)),
    Column("score", String(16)),
    Column("high_score", String(128)),
    Column("play_rslt", String(128)),
    Column("item", String(16)),
    Column("os", String(16)),
    Column("os_ver", String(16)),
    Column("ver", String(16)),
    Column("mike", String(8)),

)

whitelist = Table(
    "whitelist",
    metadata,
    Column("id", String(512), primary_key=True)
)
blacklist = Table(
    "blacklist",
    metadata,
    Column("id", String(512), primary_key=True),
    Column("reason", String(256))
)

async def init_db():

    if not os.path.exists(DB_PATH):
        print("[DB] Creating new database:", DB_PATH)
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    
    await engine.dispose()
    print("[DB] Database initialized successfully.")

async def get_user_data(uid, data_field):
    query = select(user.c[data_field]).where(user.c.device_id == uid[b'vid'][0].decode())
    async with database.transaction():
        result = await database.fetch_one(query)
    return result[data_field] if result else None

async def set_user_data(uid, data_field, new_data):
    query = (
        update(user)
        .where(user.c.device_id == uid[b'vid'][0].decode())
        .values({data_field: new_data})
    )
    async with database.transaction():
        await database.execute(query)
        
async def check_whitelist(uid):
    query = select(whitelist.c.id).where(whitelist.c.id == uid[b'vid'][0].decode())
    async with database.transaction():
        result = await database.fetch_one(query)
    return result is not None

async def check_blacklist(uid):
    device_id = uid[b'vid'][0].decode()
    user_data = await get_user_data(uid, "username")
    username = user_data[0] if user_data else None

    query = select(blacklist.c.id).where(
        (blacklist.c.id == device_id) | (blacklist.c.id == username)
    )
    async with database.transaction():
        result = await database.fetch_one(query)
    return result is None