from starlette.responses import Response, FileResponse, HTMLResponse
from starlette.requests import Request
from starlette.routing import Route
import os
from datetime import datetime
import json
import secrets
from sqlalchemy import select, update, insert
import xml.etree.ElementTree as ET

from config import ROOT_FOLDER, START_COIN, AUTHORIZATION_NEEDED, HOST, PORT

from api.misc import is_alphanumeric, inform_page, verify_password, hash_password, crc32_decimal, get_model_pak, get_tune_pak, get_skin_pak, get_m4a_path, get_stage_path, get_stage_zero
from api.database import database, user, daily_reward, get_user_data, set_user_data, check_blacklist, check_whitelist
from api.crypt import decrypt_fields
from api.templates import START_AVATARS, START_STAGES

async def info(request: Request):
    file_path = os.path.join(ROOT_FOLDER, "files/history.html")
    return FileResponse(file_path)

async def history(request: Request):
    file_path = os.path.join(ROOT_FOLDER, "files/history.html")
    return FileResponse(file_path)

async def delete_account(request):
    # This only tricks the client to clear its local data for now
    return Response(
        """<?xml version="1.0" encoding="UTF-8"?><response><code>0</code><taito_id></taito_id></response>""",
        media_type="application/xml"
    )

async def tier(request: Request):
    file_path = os.path.join(ROOT_FOLDER, "files/tier.xml")
    return FileResponse(file_path)

async def reg(request: Request):
    return Response("", status_code=200)

async def name_reset(request: Request):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")

    if not username or not password:
        return HTMLResponse(inform_page("FAILED:<br>Missing username or password.", 0))

    if len(username) < 6 or len(username) > 20:
        return HTMLResponse(inform_page("FAILED:<br>Username must be between 6 and 20 characters long.", 0))

    if not is_alphanumeric(username):
        return HTMLResponse(inform_page("FAILED:<br>Username must consist entirely of alphanumeric characters.", 0))

    if username == password:
        return HTMLResponse(inform_page("FAILED:<br>Username cannot be the same as password.", 0))

    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return HTMLResponse(inform_page("FAILED:<br>Invalid request data.", 0))

    if not await check_blacklist(decrypted_fields):
        return HTMLResponse(inform_page("FAILED:<br>Your account is banned and you are not allowed to perform this action.", 0))

    user_exist = await get_user_data(decrypted_fields, "username")
    if user_exist:

        query = select(user.c.id).where(user.c.username == username)
        existing_user = await database.fetch_one(query)
        if existing_user:
            return HTMLResponse(inform_page("FAILED:<br>Another user already has this name.", 0))

        password_hash = await get_user_data(decrypted_fields, "password_hash")
        if password_hash:
            if verify_password(password, password_hash):
                await set_user_data(decrypted_fields, "username", username)
                return HTMLResponse(inform_page("SUCCESS:<br>Username updated.", 0))
            else:
                return HTMLResponse(inform_page("FAILED:<br>Password is not correct.<br>Please try again.", 0))
        else:
            return HTMLResponse(inform_page("FAILED:<br>User has no password hash.<br>This should not happen.", 0))
    else:
        return HTMLResponse(inform_page("FAILED:<br>User does not exist.<br>This should not happen.", 0))


async def password_reset(request: Request):
    form = await request.form()
    old_password = form.get("old")
    new_password = form.get("new")

    if not old_password or not new_password:
        return HTMLResponse(inform_page("FAILED:<br>Missing old or new password.", 0))

    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return HTMLResponse(inform_page("FAILED:<br>Invalid request data.", 0))

    username = await get_user_data(decrypted_fields, "username")
    if username:
        if username == new_password:
            return HTMLResponse(inform_page("FAILED:<br>Username cannot be the same as password.", 0))
        if len(new_password) < 6:
            return HTMLResponse(inform_page("FAILED:<br>Password must have 6 or more characters.", 0))

        old_hash = await get_user_data(decrypted_fields, "password_hash")
        print("hash type", type(old_hash))
        if old_hash:
            if verify_password(old_password, old_hash):
                hashed_new_password = hash_password(new_password)
                await set_user_data(decrypted_fields, "password_hash", hashed_new_password)
                return HTMLResponse(inform_page("SUCCESS:<br>Password updated.", 0))
            else:
                return HTMLResponse(inform_page("FAILED:<br>Old password is not correct.<br>Please try again.", 0))
        else:
            return HTMLResponse(inform_page("FAILED:<br>User has no password hash.<br>This should not happen.", 0))
    else:
        return HTMLResponse(inform_page("FAILED:<br>User does not exist.<br>This should not happen.", 0))


async def coin_mp(request: Request):
    form = await request.form()
    mp = int(form.get("coin_mp"))

    if not mp:
        return HTMLResponse(inform_page("FAILED:<br>Missing multiplier.", 0))

    if mp < 0 or mp > 5:
        return HTMLResponse(inform_page("FAILED:<br>Multiplier not acceptable.", 0))

    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return HTMLResponse(inform_page("FAILED:<br>Invalid request data.", 0))

    user_exist = await get_user_data(decrypted_fields, "username")
    if user_exist:
        await set_user_data(decrypted_fields, "coin_mp", mp)
        return HTMLResponse(inform_page("SUCCESS:<br>Coin multiplier set to " + str(mp) + ".", 0))
    else:
        return HTMLResponse(inform_page("FAILED:<br>User does not exist.", 0))


async def save_migration(request: Request):
    form = await request.form()
    save_id = form.get("save_id")

    if not save_id:
        return HTMLResponse(inform_page("FAILED:<br>Missing save_id.", 0))

    if len(save_id) != 24 or not all(c in '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ' for c in save_id):
        return HTMLResponse(inform_page("FAILED:<br>Save ID not acceptable format.", 0))

    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return HTMLResponse(inform_page("FAILED:<br>Invalid request data.", 0))

    user_exist = await get_user_data(decrypted_fields, "username")
    if user_exist:
        query = select(user.c.username, user.c.data, user.c.crc).where(user.c.save_id == save_id)
        existing_save_data = await database.fetch_one(query)

        if existing_save_data:
            if existing_save_data['username'] == user_exist:
                return HTMLResponse(inform_page("FAILED:<br>Save ID is already associated with your account.", 0))
            query = update(user).where(user.c.device_id == decrypted_fields[b'vid'][0].decode()).values(
                data=existing_save_data["data"],
                crc=existing_save_data["crc"],
                timestamp=datetime.now()
            )
            await database.execute(query)
            return HTMLResponse(inform_page("SUCCESS:<br>Save migration was applied. If this was done by mistake, press the Save button now.", 0))
        else:
            return HTMLResponse(inform_page("FAILED:<br>Save ID is not associated with a save file.", 0))

    else:
        return HTMLResponse(inform_page("FAILED:<br>User does not exist.", 0))


async def register(request: Request):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")

    if not username or not password:
        return HTMLResponse(inform_page("FAILED:<br>Missing username or password.", 0))

    if username == password:
        return HTMLResponse(inform_page("FAILED:<br>Username cannot be the same as password.", 0))

    if len(username) < 6 or len(username) > 20:
        return HTMLResponse(inform_page("FAILED:<br>Username must be between 6 and 20<br>characters long.", 0))

    if len(password) < 6:
        return HTMLResponse(inform_page("FAILED:<br>Password must have<br>6 or above characters.", 0))

    if not is_alphanumeric(username):
        return HTMLResponse(inform_page("FAILED:<br>Username must consist entirely of<br>alphanumeric characters.", 0))

    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return HTMLResponse(inform_page("FAILED:<br>Invalid request data.", 0))

    query = select(user.c.id).where(user.c.username == username)
    existing_user = await database.fetch_one(query)
    if existing_user:
        return HTMLResponse(inform_page("FAILED:<br>Another user already has this name.", 0))

    insert_query = insert(user).values(
        username=username,
        password_hash=hash_password(password),
        device_id=decrypted_fields[b'vid'][0].decode(),
        data="",
        crc=0,
        coin_mp=1,
    )
    await database.execute(insert_query)

    return HTMLResponse(inform_page("SUCCESS:<br>Account is registered.<br>You can now backup/restore your save file.<br>You can only log into one device at a time.", 0))

async def logout(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return HTMLResponse(inform_page("FAILED:<br>Invalid request data.", 0))

    if not await check_blacklist(decrypted_fields):
        return HTMLResponse(inform_page("FAILED:<br>Your account is banned and you are<br>not allowed to perform this action.", 0))

    await set_user_data(decrypted_fields, "device_id", "")
    return HTMLResponse(inform_page("Logout success.", 0))

async def login(request: Request):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")

    if not username or not password:
        return HTMLResponse(inform_page("FAILED:<br>Missing username or password.", 0))

    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return HTMLResponse(inform_page("FAILED:<br>Invalid request data.", 0))

    query = select(user.c.id).where(user.c.username == username)
    user_record = await database.fetch_one(query)
    if user_record:
        user_id = user_record[0]

        query = select(user.c.password_hash).where(user.c.id == user_id)
        password_hash_record = await database.fetch_one(query)
        if password_hash_record and verify_password(password, password_hash_record[0]):
            update_query = (
                update(user)
                .where(user.c.id == user_id)
                .values(device_id=decrypted_fields[b'vid'][0].decode())
            )
            await database.execute(update_query)
            return HTMLResponse(inform_page("SUCCESS:<br>You are logged in.", 0))
        else:
            return HTMLResponse(inform_page("FAILED:<br>Username or password incorrect.", 0))
    else:
        return HTMLResponse(inform_page("FAILED:<br>Username or password incorrect.", 0))

async def load(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return Response("""<response><code>10</code><message><ja>この機能を使用するには、まずアカウントを登録する必要があります。</ja><en>You need to register an account first before this feature can be used.</en><fr>Vous devez d'abord créer un compte avant de pouvoir utiliser cette fonctionnalité.</fr><it>È necessario registrare un account prima di poter utilizzare questa funzione.</it></message></response>""", media_type="application/xml")

    data = await get_user_data(decrypted_fields, "data")
    if data and data != "":
        crc = await get_user_data(decrypted_fields, "crc")
        timestamp = await get_user_data(decrypted_fields, "timestamp")
        xml_data = f"""<?xml version="1.0" encoding="UTF-8"?><response><code>0</code>
            <data>{data}</data>
            <crc>{crc}</crc>
            <date>{timestamp}</date>
            </response>"""
        return Response(xml_data, media_type="application/xml")
    else:
        return Response( """<response><code>12</code><message><ja>セーブデータが無いか、セーブデータが破損しているため、ロードできませんでした。</ja><en>Unable to load; either no save data exists, or the save data is corrupted.</en><fr>Chargement impossible : les données de sauvegarde sont absentes ou corrompues.</fr><it>Impossibile caricare. Non esistono dati salvati o quelli esistenti sono danneggiati.</it></message></response>""", media_type="application/xml")

async def save(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return Response("""<response><code>10</code><message><ja>この機能を使用するには、まずアカウントを登録する必要があります。</ja><en>You need to register an account first before this feature can be used.</en><fr>Vous devez d'abord créer un compte avant de pouvoir utiliser cette fonctionnalité.</fr><it>È necessario registrare un account prima di poter utilizzare questa funzione.</it></message></response>""", media_type="application/xml")

    data = await request.body()
    data = data.decode("utf-8")

    username = await get_user_data(decrypted_fields, "username")
    if username:
        crc = crc32_decimal(data)
        formatted_time = datetime.now()
        is_save_id_unique = False
        while not is_save_id_unique:
            save_id = ''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(24))

            check_query = select(user.c.id).where(user.c.save_id == save_id)
            existing_user = await database.fetch_one(check_query)
            if not existing_user:
                is_save_id_unique = True

        update_query = (
            update(user)
            .where(user.c.device_id == decrypted_fields[b'vid'][0].decode())
            .values(data=data, crc=crc, save_id=save_id, timestamp=formatted_time)
        )
        await database.execute(update_query)

        return Response("""<response><code>0</code></response>""", media_type="application/xml")
    else:
        return Response("""<response><code>10</code><message><ja>この機能を使用するには、まずアカウントを登録する必要があります。</ja><en>You need to register an account first before this feature can be used.</en><fr>Vous devez d'abord créer un compte avant de pouvoir utiliser cette fonctionnalité.</fr><it>È necessario registrare un account prima di poter utilizzare questa funzione.</it></message></response>""", media_type="application/xml")
    
async def start(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return Response("""<response><code>10</code><message><ja>Invalid request data.</ja><en>Invalid request data.</en></message></response>""", media_type="application/xml"
        )

    file_path = os.path.join(ROOT_FOLDER, "files/start.xml")
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        return Response(f"""<response><code>500</code><message>Error parsing XML: {str(e)}</message></response>""", media_type="application/xml")

    username = await get_user_data(decrypted_fields, "username")
    user_id = await get_user_data(decrypted_fields, "id")

    should_serve = True
    if AUTHORIZATION_NEEDED:
        should_serve = await check_whitelist(decrypted_fields) and not await check_blacklist(decrypted_fields)

    if not should_serve:
        return Response("""<response><code>403</code><message>Access denied.</message></response>""", media_type="application/xml")

    host_string = "http://" + HOST + ":" + str(PORT) + "/"
    device_id = decrypted_fields[b'vid'][0].decode()

    for generator in [get_model_pak, get_tune_pak, get_skin_pak, get_m4a_path, get_stage_path]:
        try:
            root.append(generator(host_string))
        except Exception as e:
            return Response(f"""<response><code>500</code><message>Error generating XML element: {str(e)}</message></response>""", media_type="application/xml")

    daily_reward_elem = root.find(".//login_bonus")
    if daily_reward_elem is None:
        return Response("""<response><code>500</code><message>Missing <login_bonus> element in XML.</message></response>""", media_type="application/xml")

    last_count_elem = daily_reward_elem.find("last_count")
    if last_count_elem is None or not last_count_elem.text.isdigit():
        return Response("""<response><code>500</code><message>Invalid or missing last_count in XML.</message></response>""", media_type="application/xml")
    last_count = int(last_count_elem.text)
    now_count = 1

    query = select(daily_reward.c.day, daily_reward.c.timestamp).where(daily_reward.c.device_id == device_id)
    row = await database.fetch_one(query)

    if row:
        current_day = row["day"]
        last_timestamp = row["timestamp"]
        current_date = datetime.now()

        if (current_date.date() - last_timestamp.date()).days >= 1:
            now_count = current_day + 1
            if now_count > last_count:
                now_count = 1
        else:
            now_count = current_day

    now_count_elem = daily_reward_elem.find("now_count")
    if now_count_elem is None:
        now_count_elem = ET.Element("now_count")
        daily_reward_elem.append(now_count_elem)
    now_count_elem.text = str(now_count)

    query = select(daily_reward.c.my_avatar, daily_reward.c.my_stage, daily_reward.c.coin).where(daily_reward.c.device_id == device_id)
    result_obj = await database.fetch_one(query)

    if result_obj:
        my_avatar = set(json.loads(result_obj[0])) if result_obj[0] else START_AVATARS
        my_stage = set(json.loads(result_obj[1])) if result_obj[1] else START_STAGES
        coin = result_obj[2] if result_obj[2] is not None else START_COIN
    else:
        my_avatar = START_AVATARS
        my_stage = START_STAGES
        coin = START_COIN

    coin_elem = ET.Element("my_coin")
    coin_elem.text = str(coin)
    root.append(coin_elem)

    for avatar_id in my_avatar:
        avatar_elem = ET.Element("my_avatar")
        avatar_elem.text = str(avatar_id)
        root.append(avatar_elem)

    for stage_id in my_stage:
        stage_elem = ET.Element("my_stage")
        stage_id_elem = ET.Element("stage_id")
        stage_id_elem.text = str(stage_id)
        stage_elem.append(stage_id_elem)

        ac_mode_elem = ET.Element("ac_mode")
        ac_mode_elem.text = "1"
        stage_elem.append(ac_mode_elem)
        root.append(stage_elem)

    if username:
        tid = ET.Element("taito_id")
        tid.text = username
        root.append(tid)

        sid_elem = ET.Element("sid")
        sid_elem.text = str(user_id)
        root.append(sid_elem)

        try:
            sid = get_stage_zero()
            root.append(sid)
        except Exception as e:
            return Response(f"""<response><code>500</code><message>Error retrieving stage zero: {str(e)}</message></response>""", media_type="application/xml")

    xml_response = ET.tostring(root, encoding='unicode')
    return Response(xml_response, media_type="application/xml")

async def sync(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return Response(
            """<response><code>10</code><message>Invalid request data.</message></response>""",
            media_type="application/xml"
        )

    device_id = decrypted_fields[b'vid'][0].decode()
    file_path = os.path.join(ROOT_FOLDER, "files/sync.xml")
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        return Response(
            f"""<response><code>500</code><message>Error parsing XML: {str(e)}</message></response>""",
            media_type="application/xml"
        )

    username = await get_user_data(decrypted_fields, "username")
    should_serve = True
    if AUTHORIZATION_NEEDED:
        should_serve = await check_whitelist(decrypted_fields) and not await check_blacklist(decrypted_fields)

    if not should_serve:
        return Response(
            """<response><code>403</code><message>Access denied.</message></response>""",
            media_type="application/xml"
        )

    host_string = "http://" + HOST + ":" + str(PORT) + "/"
    root.append(get_model_pak(host_string))
    root.append(get_tune_pak(host_string))
    root.append(get_skin_pak(host_string))
    root.append(get_m4a_path(host_string))
    root.append(get_stage_path(host_string))

    query = select(daily_reward.c.my_avatar, daily_reward.c.my_stage, daily_reward.c.coin, daily_reward.c.item).where(daily_reward.c.device_id == device_id)
    result_obj = await database.fetch_one(query)

    if result_obj:
        my_avatar = set(json.loads(result_obj[0])) if result_obj[0] else START_AVATARS
        my_stage = set(json.loads(result_obj[1])) if result_obj[1] else START_STAGES
        coin = result_obj[2] if result_obj[2] is not None else START_COIN
        items = json.loads(result_obj[3]) if result_obj[3] else []
    else:
        my_avatar = START_AVATARS
        my_stage = START_STAGES
        coin = START_COIN
        items = []

    coin_elem = ET.Element("my_coin")
    coin_elem.text = str(coin)
    root.append(coin_elem)

    for item in items:
        item_elem = ET.Element("add_item")
        item_id_elem = ET.Element("id")
        item_id_elem.text = str(item)
        item_elem.append(item_id_elem)
        item_num_elem = ET.Element("num")
        item_num_elem.text = "9"
        item_elem.append(item_num_elem)
        root.append(item_elem)

    if items:
        update_query = (
            update(daily_reward)
            .where(daily_reward.c.device_id == device_id)
            .values(item="[]")
        )
        await database.execute(update_query)

    for avatar_id in my_avatar:
        avatar_elem = ET.Element("my_avatar")
        avatar_elem.text = str(avatar_id)
        root.append(avatar_elem)

    for stage_id in my_stage:
        stage_elem = ET.Element("my_stage")
        stage_id_elem = ET.Element("stage_id")
        stage_id_elem.text = str(stage_id)
        stage_elem.append(stage_id_elem)

        ac_mode_elem = ET.Element("ac_mode")
        ac_mode_elem.text = "1"
        stage_elem.append(ac_mode_elem)
        root.append(stage_elem)

    if username:
        tid = ET.Element("taito_id")
        tid.text = username
        root.append(tid)

        sid = get_stage_zero()
        root.append(sid)

        kid = ET.Element("friend_num")
        kid.text = "9"
        root.append(kid)

    xml_response = ET.tostring(root, encoding='unicode')
    return Response(xml_response, media_type="application/xml")

async def ttag(request: Request):
    decrypted_fields, original_field = await decrypt_fields(request)
    if not decrypted_fields:
        return HTMLResponse("""<html><body><h1>Invalid request data</h1></body></html>""", status_code=400)

    username = await get_user_data(decrypted_fields, "username")
    if username:
        gcoin_mp = await get_user_data(decrypted_fields, "coin_mp")
        savefile_id = await get_user_data(decrypted_fields, "save_id")
        with open("files/profile.html", "r") as file:
            html_content = file.read().format(
                pid=original_field,
                user=username,
                gcoin_mp_0='selected' if gcoin_mp == 0 else '',
                gcoin_mp_1='selected' if gcoin_mp == 1 else '',
                gcoin_mp_2='selected' if gcoin_mp == 2 else '',
                gcoin_mp_3='selected' if gcoin_mp == 3 else '',
                gcoin_mp_4='selected' if gcoin_mp == 4 else '',
                gcoin_mp_5='selected' if gcoin_mp == 5 else '',
                savefile_id=savefile_id
            )
    else:
        with open("files/register.html", "r") as file:
            html_content = file.read().format(pid=original_field)

    return HTMLResponse(html_content)

async def bonus(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return Response("""<response><code>10</code><message>Invalid request data.</message></response>""", media_type="application/xml")

    device_id = decrypted_fields[b'vid'][0].decode()
    file_path = os.path.join(ROOT_FOLDER, "files/start.xml")

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        return Response(f"""<response><code>500</code><message>Error parsing XML: {str(e)}</message></response>""", media_type="application/xml")

    daily_reward_elem = root.find(".//login_bonus")
    last_count_elem = daily_reward_elem.find("last_count")
    if last_count_elem is None or not last_count_elem.text.isdigit():
        return Response("""<response><code>500</code><message>Invalid or missing last_count in XML.</message></response>""", media_type="application/xml")
    last_count = int(last_count_elem.text)

    query = select(daily_reward.c.day, daily_reward.c.timestamp, daily_reward.c.my_avatar, daily_reward.c.my_stage).where(daily_reward.c.device_id == device_id)
    row = await database.fetch_one(query)

    time = datetime.now()

    if row:
        current_day = row["day"]
        last_timestamp = row["timestamp"]
        my_avatar = set(json.loads(row["my_avatar"])) if row["my_avatar"] else set()
        my_stage = set(json.loads(row["my_stage"])) if row["my_stage"] else set()

        if (time.date() - last_timestamp.date()).days >= 1:
            current_day += 1
            if current_day > last_count:
                current_day = 1
            reward_elem = daily_reward_elem.find(f".//reward[count='{current_day}']")
            if reward_elem is not None:
                cnt_type = int(reward_elem.find("cnt_type").text)
                cnt_id = int(reward_elem.find("cnt_id").text)

                if cnt_type == 1:
                    stages = set(json.loads(my_stage)) if my_stage else set()
                    if cnt_id not in stages:
                        stages.add(cnt_id)
                    my_stage = json.dumps(list(stages))
                    update_query = (
                        update(daily_reward)
                        .where(daily_reward.c.device_id == device_id)
                        .values(timestamp=time, day=current_day, my_stage=my_stage)
                    )
                    await database.execute(update_query)

                elif cnt_type == 2:
                    avatars = set(json.loads(my_avatar)) if my_avatar else set()
                    if cnt_id not in avatars:
                        avatars.add(cnt_id)
                    my_avatar = json.dumps(list(avatars))
                    update_query = (
                        update(daily_reward)
                        .where(daily_reward.c.device_id == device_id)
                        .values(timestamp=time, day=current_day, my_avatar=my_avatar)
                    )
                    await database.execute(update_query)
                
                else:
                    update_query = (
                        update(daily_reward)
                        .where(daily_reward.c.device_id == device_id)
                        .values(timestamp=time, day=current_day)
                    )
                    await database.execute(update_query)
            else:
                update_query = (
                    update(daily_reward)
                    .where(daily_reward.c.device_id == device_id)
                    .values(timestamp=time, day=current_day)
                )
                await database.execute(update_query)

            xml_response = "<response><code>0</code></response>"
        else:
            xml_response = "<response><code>1</code></response>"
    else:
        insert_query = insert(daily_reward).values(
            device_id=device_id,
            day=1,
            timestamp=time,
            my_avatar=json.dumps(START_AVATARS),
            my_stage=json.dumps(START_STAGES),
            coin=START_COIN,
            item="[]",
            lvl=1,
            title=1,
            avatar=1
        )
        await database.execute(insert_query)
        xml_response = "<response><code>0</code></response>"

    return Response(xml_response, media_type="application/xml")

routes = [
    Route('/info.php', info, methods=['GET']),
    Route('/history.php', history, methods=['GET']),
    Route('/delete_account.php', delete_account, methods=['GET']),
    Route('/confirm_tier.php', tier, methods=['GET']),
    Route('/gcm/php/register.php', reg, methods=['GET']),
    Route('/name_reset/', name_reset, methods=['POST']),
    Route('/password_reset/', password_reset, methods=['POST']),
    Route('/coin_mp/', coin_mp, methods=['POST']),
    Route('/save_migration/', save_migration, methods=['POST']),
    Route('/register/', register, methods=['POST']),
    Route('/logout/', logout, methods=['POST']),
    Route('/login/', login, methods=['POST']),
    Route('/load.php', load, methods=['GET']),
    Route('/save.php', save, methods=['POST']),
    Route('/start.php', start, methods=['GET']),
    Route('/sync.php', sync, methods=['GET', 'POST']),
    Route('/ttag.php', ttag, methods=['GET']),
    Route('/login_bonus.php', bonus, methods=['GET'])
]