from starlette.responses import HTMLResponse, JSONResponse
from starlette.requests import Request
from starlette.routing import Route
import os

from config import STAGE_PRICE, AVATAR_PRICE, ITEM_PRICE, FMAX_PRICE, EX_PRICE

from api.crypt import decrypt_fields
from api.misc import inform_page, parse_res, should_serve, get_host_string
from api.database import decrypt_fields_to_user_info, get_user_entitlement_from_devices, set_device_data_using_decrypted_fields
from api.template import SONG_LIST, AVATAR_LIST, ITEM_LIST, EXCLUDE_STAGE_EXP

async def web_shop(request: Request):
    decrypted_fields, original_fields = await decrypt_fields(request)
    if not decrypted_fields:
        return inform_page("Invalid request data", 6)

    should_serve_result = await should_serve(decrypted_fields)

    if not should_serve_result:
        return inform_page("Access denied", 6)

    user_info, device_info = await decrypt_fields_to_user_info(decrypted_fields)
    if not device_info:
        return inform_page("Invalid device information", 6)

    try:
        with open("web/web_shop.html", "r", encoding="utf-8") as file:
            html_content = file.read().format(host_url=await get_host_string(), payload=original_fields)
    except FileNotFoundError:
        return inform_page("Shop page not found", 6)

    return HTMLResponse(html_content)

async def api_shop_player_data(request: Request):
    from api.misc import FMAX_VER
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return JSONResponse({"state": 0, "message": "Invalid request data"}, status_code=400)
    
    should_serve_result = await should_serve(decrypted_fields)
    if not should_serve_result:
        return JSONResponse({"state": 0, "message": "Access denied"}, status_code=403)
    
    user_info, device_info = await decrypt_fields_to_user_info(decrypted_fields)

    if user_info:
        my_stage, my_avatar = await get_user_entitlement_from_devices(user_info['id'])
    elif device_info:
        my_stage = device_info['my_stage']
        my_avatar = device_info['my_avatar']
    else:
        return JSONResponse({"state": 0, "message": "User and device not found"}, status_code=404)

    is_fmax_purchased = False
    is_extra_purchased = False

    stage_list = []
    stage_low_end = 100
    stage_high_end = 615

    stage_list = [
        stage_id for stage_id in range(stage_low_end, stage_high_end)
        if stage_id not in EXCLUDE_STAGE_EXP and stage_id not in my_stage
    ]

    avatar_list = []
    avatar_low_end = 15
    avatar_high_end = 173 if FMAX_VER == 0 else 267

    avatar_list = [
        avatar_id for avatar_id in range(avatar_low_end, avatar_high_end)
        if avatar_id not in my_avatar
    ]

    item_list = []
    item_low_end = 1
    item_high_end = 11

    item_list = [
        item_id for item_id in range(item_low_end, item_high_end)
    ]

    if 700 in my_stage and os.path.isfile('./files/4max_ver.txt'):
        is_fmax_purchased = True

    if 980 in my_stage and os.path.isfile('./files/4max_ver.txt'):
        is_extra_purchased = True

    payload = {
        "state": 1,
        "message": "Success",
        "data": {
            "coin": device_info['coin'],
            "stage_list": stage_list,
            "avatar_list": avatar_list,
            "item_list": item_list,
            "fmax_purchased": is_fmax_purchased,
            "extra_purchased": is_extra_purchased
        }
    }
    return JSONResponse(payload)

async def api_shop_item_data(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return JSONResponse({"state": 0, "message": "Invalid request data"}, status_code=400)
    
    should_serve_result = await should_serve(decrypted_fields)
    if not should_serve_result:
        return JSONResponse({"state": 0, "message": "Access denied"}, status_code=403)
    
    user_info, device_info = await decrypt_fields_to_user_info(decrypted_fields)
    if not device_info:
        return JSONResponse({"state": 0, "message": "Invalid device information"}, status_code=400)
    
    list_to_use = []

    post_data = await request.json()
    item_type = int(post_data.get("mode"))
    item_id = int(post_data.get("item_id"))

    list_to_use = []
    price = 0
    prop_first = ""
    prop_second = ""
    prop_third = ""

    if item_type == 0:
        list_to_use = SONG_LIST

    elif item_type == 1:
        list_to_use = AVATAR_LIST

    elif item_type == 2:
        list_to_use = ITEM_LIST

    item = next((item for item in list_to_use if item['id'] == item_id), None) if list_to_use else None

    if item or item_type in [3, 4]:
        if item_type == 0:
            price = STAGE_PRICE * 2 if len(item["difficulty_levels"]) == 6 else STAGE_PRICE
            prop_first = item['name_en']
            prop_second = item['author_en']
            prop_third = "/".join(map(str, item.get("difficulty_levels", [])))

        elif item_type == 1:
            prop_first = item['name']
            prop_second = item['effect']
            price = AVATAR_PRICE

        elif item_type == 2:
            prop_first = item['name']
            prop_second = item['effect']
            price = ITEM_PRICE

        elif item_type == 3:
            from api.misc import FMAX_VER, FMAX_RES
            log = parse_res(FMAX_RES)
            prop_first = FMAX_VER
            prop_second = log
            price = FMAX_PRICE

        elif item_type == 4:
            price = EX_PRICE

    if item or item_type in [3, 4]:
        payload = {
            "state": 1,
            "message": "Success",
            "data": {
                "price": price,
                "property_first": prop_first,
                "property_second": prop_second,
                "property_third": prop_third
            }
        }

    else:
        payload = {
            "state": 0,
            "message": "Item not found"
        }

    return JSONResponse(payload)

async def api_shop_purchase_item(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return JSONResponse({"state": 0, "message": "Invalid request data"}, status_code=400)
    
    should_serve_result = await should_serve(decrypted_fields)
    if not should_serve_result:
        return JSONResponse({"state": 0, "message": "Access denied"}, status_code=403)
    
    list_to_use = []

    post_data = await request.json()
    item_type = int(post_data.get("mode"))
    item_id = int(post_data.get("item_id"))

    price = 0
    list_to_use = []

    amount = 1 if item_type in [0, 1, 3, 4] else 10

    if item_type == 0:
        list_to_use = SONG_LIST

    elif item_type == 1:
        list_to_use = AVATAR_LIST

    elif item_type == 2:
        list_to_use = ITEM_LIST

    item = next((item for item in list_to_use if item['id'] == item_id), None) if list_to_use else None

    if item or item_type in [3, 4]:
        if item_type == 0:
            price = STAGE_PRICE * 2 if len(item["difficulty_levels"]) == 6 else STAGE_PRICE

        elif item_type == 1:
            price = AVATAR_PRICE

        elif item_type == 2:
            price = ITEM_PRICE

        elif item_type == 3:
            price = FMAX_PRICE

        elif item_type == 4:
            price = EX_PRICE

    if price == 0:
        payload = {
            "state": 0,
            "message": "Item not found"
        }

    else:
        user_info, device_info = await decrypt_fields_to_user_info(decrypted_fields)

        if user_info:
            my_stage, my_avatar = await get_user_entitlement_from_devices(user_info['id'])
        elif device_info:
            my_stage = device_info['my_stage']
            my_avatar = device_info['my_avatar']
        else:
            return JSONResponse({"state": 0, "message": "User and device not found"}, status_code=404)
        
        my_stage = set(my_stage)
        my_avatar = set(my_avatar)
        item_pending = device_info['item'] or []
        
        if item_type == 0 and item_id in my_stage:
            return JSONResponse({"state": 0, "message": "Stage already owned. Exit the shop and it will be added to the game."}, status_code=400)
        elif item_type == 1 and item_id in my_avatar:
            return JSONResponse({"state": 0, "message": "Avatar already owned. Exit the shop and it will be added to the game."}, status_code=400)
        elif item_type == 3 and 700 in my_stage:
            return JSONResponse({"state": 0, "message": "FMAX already owned. Exit the shop and it will be added to the game."}, status_code=400)
        elif item_type == 4 and 980 in my_stage:
            return JSONResponse({"state": 0, "message": "EXTRA already owned. Exit the shop and it will be added to the game."}, status_code=400)
        
        if price > device_info['coin']:
            return JSONResponse({"state": 0, "message": "Insufficient coins."}, status_code=400)
        
        new_coin_amount = device_info['coin'] - price

        if item_type == 0:
            my_stage.add(item_id)
        elif item_type == 1:
            my_avatar.add(item_id)
        elif item_type == 2:
            item_pending.append(item_id)

        elif item_type == 3:
            for i in range(615, 926):
                my_stage.add(i)

        elif item_type == 4:
            for i in range(926, 985):
                my_stage.add(i)

        update_data = {
            "coin": new_coin_amount,
            "my_stage": list(my_stage),
            "my_avatar": list(my_avatar),
            "item": item_pending
        }

        await set_device_data_using_decrypted_fields(decrypted_fields, update_data)

        payload = {
            "state": 1,
            "message": "Purchase successful.",
            "data": {
                "coin": new_coin_amount
            }
        }

    print(payload)

    return JSONResponse(payload)


routes = [
    Route('/web_shop.php', web_shop, methods=['GET', 'POST']),
    Route('/api/shop/player_data', api_shop_player_data, methods=['GET']),
    Route('/api/shop/item_data', api_shop_item_data, methods=['POST']),
    Route('/api/shop/purchase_item', api_shop_purchase_item, methods=['POST']),
]