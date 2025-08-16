from starlette.responses import Response, FileResponse, HTMLResponse
from starlette.requests import Request
from starlette.routing import Route
import os
import json
import math
from sqlalchemy import select, update
import xml.etree.ElementTree as ET

from config import START_COIN, AUTHORIZATION_NEEDED, STAGE_PRICE, START_COIN, AVATAR_PRICE, ITEM_PRICE, FMAX_PRICE, EX_PRICE

from api.crypt import decrypt_fields
from api.misc import inform_page, parse_res, FMAX_VER, FMAX_RES
from api.database import database, daily_reward, check_blacklist, check_whitelist
from api.templates import START_AVATARS, START_STAGES, EXCLUDE_STAGE_EXP, SONG_LIST, AVATAR_LIST, ITEM_LIST

async def web_shop(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return HTMLResponse("""<html><body><h1>Invalid request data</h1></body></html>""", status_code=400)

    should_serve = True
    if AUTHORIZATION_NEEDED:
        should_serve = await check_whitelist(decrypted_fields) and not await check_blacklist(decrypted_fields)

    if should_serve:
        cnt_type = decrypted_fields[b'cnt_type'][0].decode()
        device_id = decrypted_fields[b'vid'][0].decode()
        if (decrypted_fields.get(b'page')):
            page = int(decrypted_fields.get(b'page')[0].decode())
        else:
            page = 0

        inc = 0
        fmax_inc = 0
        buttons_html = ""
        spawn_prev_page = False
        spawn_next_page = False

        query = select(daily_reward.c.my_stage, daily_reward.c.my_avatar, daily_reward.c.coin).where(daily_reward.c.device_id == device_id)
        result = await database.fetch_one(query)

        my_stage = set(json.loads(result["my_stage"])) if result and result["my_stage"] else START_STAGES
        my_avatar = set(json.loads(result["my_avatar"])) if result and result["my_avatar"] else START_AVATARS
        coin = result["coin"] if result and result["coin"] else START_COIN

        if cnt_type == "1":
            low_range = 100
            up_range = 615

            if page < 0 or page > math.ceil(up_range - low_range) / 80:
                return HTMLResponse("""<html><body><h1>Invalid page number</h1></body></html>""", status_code=400)
            
            if page > 0:
                spawn_prev_page = True
            if page < math.ceil(up_range - low_range) / 80 - 1:
                spawn_next_page = True

            low_range = low_range + page * 80
            up_range = min(up_range, low_range + 80)

            if 700 not in my_stage and os.path.isfile('./files/dlc_4max.html') and not spawn_prev_page:
                buttons_html += """
                    <a href="wwic://web_shop_detail?&cnt_type=1&cnt_id=-1">
                        <img src="/files/web/dlc_4max.jpg" style="width: 84%; margin-bottom: 110px; margin-top: -100px;" />
                    </a><br>
                """
                fmax_inc = 1
            elif 700 in my_stage and os.path.isfile('./files/dlc_4max.html') and not spawn_prev_page:
                buttons_html += """
                    <a href="wwic://web_shop_detail?&cnt_type=1&cnt_id=-3">
                        <img src="/files/web/dlc_4max.jpg" style="width: 84%; margin-bottom: 110px; margin-top: -100px;" />
                    </a><br>
                """

            if 980 not in my_stage and os.path.isfile('./files/dlc_extra.html') and not spawn_prev_page:
                buttons_html += """
                    <a href="wwic://web_shop_detail?&cnt_type=1&cnt_id=-2">
                        <img src="/files/web/dlc_extra.jpg" style="width: 84%; margin-bottom: 20px; margin-top: -100px;" />
                    </a><br>
                """
                fmax_inc = 1
            elif 980 in my_stage and os.path.isfile('./files/dlc_4max.html') and not spawn_prev_page:
                buttons_html += """
                    <a href="wwic://web_shop_detail?&cnt_type=1&cnt_id=-4">
                        <img src="/files/web/dlc_extra.jpg" style="width: 84%; margin-bottom: 20px; margin-top: -100px;" />
                    </a><br>
                """

            for i in range(low_range, up_range):
                if i not in my_stage and i not in EXCLUDE_STAGE_EXP:
                    buttons_html += f"""
                        <button style="width: 170px; height: 170px; margin: 10px; background-size: cover; background-image: url('/files/image/icon/shop/{i}.jpg');"
                                onclick="window.location.href='wwic://web_shop_detail?&cnt_type={cnt_type}&cnt_id={i}'">
                        </button>
                    """
                    inc += 1
                    if inc % 4 == 0:
                        buttons_html += "<br>"

            if spawn_prev_page:
                buttons_html += """<br>
                    <button style="width: 170px; height: 40px; margin: 10px; background-color: #000000; color: #FFFFFF;"
                            onclick="window.location.href='wwic://web_shop?&cnt_type=1&page={}'">
                        Prev Page
                    </button>
                """.format(page - 1)

            if spawn_next_page:
                buttons_html += """<br>
                    <button style="width: 170px; height: 40px; margin: 10px; background-color: #000000; color: #FFFFFF;"
                            onclick="window.location.href='wwic://web_shop?&cnt_type=1&page={}'">
                        Next Page
                    </button>
                """.format(page + 1)

        elif cnt_type == "2":
            low_range = 15
            up_range = 173 if FMAX_VER == 0 else 267

            if page < 0 or page > math.ceil(up_range - low_range) / 80:
                return HTMLResponse("""<html><body><h1>Invalid page number</h1></body></html>""", status_code=400)
            
            if page > 0:
                spawn_prev_page = True
            if page < math.ceil(up_range - low_range) / 80 - 1:
                spawn_next_page = True

            low_range = low_range + page * 80
            up_range = min(up_range, low_range + 80)

            for i in range(low_range, up_range):
                if i not in my_avatar and i not in EXCLUDE_STAGE_EXP:
                    buttons_html += f"""
                        <button style="width: 170px; height: 170px; margin: 10px; background-color: black; background-size: contain; background-repeat: no-repeat; background-position: center center; background-image: url('/files/image/icon/avatar/{i}.png');"
                                onclick="window.location.href='wwic://web_shop_detail?&cnt_type={cnt_type}&cnt_id={i}'">
                        </button>
                    """
                    inc += 1
                    if inc % 4 == 0:
                        buttons_html += "<br>"

            if spawn_prev_page:
                buttons_html += """<br>
                    <button style="width: 170px; height: 40px; margin: 10px; background-color: #000000; color: #FFFFFF;"
                            onclick="window.location.href='wwic://web_shop?&cnt_type=2&page={}'">
                        Prev Page
                    </button>
                """.format(page - 1)

            if spawn_next_page:
                buttons_html += """<br>
                    <button style="width: 170px; height: 40px; margin: 10px; background-color: #000000; color: #FFFFFF;"
                            onclick="window.location.href='wwic://web_shop?&cnt_type=2&page={}'">
                        Next Page
                    </button>
                """.format(page + 1)

        elif cnt_type == "3":
            for i in range(1, 11):
                buttons_html += f"""
                    <button style="width: 170px; height: 170px; margin: 10px; background-size: cover; background-image: url('/files/image/icon/item/{i}.png');"
                            onclick="window.location.href='wwic://web_shop_detail?&cnt_type={cnt_type}&cnt_id={i}'">
                    </button>
                """
                if i % 4 == 0:
                    buttons_html += "<br>"

        if inc == 0 and fmax_inc == 0 and cnt_type != "3":
            buttons_html += """<div>Everything has been purchased!</div>"""

        html_path = f"files/web_shop_{cnt_type}.html"
        try:
            with open(html_path, "r", encoding="utf-8") as file:
                html_content = file.read().format(text=buttons_html, coin=coin)
        except FileNotFoundError:
            return HTMLResponse("""<html><body><h1>Shop template not found</h1></body></html>""", status_code=500)

        return HTMLResponse(html_content)
    else:
        return HTMLResponse("""<html><body><h1>Access denied</h1></body></html>""", status_code=403)
    
async def web_shop_detail(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return HTMLResponse("""<html><body><h1>Invalid request data</h1></body></html>""", status_code=400)

    should_serve = True
    if AUTHORIZATION_NEEDED:
        should_serve = await check_whitelist(decrypted_fields) and not await check_blacklist(decrypted_fields)

    if should_serve:
        cnt_type = decrypted_fields[b'cnt_type'][0].decode()
        cnt_id = int(decrypted_fields[b'cnt_id'][0].decode())
        device_id = decrypted_fields[b'vid'][0].decode()

        query = select(daily_reward.c.coin).where(daily_reward.c.device_id == device_id)
        result = await database.fetch_one(query)
        coin = result["coin"] if result and result["coin"] else 0
        html = ""

        if cnt_type == "1":
            if cnt_id > -1:
                song = SONG_LIST[cnt_id]
                difficulty_levels = "/".join(map(str, song.get("difficulty_levels", [])))
                song_stage_price = STAGE_PRICE * 2 if len(song["difficulty_levels"]) == 6 else STAGE_PRICE
                html = f"""
                <div class="image-container">
                    <img src="/files/image/icon/shop/{cnt_id}.jpg" alt="Item Image" style="width: 180px; height: 180px;" />
                </div>
                <p>Would you like to purchase this song?</p>
                <div>
                    <p>{song.get("name_en")} - {song.get("author_en")}</p>
                    <p>Difficulty Levels: {difficulty_levels}</p>
                </div>
                <div>
                    <img src="/files/web/coin_icon.png" class="coin-icon" style="width: 40px; height: 40px;" alt="Coin Icon" />
                    <span style="color: #FFFFFF; font-size: 44px; font-family: Hiragino Kaku Gothic ProN, sans-serif;">{song_stage_price}</span>
                </div>
                """
            elif cnt_id == -3:
                log = parse_res(FMAX_RES)
                html = f"""
                    <div class="text-content">
                        <p>You have unlocked the GC4MAX expansion!</p>
                        <p>Please report bugs/missing tracks to Discord: #AnTcfgss, or QQ 3421587952.</p>
                        <button class="quit-button" onclick="window.location.href='wwic://web_shop?&cnt_type=1'">
                            Go Back
                        </button><br>
                        <strong>This server has version {FMAX_VER}.</strong>
                        <p>Update log: </p>
                        <p>{log}<p><br>
                    </div>
                """
            elif cnt_id == -4:
                html = f"""
                    <div class="text-content">
                        <p>You have unlocked the EXTRA Challenge!</p>
                        <p>Please report bugs/missing tracks to Discord: #AnTcfgss, or QQ 3421587952.</p>
                        <button class="quit-button-extra" onclick="window.location.href='wwic://web_shop?&cnt_type=1'">
                            Go Back
                        </button>
                    </div>
                """
            elif cnt_id == -2:
                html = f"""
                    <div class="text-content">
                        <p>Brace the Ultimate - Extra - Challenge.</p>
                        <p>170+ Arcade Extra difficulty charts await you.</p>
                        <p>You have been warned.</p>
                    </div>

                    <button class="buy-button-extra" onclick="window.location.href='wwic://web_purchase_coin?&cnt_type=1&cnt_id=-2&num=1'">
                        Buy
                        <div class="coin-container">
                        <img src="/files/web/coin_icon.png" alt="Coin Icon" class="coin-icon">
                        <span style="font-size: 22px; font-weight: bold;"> {EX_PRICE}</span>
                        </div>
                    </button>
                    <br><br>
                    <button class="quit-button-extra" onclick="window.location.href='wwic://web_shop?&cnt_type=1'">
                        Go Back
                    </button>
                """
            elif cnt_id == -1:
                html = f"""
                    <div class="text-content">
                        <p>Experience the arcade with the GC4MAX expansion! This DLC unlocks 320+ exclusive songs for your 2OS experience.</p>
                        <p>Note that these songs don't have mobile difficulties. A short placeholder is used, and GCoin reward is not available for playing them. You must clear the Normal difficulty to unlock AC content.</p>
                        <p>Due to technical limitations, Extra level charts cannot be ported as of now. After purchasing, you will have access to support information and update logs.</p>
                    </div>

                    <button class="buy-button" onclick="window.location.href='wwic://web_purchase_coin?&cnt_type=1&cnt_id=-1&num=1'">
                        Buy
                        <div class="coin-container">
                        <img src="/files/web/coin_icon.png" alt="Coin Icon" class="coin-icon">
                        <span style="font-size: 22px; font-weight: bold;"> {FMAX_PRICE}</span>
                        </div>
                    </button>
                    <br><br>
                    <button class="quit-button" onclick="window.location.href='wwic://web_shop?&cnt_type=1'">
                        Go Back
                    </button>
                """

        elif cnt_type == "2":
            avatar = next((item for item in AVATAR_LIST if item.get("id") == cnt_id), None)
            if avatar:
                html = f"""
                <div class="image-container">
                    <img src="/files/image/icon/avatar/{cnt_id}.png" alt="Item Image" style="width: 180px; height: 180px; background-color: black; object-fit: contain;" />
                </div>
                <p>Would you like to purchase this avatar?</p>
                <div>
                    <p>{avatar.get("name")}</p>
                    <p>Effect: {avatar.get("effect")}</p>
                </div>
                <div>
                    <img src="/files/web/coin_icon.png" class="coin-icon" style="width: 40px; height: 40px;" alt="Coin Icon" />
                    <span>{AVATAR_PRICE}</span>
                </div>
                """
            else:
                html = "<p>Avatar not found.</p>"

        elif cnt_type == "3":
            item = next((item for item in ITEM_LIST if item.get("id") == cnt_id), None)
            if item:
                html = f"""
                <div class="image-container">
                    <img src="/files/image/icon/item/{cnt_id}.png" alt="Item Image" style="width: 180px; height: 180px;" />
                </div>
                <p>Would you like to purchase this item?</p>
                <div>
                    <p>{item.get("name")}</p>
                    <p>Effect: {item.get("effect")}</p>
                </div>
                <div>
                    <img src="/files/web/coin_icon.png" class="coin-icon" style="width: 40px; height: 40px;" alt="Coin Icon" />
                    <span>{ITEM_PRICE}</span>
                </div>
                """
            else:
                html = "<p>Item not found.</p>"

        if cnt_type == "1" and (cnt_id == -1 or cnt_id == -3):
            source_html = f"files/dlc_4max.html"
        elif cnt_type == "1" and (cnt_id == -2 or cnt_id == -4):
            source_html = f"files/dlc_extra.html"
        else:
            source_html = f"files/web_shop_detail.html"
            html += f"""
                <br>
                <div class="buttons" style="margin-top: 20px;">
                    <a href="wwic://web_purchase_coin?cnt_type={cnt_type}&cnt_id={cnt_id}&num=1" class="bt_bg01" >Buy</a><br>
                    <a href="wwic://web_shop?cnt_type={cnt_type}" class="bt_bg01" >Go Back</a>
                </div>
            """

        try:
            with open(source_html, "r", encoding="utf-8") as file:
                html_content = file.read().format(text=html, coin=coin)
        except FileNotFoundError:
            return HTMLResponse("""<html><body><h1>Shop detail template not found</h1></body></html>""", status_code=500)

        return HTMLResponse(html_content)
    else:
        return HTMLResponse("""<html><body><h1>Access denied</h1></body></html>""", status_code=403)

async def buy_by_coin(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return Response("""<?xml version="1.0" encoding="UTF-8"?><response><code>1</code><result_url>coin_error.php</result_url></response>""", media_type="application/xml")

    should_serve = True
    if AUTHORIZATION_NEEDED:
        should_serve = await check_whitelist(decrypted_fields) and not await check_blacklist(decrypted_fields)

    if should_serve:
        cnt_type = decrypted_fields[b'cnt_type'][0].decode()
        cnt_id = int(decrypted_fields[b'cnt_id'][0].decode())
        num = int(decrypted_fields[b'num'][0].decode())
        device_id = decrypted_fields[b'vid'][0].decode()

        fail_url = """<?xml version="1.0" encoding="UTF-8"?><response><code>1</code><result_url>coin_error.php</result_url></response>"""

        query = select(daily_reward.c.my_stage, daily_reward.c.my_avatar, daily_reward.c.coin, daily_reward.c.item).where(daily_reward.c.device_id == device_id)
        result = await database.fetch_one(query)

        if not result:
            return Response(fail_url, media_type="application/xml")

        my_stage = set(json.loads(result["my_stage"])) if result["my_stage"] else set()
        my_avatar = set(json.loads(result["my_avatar"])) if result["my_avatar"] else set()
        coin = int(result["coin"]) if result["coin"] else 0
        item = json.loads(result["item"]) if result["item"] else []

        if cnt_type == "1":
            if cnt_id == -1:
                song_stage_price = FMAX_PRICE
                if coin < song_stage_price:
                    return Response(fail_url, media_type="application/xml")

                for i in range(615, 926):
                    my_stage.add(i)
                coin -= song_stage_price
            elif cnt_id == -2:
                song_stage_price = EX_PRICE
                if coin < song_stage_price:
                    return Response(fail_url, media_type="application/xml")

                for i in range(926, 985):
                    my_stage.add(i)
                coin -= song_stage_price
            else:
                song_stage_price = STAGE_PRICE * 2 if len(SONG_LIST[cnt_id]["difficulty_levels"]) == 6 else STAGE_PRICE
                if coin < song_stage_price or cnt_id in my_stage:
                    return Response(fail_url, media_type="application/xml")

                coin -= song_stage_price
                my_stage.add(cnt_id)

        elif cnt_type == "2":
            if coin < AVATAR_PRICE or cnt_id in my_avatar:
                return Response(fail_url, media_type="application/xml")

            coin -= AVATAR_PRICE
            my_avatar.add(cnt_id)

        elif cnt_type == "3":
            if coin < ITEM_PRICE:
                return Response(fail_url, media_type="application/xml")

            coin -= ITEM_PRICE
            item.append(cnt_id)

        else:
            return Response(fail_url, media_type="application/xml")

        update_query = (
            update(daily_reward)
            .where(daily_reward.c.device_id == device_id)
            .values(
                my_stage=json.dumps(list(my_stage)),
                my_avatar=json.dumps(list(my_avatar)),
                coin=coin,
                item=json.dumps(item)
            )
        )
        await database.execute(update_query)

        response = ET.Element("response")
        ET.SubElement(response, "code").text = "0"
        ET.SubElement(response, "result_url").text = "web_shop_result.php"
        ET.SubElement(response, "cnt_type").text = cnt_type
        ET.SubElement(response, "cnt_id").text = str(cnt_id)
        ET.SubElement(response, "num").text = str(num)

        if cnt_type == "1":
            ET.SubElement(response, "stage_id").text = str(cnt_id)

        response_string = ET.tostring(response, encoding="utf-8", method="xml").decode("utf-8")
        return Response(response_string, media_type="application/xml")
    else:
        return Response("""<?xml version="1.0" encoding="UTF-8"?><response><code>1</code><result_url>coin_error.php</result_url></response>""", media_type="application/xml")
    
async def web_shop_result(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    cnt_type = decrypted_fields[b'cnt_type'][0].decode()
    return HTMLResponse(inform_page(f"""SUCCESS:<br>Purchase successful.<br>Please close this page and the reward will arrive shortly.<br>If it took too long, try restarting the game.<br><a href='wwic://web_shop?cnt_type={cnt_type}' class='bt_bg01' >Go Back</a>""", 2))

async def coin_error(request: Request):
    return HTMLResponse(inform_page(f"""FAILED:<br>Either you don't have enough coin,<br>or there were a duplicate order, and the reward will arrive shortly.""", 2))


routes = [
    Route('/web_shop.php', web_shop, methods=['GET', 'POST']),
    Route('/web_shop_detail.php', web_shop_detail, methods=['GET', 'POST']),
    Route('/buy_by_coin.php', buy_by_coin, methods=['GET']),
    Route('/web_shop_result.php', web_shop_result, methods=['GET']),
    Route('/coin_error.php', coin_error, methods=['GET']),
]