import sqlalchemy
from sqlalchemy import Table, Column, Integer, String, DateTime, JSON, ForeignKey, Index
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select, update
import base64
import aiofiles
import json

from config import START_COIN, SIMULTANEOUS_LOGINS
from api.template import START_AVATARS, START_STAGES

import os
import databases
from datetime import datetime, timedelta

DB_NAME = "player.db"
DB_PATH = os.path.join(os.getcwd(), DB_NAME)
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

CACHE_DB_NAME = "cache.db"
CACHE_DB_PATH = os.path.join(os.getcwd(), CACHE_DB_NAME)
CACHE_DATABASE_URL = f"sqlite+aiosqlite:///{CACHE_DB_PATH}"

cache_database = databases.Database(CACHE_DATABASE_URL)
cache_metadata = sqlalchemy.MetaData()

player_database = databases.Database(DATABASE_URL)
player_metadata = sqlalchemy.MetaData()

#----------------------- Table definitions -----------------------#

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

ranking_cache = Table(
    "ranking_cache",
    cache_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("key", String(16), nullable=False),
    Column("value", JSON, nullable=False),
    Column("expire_at", Integer)
)

#----------------------- End of Table definitions -----------------------#

async def init_db():
    if not os.path.exists(DB_PATH):
        print("[DB] Creating new database:", DB_PATH)

    if not os.path.exists(CACHE_DB_PATH):
        print("[DB] Creating new cache database:", CACHE_DB_PATH)
    
    cache_engine = create_async_engine(CACHE_DATABASE_URL, echo=False)
    async with cache_engine.begin() as conn:
        await conn.run_sync(cache_metadata.create_all)
    await cache_engine.dispose()
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(player_metadata.create_all)
    
    await engine.dispose()
    print("[DB] Database initialized successfully.")
    await ensure_user_columns()

async def ensure_user_columns():
    import aiosqlite

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("PRAGMA table_info(user);") as cursor:
            columns = [row[1] async for row in cursor]

        alter_needed = False
        #if "save_id" not in columns:
        #    await db.execute("ALTER TABLE user ADD COLUMN save_id TEXT;")
        #    alter_needed = True
        #if "coin_mp" not in columns:
        #    await db.execute("ALTER TABLE user ADD COLUMN coin_mp INTEGER DEFAULT 1;")
        #    alter_needed = True
        if alter_needed:
            await db.commit()
            print("[DB] Added missing columns to user table.")

async def get_bind(user_id):
    if not user_id:
        return None
    query = binds.select().where(binds.c.user_id == user_id)
    result = await player_database.fetch_one(query)
    return dict(result) if result else None

async def refresh_bind(user_id):
    existing_bind = await get_bind(user_id)
    if existing_bind and existing_bind['is_verified'] == 1:
        new_auth_token = base64.urlsafe_b64encode(os.urandom(64)).decode("utf-8")
        update_query = update(binds).where(binds.c.id == existing_bind['id']).values(
            auth_token=new_auth_token
        )
        await player_database.execute(update_query)

async def log_download(user_id, filename, filesize):
    query = logs.insert().values(
        user_id=user_id,
        filename=filename,
        filesize=filesize,
        timestamp=datetime.utcnow()
    )
    await player_database.execute(query)

async def get_downloaded_bytes(user_id, hours):
    query = select(sqlalchemy.func.sum(logs.c.filesize)).where(
        (logs.c.user_id == user_id) &
        (logs.c.timestamp >= datetime.utcnow() - timedelta(hours=hours))
    )
    result = await player_database.fetch_one(query)
    return result[0] if result[0] is not None else 0

async def verify_user_code(code, user_id):
    existing_bind = await get_bind(user_id)
    if existing_bind and existing_bind['is_verified'] == 1:
        return "This account is already bound to an account."
    
    query = binds.select().where(
        (binds.c.bind_code == code) &
        (binds.c.user_id == user_id) &
        (binds.c.is_verified == 0) &
        (binds.c.bind_date >= datetime.utcnow() - timedelta(minutes=10))
    )
    result = await player_database.fetch_one(query)
    if not result:
        return "Invalid or expired verification code."

    update_query = update(binds).where(binds.c.id == result['id']).values(
        is_verified=1,
        auth_token=base64.urlsafe_b64encode(os.urandom(64)).decode("utf-8")
    )
    await player_database.execute(update_query)
    return "Verified and account successfully bound."

async def decrypt_fields_to_user_info(decrypted_fields):
    device_id = decrypted_fields[b'vid'][0].decode()
    query = devices.select().where(devices.c.device_id == device_id)
    device_record = await player_database.fetch_one(query)
    if device_record:
        device_record = dict(device_record)
        user_query = accounts.select().where(accounts.c.id == device_record['user_id'])
        user_record = await player_database.fetch_one(user_query)
        if user_record:
            user_record = dict(user_record)
            return user_record, device_record
        
        return None, device_record
    
    return None, None

async def user_id_to_user_info(user_id):
    user_query = accounts.select().where(accounts.c.id == user_id)
    user_record = await player_database.fetch_one(user_query)
    user_record = dict(user_record) if user_record else None
    if user_record:
        user_record = dict(user_record)
        device_query = devices.select().where(devices.c.user_id == user_id)
        device_record = await player_database.fetch_all(device_query)
        device_record = [dict(d) for d in device_record]
        return user_record, device_record
    
    return None, None

async def user_id_to_user_info_simple(user_id):
    user_query = accounts.select().where(accounts.c.id == user_id)
    user_record = await player_database.fetch_one(user_query)
    user_record = dict(user_record) if user_record else None
    return user_record

async def user_name_to_user_info(username):
    user_query = accounts.select().where(accounts.c.username == username)
    user_record = await player_database.fetch_one(user_query)
    user_record = dict(user_record) if user_record else None
    
    return user_record

async def check_whitelist(decrypted_fields):
    device_id = decrypted_fields[b'vid'][0].decode()
    user_info, _ = await decrypt_fields_to_user_info(decrypted_fields)
    query = select(whitelists.c.device_id).where((whitelists.c.device_id == device_id) | (whitelists.c.device_id == user_info['username']))
    result = await player_database.fetch_one(query)
    return result is not None

async def check_blacklist(decrypted_fields):
    device_id = decrypted_fields[b'vid'][0].decode()
    user_info, _ = await decrypt_fields_to_user_info(decrypted_fields)
    query = select(blacklists.c.ban_terms).where((blacklists.c.ban_terms == device_id) | (blacklists.c.ban_terms == user_info['username']))
    result = await player_database.fetch_one(query)
    return result is None

async def get_user_entitlement_from_devices(user_id):
    devices_query = devices.select().where(devices.c.user_id == user_id)
    devices_list = await player_database.fetch_all(devices_query)
    devices_list = [dict(dev) for dev in devices_list] if devices_list else []

    stage_set = set()
    avatar_set = set()

    for dev in devices_list:
        my_stages = dev['my_stage'] if dev['my_stage'] else []
        my_avatars = dev['my_avatar'] if dev['my_avatar'] else []
        stage_set.update(my_stages)
        avatar_set.update(my_avatars)

    return list(stage_set), list(avatar_set)

async def set_user_data_using_decrypted_fields(decrypted_fields, data_fields):
    data_fields['updated_at'] = datetime.utcnow()
    device_id = decrypted_fields[b'vid'][0].decode()
    device_query = devices.select().where(devices.c.device_id == device_id)
    device_result = await player_database.fetch_one(device_query)
    if device_result:
        user_id = device_result['user_id']
        query = (
            update(accounts)
            .where(accounts.c.id == user_id)
            .values(**data_fields)
        )
        await player_database.execute(query)

async def set_device_data_using_decrypted_fields(decrypted_fields, data_fields):
    data_fields['updated_at'] = datetime.utcnow()
    device_id = decrypted_fields[b'vid'][0].decode()
    query = (
        update(devices)
        .where(devices.c.device_id == device_id)
        .values(**data_fields)
    )
    await player_database.execute(query)

async def get_user_from_save_id(save_id):
    query = accounts.select().where(accounts.c.save_id == save_id)
    result = await player_database.fetch_one(query)
    result = dict(result) if result else None
    return result

async def create_user(username, password_hash, device_id):
    insert_query = accounts.insert().values(
        username=username,
        password_hash=password_hash,
        save_crc=None,
        save_timestamp=None,
        save_id=None,
        coin_mp=1,
        title=1,
        avatar=1,
        mobile_delta=0,
        arcade_delta=0,
        total_delta=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    user_id = await player_database.execute(insert_query)
    await login_user(user_id, device_id)

async def logout_user(device_id):
    query = (
        update(devices)
        .where(devices.c.device_id == device_id)
        .values(user_id=None)
    )
    await player_database.execute(query)

async def login_user(user_id, device_id):
    query = (
        update(devices)
        .where(devices.c.device_id == device_id)
        .values(user_id=user_id, last_login_at=datetime.utcnow())
    )
    await player_database.execute(query)

    _, device_list = await user_id_to_user_info(user_id)

    if len(device_list) > SIMULTANEOUS_LOGINS:
        sorted_devices = sorted(device_list, key=lambda d: d['last_login_at'] or datetime.min)
        devices_to_logout = sorted_devices[:-SIMULTANEOUS_LOGINS]
        for device in devices_to_logout:
            await logout_user(device['device_id'])

async def create_device(device_id, current_time):
    insert_query = devices.insert().values(
        device_id=device_id,
        user_id=None,
        my_avatar=START_AVATARS,
        my_stage=START_STAGES,
        item=[],
        daily_day=1,
        daily_timestamp=current_time,
        coin=START_COIN,
        lvl=1,
        title=1,
        avatar=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        last_login_at=None
    )
    await player_database.execute(insert_query)

async def is_admin(token):
    if not token:
        return False
    query = webs.select().where(webs.c.web_token == token)
    web_data = await player_database.fetch_one(query)
    if not web_data:
        return False
    if web_data['permission'] != 2:
        return False
    return web_data['user_id']

async def results_query(query_params):
    query = select(results.c.id, results.c.user_id, results.c.score, results.c.avatar)
    for key, value in query_params.items():
        query = query.where(getattr(results.c, key) == value)
    query = query.order_by(results.c.score.desc())
    records = await player_database.fetch_all(query)
    return [dict(record) for record in records]

async def clear_rank_cache(key):
    delete_query = ranking_cache.delete().where(ranking_cache.c.key == key)
    await cache_database.execute(delete_query)

async def write_rank_cache(key, value, expire_seconds=None):
    if expire_seconds:
        expire_time = datetime.utcnow() + timedelta(seconds=expire_seconds)
    else:
        expire_time = None
    
    insert_query = ranking_cache.insert().values(
        key=key,
        value=value,
        expire_at=expire_time
    )
    await cache_database.execute(insert_query)

async def get_rank_cache(key):
    query = ranking_cache.select().where(ranking_cache.c.key == key)
    result = await cache_database.fetch_one(query)
    if result:
        expire_at = datetime.fromisoformat(result['expire_at']) if result['expire_at'] else None
        if expire_at and expire_at < datetime.utcnow():
            await clear_rank_cache(key)
            return None
        return dict(result)['value']
    return None

async def get_user_export_data(user_id):
    user_data = {}
    user_info, device_list = await user_id_to_user_info(user_id)

    user_save = await read_user_save_file(user_id)
    user_info['save_data'] = user_save

    user_data['account'] = [user_info]
    user_data['devices'] = device_list

    all_results_query = results.select().where(results.c.user_id == user_id)
    all_results = await player_database.fetch_all(all_results_query)
    user_data['results'] = [dict(result) for result in all_results]

    user_binds_query = binds.select().where(binds.c.user_id == user_id)
    user_binds = await player_database.fetch_all(user_binds_query)

    user_data['binds'] = [dict(bind) for bind in user_binds]
    # Convert JSON fields to strings
    for key, value in user_data.items():
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    for field, field_value in item.items():
                        if isinstance(field_value, (dict, list)):
                            item[field] = json.dumps(field_value)

    return user_data

async def read_user_save_file(user_id):
    if user_id is None:
        return ""
    elif type(user_id) != int:
        return ""
    else:
        try:
            async with aiofiles.open(f"./save/{user_id}.dat", "rb") as file:
                result = await file.read()
                result = result.decode("utf-8")
                return result
            
        except FileNotFoundError:
            return ""
        
async def write_user_save_file(user_id, data):
    if user_id is None:
        return
    elif type(user_id) != int:
        return
    else:
        try:
            async with aiofiles.open(f"./save/{user_id}.dat", "wb") as file:
                await file.write(data.encode("utf-8"))
        except Exception as e:
            print(f"An error occurred while writing the file: {e}")