from starlette.responses import Response, FileResponse, HTMLResponse
from starlette.requests import Request
from starlette.routing import Route
import os
from datetime import datetime
import xml.etree.ElementTree as ET
import copy

from config import START_COIN

from api.misc import get_model_pak, get_tune_pak, get_skin_pak, get_m4a_path, get_stage_path, get_stage_zero, should_serve_init, inform_page
from api.database import decrypt_fields_to_user_info, refresh_bind, get_user_entitlement_from_devices, set_device_data_using_decrypted_fields, create_device
from api.crypt import decrypt_fields
from api.template import START_AVATARS, START_STAGES, START_XML, SYNC_XML

async def info(request: Request):
    try:
        with open("web/history.html", "r", encoding="utf-8") as file:
            html_content = file.read()
    except FileNotFoundError:
        return inform_page("history.html not found", 1)
    
    return HTMLResponse(html_content)

async def history(request: Request):
    try:
        with open("web/history.html", "r", encoding="utf-8") as file:
            html_content = file.read()
    except FileNotFoundError:
        return inform_page("history.html not found", 1)
    
    return HTMLResponse(html_content)

async def delete_account(request):
    # This only tricks the client to clear its local data for now
    return Response(
        """<?xml version="1.0" encoding="UTF-8"?><response><code>0</code><taito_id></taito_id></response>""",
        media_type="application/xml"
    )

async def tier(request: Request):
    html_path = f"files/tier.xml"

    try:
        with open(html_path, "r", encoding="utf-8") as file:
            xml_content = file.read()
    except FileNotFoundError:
        return Response(
        """<?xml version="1.0" encoding="UTF-8"?><response><code>0</code></response>""",
        media_type="application/xml"
    )
    
    return Response(xml_content, media_type="application/xml")

async def reg(request: Request):
    return Response("", status_code=200)

async def start(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return Response("""<response><code>10</code><message><ja>Invalid request data.</ja><en>Invalid request data.</en></message></response>""", media_type="application/xml"
        )

    root = copy.deepcopy(START_XML.getroot())

    user_info, device_info = await decrypt_fields_to_user_info(decrypted_fields)
    username = user_info['username'] if user_info else None
    user_id = user_info['id'] if user_info else None
    device_id = decrypted_fields[b'vid'][0].decode()

    should_serve_result = await should_serve_init(decrypted_fields)
    if not should_serve_result:
        return Response("""<response><code>403</code><message>Access denied.</message></response>""", media_type="application/xml")

    if user_id:
        await refresh_bind(user_id)

    root.append(await get_model_pak(decrypted_fields, user_id))
    root.append(await get_tune_pak(decrypted_fields, user_id))
    root.append(await get_skin_pak(decrypted_fields, user_id))
    root.append(await get_m4a_path(decrypted_fields, user_id))
    root.append(await get_stage_path(decrypted_fields, user_id))
    daily_reward_elem = root.find(".//login_bonus")
    if daily_reward_elem is None:
        return Response("""<response><code>500</code><message>Missing <login_bonus> element in XML.</message></response>""", media_type="application/xml")

    last_count_elem = daily_reward_elem.find("last_count")
    if last_count_elem is None or not last_count_elem.text.isdigit():
        return Response("""<response><code>500</code><message>Invalid or missing last_count in XML.</message></response>""", media_type="application/xml")
    last_count = int(last_count_elem.text)
    now_count = 1

    if device_info:
        current_day = device_info["daily_day"]
        last_timestamp = device_info["daily_timestamp"]
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

    if user_id:
        # This is a logged in user
        my_stage, my_avatar = await get_user_entitlement_from_devices(user_id)
        coin = device_info['coin'] if device_info is not None else 0

    elif device_info:
        # This is a guest user with existing data
        my_avatar = set(device_info['my_avatar']) if device_info['my_avatar'] else START_AVATARS
        my_stage = set(device_info['my_stage']) if device_info['my_stage'] else START_STAGES
        coin = device_info['coin'] if device_info['coin'] is not None else 0
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

    should_serve_result = await should_serve_init(decrypted_fields)
    if not should_serve_result:
        return Response(
            """<response><code>403</code><message>Access denied.</message></response>""",
            media_type="application/xml"
        )

    device_id = decrypted_fields[b'vid'][0].decode()
    root = copy.deepcopy(SYNC_XML.getroot())

    user_info, device_info = await decrypt_fields_to_user_info(decrypted_fields)

    username = user_info['username'] if user_info else None
    user_id = user_info['id'] if user_info else None

    root.append(await get_model_pak(decrypted_fields, user_id))
    root.append(await get_tune_pak(decrypted_fields, user_id))
    root.append(await get_skin_pak(decrypted_fields, user_id))
    root.append(await get_m4a_path(decrypted_fields, user_id))
    root.append(await get_stage_path(decrypted_fields, user_id))
    if user_id:
        # This is a logged in user
        my_stage, my_avatar = await get_user_entitlement_from_devices(user_id)
        coin = device_info['coin'] if device_info['coin'] is not None else 0
        items = device_info['item'] if device_info['item'] else []

    elif device_info:
        # This is a guest user with existing data
        my_avatar = set(device_info['my_avatar']) if device_info['my_avatar'] else START_AVATARS
        my_stage = set(device_info['my_stage']) if device_info['my_stage'] else START_STAGES
        coin = device_info['coin'] if device_info['coin'] is not None else 0
        items = device_info['item'] if device_info['item'] else []
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
        await set_device_data_using_decrypted_fields(decrypted_fields, {"item": []})

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

async def bonus(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return Response("""<response><code>10</code><message>Invalid request data.</message></response>""", media_type="application/xml")

    device_id = decrypted_fields[b'vid'][0].decode()
    user_info, device_info = await decrypt_fields_to_user_info(decrypted_fields)

    root = copy.deepcopy(START_XML.getroot())

    daily_reward_elem = root.find(".//login_bonus")
    last_count_elem = daily_reward_elem.find("last_count")
    if last_count_elem is None or not last_count_elem.text.isdigit():
        return Response("""<response><code>500</code><message>Invalid or missing last_count in XML.</message></response>""", media_type="application/xml")
    last_count = int(last_count_elem.text)

    user_id = user_info['id'] if user_info else None

    time = datetime.now()

    if device_info:
        current_day = device_info["daily_day"]
        last_timestamp = device_info["daily_timestamp"]
        if user_id:
            my_stage, my_avatar = await get_user_entitlement_from_devices(user_id)
        else:
            my_avatar = set(device_info["my_avatar"]) if device_info["my_avatar"] else set()
            my_stage = set(device_info["my_stage"]) if device_info["my_stage"] else set()

        if (time.date() - last_timestamp.date()).days >= 1:
            current_day += 1
            if current_day > last_count:
                current_day = 1
            reward_elem = daily_reward_elem.find(f".//reward[count='{current_day}']")
            if reward_elem is not None:
                cnt_type = int(reward_elem.find("cnt_type").text)
                cnt_id = int(reward_elem.find("cnt_id").text)

                if cnt_type == 1:
                    stages = set(my_stage) if my_stage else set()
                    if cnt_id not in stages:
                        stages.add(cnt_id)
                    my_stage = list(stages)
                    update_data = {
                        "daily_timestamp": time,
                        "daily_day": current_day,
                        "my_stage": my_stage
                    }
                    await set_device_data_using_decrypted_fields(decrypted_fields, update_data)

                elif cnt_type == 2:
                    avatars = set(my_avatar) if my_avatar else set()
                    if cnt_id not in avatars:
                        avatars.add(cnt_id)
                    my_avatar = list(avatars)
                    update_data = {
                        "daily_timestamp": time,
                        "daily_day": current_day,
                        "my_avatar": my_avatar
                    }
                    await set_device_data_using_decrypted_fields(decrypted_fields, update_data)
                
                else:
                    update_data = {
                        "daily_timestamp": time,
                        "daily_day": current_day
                    }
                    await set_device_data_using_decrypted_fields(decrypted_fields, update_data)
            else:
                update_data = {
                    "daily_timestamp": time,
                    "daily_day": current_day
                }
                await set_device_data_using_decrypted_fields(decrypted_fields, update_data)

            xml_response = "<response><code>0</code></response>"
        else:
            xml_response = "<response><code>1</code></response>"
    else:
        await create_device(device_id, time)
        xml_response = "<response><code>0</code></response>"

    return Response(xml_response, media_type="application/xml")

routes = [
    Route('/info.php', info, methods=['GET']),
    Route('/history.php', history, methods=['GET']),
    Route('/delete_account.php', delete_account, methods=['GET']),
    Route('/confirm_tier.php', tier, methods=['GET']),
    Route('/gcm/php/register.php', reg, methods=['GET']),
    Route('/start.php', start, methods=['GET']),
    Route('/sync.php', sync, methods=['GET', 'POST']),
    Route('/login_bonus.php', bonus, methods=['GET'])
]