import sqlalchemy
from sqlalchemy import Table, Column, Integer, String, DateTime, JSON, ForeignKey, Index
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select, update, insert
import json
import os

START_COIN = 10

import os
import databases
from datetime import datetime, timedelta

DB_NAME = "player.db"
DB_PATH = os.path.join(os.getcwd(), DB_NAME)
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

OLD_DB_NAME = "player_d.db"
OLD_DB_PATH = os.path.join(os.getcwd(), OLD_DB_NAME)
OLD_DATABASE_URL = f"sqlite+aiosqlite:///{OLD_DB_PATH}"

old_database = databases.Database(OLD_DATABASE_URL)
old_metadata = sqlalchemy.MetaData()

player_database = databases.Database(DATABASE_URL)
player_metadata = sqlalchemy.MetaData()

#----------------------- Old Table definitions -----------------------#

user = Table(
    "user",
    old_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("username", String(20), unique=True, nullable=False),
    Column("password_hash", String(255), nullable=False),
    Column("device_id", String(512)),
    Column("data", String, nullable=True),
    Column("save_id", String, nullable=True),
    Column("crc", Integer, nullable=True),
    Column("timestamp", DateTime, default=None),
    Column("coin_mp", Integer, default=1)
)

daily_reward = Table(
    "daily_reward",
    old_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("device_id", String(512)),
    Column("timestamp", DateTime, default=datetime.utcnow),
    Column("my_stage", JSON),
    Column("my_avatar", JSON),
    Column("item", JSON),
    Column("day", Integer),
    Column("coin", Integer),
    Column("lvl", Integer),
    Column("title", Integer),
    Column("avatar", Integer),
)

result = Table(
    "result",
    old_metadata,
    Column("rid", Integer, primary_key=True, autoincrement=True),
    Column("vid", String(512), nullable=False),
    Column("tid", String(512), nullable=False),
    Column("sid", Integer, nullable=False),
    Column("stts", String(64)),
    Column("id", Integer),
    Column("mode", Integer),
    Column("avatar", Integer),
    Column("score", Integer),
    Column("high_score", String(128)),
    Column("play_rslt", String(128)),
    Column("item", Integer),
    Column("os", String(16)),
    Column("os_ver", String(16)),
    Column("ver", String(16)),
    Column("mike", Integer),
)

whitelist = Table(
    "whitelist",
    old_metadata,
    Column("id", String(512), primary_key=True)
)
blacklist = Table(
    "blacklist",
    old_metadata,
    Column("id", String(512), primary_key=True),
    Column("reason", String(256))
)

bind = Table(
    "bind",
    old_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, sqlalchemy.ForeignKey("user.id")),
    Column("bind_acc", String(256), unique=True, nullable=False),
    Column("bind_code", String(16), nullable=False),
    Column("is_verified", Integer, default=0),
    Column("auth_token", String(256), nullable=True),
    Column("bind_date", DateTime, default=datetime.utcnow)
)

logs = Table(
    "logs",
    old_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, sqlalchemy.ForeignKey("user.id")),
    Column("filename", String(256)),
    Column("filesize", Integer),
    Column("timestamp", DateTime, default=datetime.utcnow)
)

device_list = Table(
    "device_list",
    old_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, sqlalchemy.ForeignKey("user.id")),
    Column("device_id", String(512), unique=True, nullable=False),
    Column("last_login", DateTime, default=datetime.utcnow)
)

#----------------------- End of old Table definitions -----------------------#

#----------------------- New Table definitions -----------------------#

accounts = Table(
    "accounts",
    player_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("username", String(20), unique=True, nullable=False),
    Column("password_hash", String(255), nullable=False),
    Column("save_crc", String(24), nullable=True),
    Column("save_timestamp", DateTime, nullable=True),
    Column("save_id", String(24), nullable=True),
    Column("coin_mp", Integer, default=0),
    Column("title", Integer, default=1),
    Column("avatar", Integer, default=1),
    Column("mobile_delta", Integer, default=0),
    Column("arcade_delta", Integer, default=0),
    Column("total_delta", Integer, default=0),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
)

devices = Table(
    "devices",
    player_metadata,
    Column("device_id", String(64), primary_key=True),
    Column("user_id", Integer, ForeignKey("accounts.id")),
    Column("my_stage", JSON, default=[]),
    Column("my_avatar", JSON, default=[]),
    Column("item", JSON, default=[]),
    Column("daily_day", Integer, default=0),
    Column("daily_timestamp", DateTime, default=datetime.min),
    Column("coin", Integer, default=START_COIN),
    Column("lvl", Integer, default=1),
    Column("title", Integer, default=1),
    Column("avatar", Integer, default=1),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    Column("last_login_at", DateTime, default=None)
)

results = Table(
    "results",
    player_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("device_id", String(64), ForeignKey("devices.device_id")),
    Column("user_id", Integer, ForeignKey("accounts.id")),
    Column("stts", JSON, nullable=False),
    Column("song_id", Integer, nullable=False),
    Column("mode", Integer, nullable=False),
    Column("avatar", Integer, nullable=False),
    Column("score", Integer, nullable=False),
    Column("high_score", JSON, nullable=False),
    Column("play_rslt", JSON, nullable=False),
    Column("item", Integer, nullable=False),
    Column("os", String(8), nullable=False),
    Column("os_ver", String(16), nullable=False),
    Column("ver", String(8), nullable=False),
    Column("created_at", DateTime, default=datetime.utcnow)
)

Index(
    "idx_results_song_mode_score",
    results.c.song_id,
    results.c.mode,
    results.c.score.desc(),
)

webs = Table(
    "webs",
    player_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("accounts.id")),
    Column("permission", Integer, default=1),
    Column("web_token", String(128), unique=True, nullable=False),
    Column("last_save_export", Integer, nullable=True),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
)

batch_tokens = Table(
    "batch_tokens",
    player_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("batch_token", String(128), unique=True, nullable=False),
    Column("expire_at", DateTime, nullable=False),
    Column("uses_left", Integer, default=1),
    Column("auth_id", String(64), nullable=False),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
)

whitelists = Table(
    "whitelists",
    player_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("device_id", String(64), ForeignKey("devices.device_id")),
)

blacklists = Table(
    "blacklists",
    player_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("ban_terms", String(128), unique=True, nullable=False),
    Column("reason", String(255), nullable=True)
)

binds = Table(
    "binds",
    player_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("accounts.id")),
    Column("bind_account", String(128), unique=True, nullable=False),
    Column("bind_code", String(6), nullable=False),
    Column("is_verified", Integer, default=0),
    Column("auth_token", String(64), unique=True),
    Column("bind_date", DateTime, default=datetime.utcnow)
)

logs = Table(
    "logs",
    player_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("accounts.id")),
    Column("filename", String(255), nullable=False),
    Column("filesize", Integer, nullable=False),
    Column("timestamp", DateTime, default=datetime.utcnow)
)

#----------------------- End of new Table definitions -----------------------#

async def init_db():
    if not os.path.exists(DB_PATH):
        print("[DB] Creating new database:", DB_PATH)

    if not os.path.exists(OLD_DB_PATH):
        print("[DB] Old db must exist as player_d.db")
    
    old_engine = create_async_engine(OLD_DATABASE_URL, echo=False)
    async with old_engine.begin() as conn:
        await conn.run_sync(old_metadata.create_all)
    await old_engine.dispose()
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(player_metadata.create_all)
    
    await engine.dispose()
    print("[DB] Database initialized successfully.")

async def save_user_data(user_id, user_data):
    save_dir = "save"
    save_file = os.path.join(save_dir, f"{user_id}.dat")

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    with open(save_file, "w") as file:
        file.write(user_data)

async def convert_db():
    await old_database.connect()
    await player_database.connect()
    
    # Conversion logic goes here
    print("[DB] Starting database conversion...")

    # Convert user -> accounts
    print("[DB] Converting users to accounts...")
    query = select(old_metadata.tables["user"])
    all_users = await old_database.fetch_all(query)
    all_users = [dict(u) for u in all_users]
    for user in all_users:
        user_device_id = user['device_id']

        user_data = user.get('data') if 'data' in user else None
        if user_data:
            user_id = user['id']
            await save_user_data(user_id, user_data)


        user_old_device = await old_database.fetch_one(
            select(old_metadata.tables["daily_reward"]).where(old_metadata.tables["daily_reward"].c.device_id == user_device_id)
        )
        user_old_device = dict(user_old_device) if user_old_device else None

        insert_query = insert(accounts).values(
            username=user['username'],
            password_hash=user['password_hash'],
            save_crc=user['crc'],
            save_timestamp=user['timestamp'],
            save_id=user['save_id'],
            coin_mp=user['coin_mp'],
            title=user_old_device['title'] if user_old_device else 1,
            avatar=user_old_device['avatar'] if user_old_device else 1,
            mobile_delta=0,
            arcade_delta=0,
            total_delta=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        await player_database.execute(insert_query)

    # Compute score deltas
    print("[DB] Computing score deltas for accounts...")
    all_new_users = await player_database.fetch_all(select(accounts))
    all_new_users = [dict(u) for u in all_new_users]
    for new_user in all_new_users:
        username = new_user['username']
        old_user_object = await old_database.fetch_one(
            select(old_metadata.tables["user"]).where(old_metadata.tables["user"].c.username == username)
        )
        old_user_id = old_user_object['id']
        old_user_results_mobile = await old_database.fetch_all(
            select(old_metadata.tables["result"]).where(
                (old_metadata.tables["result"].c.sid == old_user_id) &
                (old_metadata.tables["result"].c.mode.in_([1, 2, 3]))
            )
        )
        old_user_mobile_sum = sum([int(r['score']) for r in old_user_results_mobile])
        old_user_results_arcade = await old_database.fetch_all(
            select(old_metadata.tables["result"]).where(
                (old_metadata.tables["result"].c.sid == old_user_id) &
                (old_metadata.tables["result"].c.mode.in_([11, 12, 13]))
            )
        )
        old_user_arcade_sum = sum([int(r['score']) for r in old_user_results_arcade])
        old_user_results_total = old_user_mobile_sum + old_user_arcade_sum

        update_query = (
            update(accounts).where(accounts.c.id == new_user['id']).values(
                mobile_delta=old_user_mobile_sum,
                arcade_delta=old_user_arcade_sum,
                total_delta=old_user_results_total
            )
        )
        await player_database.execute(update_query)

    # Convert daily_reward -> devices
    print("[DB] Converting daily rewards to devices...")
    all_devices = await old_database.fetch_all(select(old_metadata.tables["daily_reward"]))
    all_devices = [dict(d) for d in all_devices]
    for device in all_devices:
        connected_old_user = await old_database.fetch_one(
            select(old_metadata.tables["user"]).where(old_metadata.tables["user"].c.device_id == device['device_id'])
        )
        new_user_id = None
        old_user_username = connected_old_user['username'] if connected_old_user else None
        if old_user_username:
            connected_user = await player_database.fetch_one(
                select(accounts).where(accounts.c.username == old_user_username)
            )
            new_user_id = connected_user['id'] if connected_user else None

        insert_query = insert(devices).values(
            device_id=device['device_id'],
            user_id=new_user_id,
            my_stage=device['my_stage'],
            my_avatar=device['my_avatar'],
            item=device['item'],
            daily_day=device['day'],
            daily_timestamp=device['timestamp'],
            coin=device['coin'],
            lvl=device['lvl'],
            title=device['title'],
            avatar=device['avatar'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_login_at=datetime.utcnow()
        )
        await player_database.execute(insert_query)

    # convert result -> results
    print("[DB] Converting results to results...")
    all_results = await old_database.fetch_all(select(old_metadata.tables["result"]))
    all_results = [dict(r) for r in all_results]
    for result in all_results:
        if result['sid'] is not None and result['sid'] != 0:
            # Skip guests, they are no longer ranked
            old_user_object = await old_database.fetch_one(
                select(old_metadata.tables["user"]).where(old_metadata.tables["user"].c.id == result['sid'])
            )
            old_user_username = old_user_object['username'] if old_user_object else None
            if old_user_username:
                new_user_object = await player_database.fetch_one(
                    select(accounts).where(accounts.c.username == old_user_username)
                )
                new_user_id = new_user_object['id']
                insert_query = insert(results).values(
                    device_id=result['vid'],
                    user_id=new_user_id,
                    stts=convert_array(result['stts']),
                    song_id=result['id'],
                    mode=result['mode'],
                    avatar=result['avatar'],
                    score=result['score'],
                    high_score=convert_array(result['high_score']),
                    play_rslt=convert_array(result['play_rslt']),
                    item=result['item'],
                    os=result['os'],
                    os_ver=result['os_ver'],
                    ver=result['ver'],
                    created_at=datetime.utcnow(),
                )
                await player_database.execute(insert_query)

    # convert bwlist
    print("[DB] Converting blacklists and whitelists...")
    old_blacklists = await old_database.fetch_all(select(old_metadata.tables["blacklist"]))
    old_blacklists = [dict(b) for b in old_blacklists]

    for bl in old_blacklists:
        insert_query = insert(blacklists).values(
            ban_terms=bl['id'],
            reason=bl['reason']
        )
        await player_database.execute(insert_query)

    old_whitelists = await old_database.fetch_all(select(old_metadata.tables["whitelist"]))
    old_whitelists = [dict(w) for w in old_whitelists]
    for wl in old_whitelists:
        insert_query = insert(whitelists).values(
            device_id=wl['id']
        )
        await player_database.execute(insert_query)

    # convert binds (optional)

    if 'bind' in old_metadata.tables:
        print("[DB] Converting binds...")
        old_binds = await old_database.fetch_all(select(old_metadata.tables["bind"]))
        old_binds = [dict(b) for b in old_binds]
        for b in old_binds:
            insert_query = insert(binds).values(
                user_id=b['user_id'],
                bind_account=b['bind_acc'],
                bind_code=b['bind_code'],
                is_verified=b['is_verified'],
                auth_token=b['auth_token'],
                bind_date=b['bind_date']
            )
            await player_database.execute(insert_query)

    # convert logs (optional)

    if 'logs' in old_metadata.tables:
        print("[DB] Converting logs...")
        old_logs = await old_database.fetch_all(select(old_metadata.tables["logs"]))
        old_logs = [dict(l) for l in old_logs]
        for l in old_logs:
            insert_query = insert(logs).values(
                user_id=l['user_id'],
                filename=l['filename'],
                filesize=l['filesize'],
                timestamp=l['timestamp']
            )
            await player_database.execute(insert_query)

    # tables not converted: batch_tokens (new field added), webs (auto created)
    
    await old_database.disconnect()
    await player_database.disconnect()
    print("[DB] Database conversion completed successfully.")

def convert_array(old_array):
    old_array = "[" + old_array + "]"
    old_array = json.loads(old_array)
    return old_array
        


if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())
    asyncio.run(convert_db())