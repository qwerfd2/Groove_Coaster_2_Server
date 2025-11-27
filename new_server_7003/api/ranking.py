from starlette.responses import HTMLResponse, JSONResponse
from starlette.requests import Request
from starlette.routing import Route
from sqlalchemy import select

from api.crypt import decrypt_fields
from api.misc import inform_page, should_serve, get_host_string, inform_page
from api.database import decrypt_fields_to_user_info, get_user_entitlement_from_devices, results_query, set_user_data_using_decrypted_fields, user_id_to_user_info_simple, accounts, player_database, write_rank_cache, get_rank_cache, set_device_data_using_decrypted_fields
from api.template import SONG_LIST, EXP_UNLOCKED_SONGS, TITLE_LISTS, SUM_TITLE_LIST

async def mission(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return inform_page("Invalid request data", 5)

    should_serve_result = await should_serve(decrypted_fields)

    if not should_serve_result:
        return inform_page("Access denied", 5)

    user_info, device_info = await decrypt_fields_to_user_info(decrypted_fields)
    if not device_info:
        return inform_page("Invalid device information", 4)

    html = f"""<div class="f90 a_center pt50">Play Music to level up and unlock free songs!<br>Songs can only be unlocked when you play online.</div><div class='mission-list'>"""

    for song in EXP_UNLOCKED_SONGS:
        song_id = song["id"]
        level_required = song["lvl"]
        song_name = SONG_LIST[song_id]["name_en"] if song_id < len(SONG_LIST) else "Unknown Song"

        html += f"""
            <div class="mission-row">
                <div class="mission-level">Level {level_required}</div>
                <div class="mission-song">{song_name}</div>
            </div>
        """

    html += "</div>"
    try:
        with open("web/mission.html", "r", encoding="utf-8") as file:
            html_content = file.read().format(text=html)
    except FileNotFoundError:
        return HTMLResponse("""<html><body><h1>Mission file not found</h1></body></html>""", status_code=500)

    return HTMLResponse(html_content)
        
    
async def status(request: Request):
    decrypted_fields, original_fields = await decrypt_fields(request)
    if not decrypted_fields:
        return inform_page("Invalid request data", 3)

    should_serve_result = await should_serve(decrypted_fields)

    if not should_serve_result:
        return inform_page("Access denied", 3)
    
    user_info, device_info = await decrypt_fields_to_user_info(decrypted_fields)
    if not device_info:
        return inform_page("Invalid device information", 4)

    try:
        with open("web/status.html", "r", encoding="utf-8") as file:
            html_content = file.read().format(host_url=await get_host_string(), payload=original_fields)
    except FileNotFoundError:
        return inform_page("Status page not found", 4)

    return HTMLResponse(html_content)

async def status_title_list(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return JSONResponse({"state": 0, "message": "Invalid request data"}, status_code=400)

    should_serve_result = await should_serve(decrypted_fields)

    if not should_serve_result:
        return JSONResponse({"state": 0, "message": "Access denied"}, status_code=403)

    user_info, device_info = await decrypt_fields_to_user_info(decrypted_fields)
    if not device_info:
        return JSONResponse({"state": 0, "message": "Invalid user information"}, status_code=400)

    username = user_info["username"] if user_info else "Guest"
    current_title = user_info["title"] if user_info else device_info['title']
    current_avatar = user_info["avatar"] if user_info else device_info['avatar']
    current_lvl = device_info['lvl']

    player_object = {
        "username": username,
        "title": current_title,
        "avatar": current_avatar,
        "lvl": current_lvl
    }

    payload = {
        "state": 1,
        "message": "Success",
        "data": {
            "title_list": TITLE_LISTS,
            "player_info": player_object
        }
    }

    return JSONResponse(payload)

async def set_title(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return JSONResponse({"state": 0, "message": "Invalid request data"}, status_code=400)

    should_serve_result = await should_serve(decrypted_fields)

    if not should_serve_result:
        return JSONResponse({"state": 0, "message": "Access denied"}, status_code=403)

    user_info, device_info = await decrypt_fields_to_user_info(decrypted_fields)
    if not device_info:
        return JSONResponse({"state": 0, "message": "Invalid user information"}, status_code=400)

    post_data = await request.json()
    new_title = int(post_data.get("title", -1))

    if new_title not in SUM_TITLE_LIST:
        return JSONResponse({"state": 0, "message": "Invalid title"}, status_code=400)
    
    update_data = {
        "title": new_title
    }

    if user_info:
        await set_user_data_using_decrypted_fields(decrypted_fields, update_data)
    
    await set_device_data_using_decrypted_fields(decrypted_fields, update_data)

    return JSONResponse({"state": 1, "message": "Title updated successfully"})


async def ranking(request: Request):
    decrypted_fields, original_fields = await decrypt_fields(request)
    if not decrypted_fields:
        return inform_page("Invalid request data", 4)

    should_serve_result = await should_serve(decrypted_fields)

    if not should_serve_result:
        return inform_page("Access denied", 4)
    
    user_info, device_info = await decrypt_fields_to_user_info(decrypted_fields)
    if not device_info:
        return inform_page("Invalid device information", 4)

    try:
        with open("web/ranking.html", "r", encoding="utf-8") as file:
            html_content = file.read().format(host_url=await get_host_string(), payload=original_fields)
    except FileNotFoundError:
        return inform_page("Ranking page not found", 4)

    return HTMLResponse(html_content)


async def user_song_list(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return JSONResponse({"state": 0, "message": "Invalid request data"}, status_code=400)
    
    should_serve_result = await should_serve(decrypted_fields)
    if not should_serve_result:
        return JSONResponse({"state": 0, "message": "Access denied"}, status_code=403)

    user_info, device_info = await decrypt_fields_to_user_info(decrypted_fields)

    my_stage = []
    if user_info:
        my_stage, _ = await get_user_entitlement_from_devices(user_info["id"])
    elif device_info:
        my_stage = device_info['my_stage']

    payload = {
        "state": 1,
        "message": "Success",
        "data": {
            "song_list": SONG_LIST,
            "my_stage": my_stage
        }
    }
    return JSONResponse(payload)

async def user_ranking_individual(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return JSONResponse({"state": 0, "message": "Invalid request data"}, status_code=400)
    
    should_serve_result = await should_serve(decrypted_fields)
    if not should_serve_result:
        return JSONResponse({"state": 0, "message": "Access denied"}, status_code=403)

    user_info, device_info = await decrypt_fields_to_user_info(decrypted_fields)
    if not device_info:
        return JSONResponse({"state": 0, "message": "Invalid device information"}, status_code=400)

    post_data = await request.json()
    song_id = int(post_data.get("song_id", -1))
    mode = int(post_data.get("mode", -1))
    page_number = int(post_data.get("page", 0))
    page_count = 50

    if song_id not in range(0, 1000) or mode not in [1, 2, 3, 11, 12, 13]:
        return JSONResponse({"state": 0, "message": "Invalid song_id or mode"}, status_code=400)

    user_id = user_info["id"] if user_info else None

    total_count = 0
    ranking_list = []
    player_ranking = {"username": user_info["username"] if user_info else "Guest (Not Ranked)", "score": 0, "position": -1, "title": user_info["title"] if user_info else device_info['title'], "avatar": device_info["avatar"]}

    cache_key = f"{str(song_id)}-{str(mode)}"
    cached_data = await get_rank_cache(cache_key)

    if cached_data:
        records = cached_data
    else:
        query_param = {
            "song_id": song_id,
            "mode": mode
        }
        records = await results_query(query_param)
        await write_rank_cache(cache_key, records)

    total_count = len(records)
    for index, record in enumerate(records):
        if index >= page_number * page_count and index < (page_number + 1) * page_count:
            rank_user = await user_id_to_user_info_simple(record["user_id"])
            if rank_user:
                ranking_list.append({
                    "position": index + 1,
                    "username": rank_user["username"],
                    "score": record["score"],
                    "title": rank_user["title"],
                    "avatar": record["avatar"]
                })
        if user_id and record["user_id"] == user_id:
            player_ranking = {
                "username": user_info["username"],
                "score": record["score"],
                "position": index + 1,
                "title": user_info["title"],
                "avatar": user_info["avatar"]
            }

    payload = {
        "state": 1,
        "message": "Success",
        "data": {
            "ranking_list": ranking_list,
            "player_ranking": player_ranking,
            "total_count": total_count
        }
    }

    return JSONResponse(payload)

async def user_ranking_total(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return JSONResponse({"state": 0, "message": "Invalid request data"}, status_code=400)
    
    should_serve_result = await should_serve(decrypted_fields)
    if not should_serve_result:
        return JSONResponse({"state": 0, "message": "Access denied"}, status_code=403)

    user_info, device_info = await decrypt_fields_to_user_info(decrypted_fields)

    if not device_info:
        return JSONResponse({"state": 0, "message": "Invalid device information"}, status_code=400)

    post_data = await request.json()
    mode = int(post_data.get("mode", -1))
    page_number = int(post_data.get("page", 0))
    page_count = 50

    if mode not in [0, 1, 2]:
        return JSONResponse({"state": 0, "message": "Invalid mode"}, status_code=400)

    user_id = user_info["id"] if user_info else None
    
    total_count = 0
    ranking_list = []
    player_ranking = {"username": user_info["username"] if user_info else "Guest (Not Ranked)", "score": 0, "position": -1, "title": user_info["title"] if user_info else device_info['title'], "avatar": device_info["avatar"]}

    score_obj = ["total_delta", "mobile_delta", "arcade_delta"]

    cache_key = f"0-{str(mode)}"
    cached_data = await get_rank_cache(cache_key)
    if cached_data:
        records = cached_data
    else:

        query = select(
            accounts.c.id,
            accounts.c.username,
            accounts.c[score_obj[mode]],
            accounts.c.title,
            accounts.c.avatar,
        ).where(
            accounts.c[score_obj[mode]] > 0
        ).order_by(
            accounts.c[score_obj[mode]].desc()
        )

        records = await player_database.fetch_all(query)
        records = [dict(record) for record in records]
        await write_rank_cache(cache_key, records, expire_seconds=120)

    total_count = len(records)
    for index, record in enumerate(records):
        if index >= page_number * page_count and index < (page_number + 1) * page_count:
            rank_user = await user_id_to_user_info_simple(record["id"])
            if rank_user:
                ranking_list.append({
                    "position": index + 1,
                    "username": rank_user["username"],
                    "score": record[score_obj[mode]],
                    "title": rank_user["title"],
                    "avatar": record["avatar"]
                })
        if user_id and record["id"] == user_id:
            player_ranking = {
                "username": user_info["username"],
                "score": record[score_obj[mode]],
                "position": index + 1,
                "title": user_info["title"],
                "avatar": user_info["avatar"]
            }

    payload = {
        "state": 1,
        "message": "Success",
        "data": {
            "ranking_list": ranking_list,
            "player_ranking": player_ranking,
            "total_count": total_count
        }
    }

    return JSONResponse(payload)

routes = [
    Route('/mission.php', mission, methods=['GET']),
    Route('/status.php', status, methods=['GET']),
    Route('/api/status/title_list', status_title_list, methods=['GET']),
    Route('/api/status/set_title', set_title, methods=['POST']),
    Route('/ranking.php', ranking, methods=['GET']),
    Route('/api/ranking/song_list', user_song_list, methods=['GET']),
    Route('/api/ranking/individual', user_ranking_individual, methods=['POST']),
    Route('/api/ranking/total', user_ranking_total, methods=['POST'])
]