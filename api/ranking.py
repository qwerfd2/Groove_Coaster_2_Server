from starlette.responses import HTMLResponse
from starlette.requests import Request
from starlette.routing import Route
import os
import json
from sqlalchemy import select, update

from config import AUTHORIZATION_NEEDED, USE_REDIS_CACHE

import api.database
from api.crypt import decrypt_fields, encryptAES
from api.templates import EXP_UNLOCKED_SONGS, TITLE_LISTS, SONG_LIST
from api.misc import inform_page

async def ranking(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return HTMLResponse("""<html><body><h1>Invalid request data</h1></body></html>""", status_code=400)

    should_serve = True
    if AUTHORIZATION_NEEDED:
        should_serve = await api.database.check_whitelist(decrypted_fields) and not await api.database.check_blacklist(decrypted_fields)

    if should_serve:
        device_id = decrypted_fields[b'vid'][0].decode()

        html = "<ul class='song-list'>"
        encrypted_mass = encryptAES(("vid=" + device_id + "&song_id=-1&mode=1&dummy=").encode("utf-8"))
        href = f"/ranking_detail.php?{encrypted_mass}"
        html += f'''
            <li class="song-item">
                <a href="{href}" class="song-button">Total Score</a>
            </li>
        '''
        for index, song in enumerate(SONG_LIST):
            encrypted_mass = encryptAES(("vid=" + device_id + "&song_id=" + str(index) + "&mode=3&dummy=").encode("utf-8"))
            song_name = song.get("name_en", "Unknown")
            href = f"/ranking_detail.php?{encrypted_mass}"
            html += f'''
                <li class="song-item">
                    <a href="{href}" class="song-button">{song_name}</a>
                </li>
            '''
        html += "</ul>"

        file_path = os.path.join("files", "ranking.html")
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                html_content = file.read().format(text=html)
        except FileNotFoundError:
            return HTMLResponse("""<html><body><h1>Ranking file not found</h1></body></html>""", status_code=500)

        return HTMLResponse(html_content)
    else:
        return HTMLResponse("""<html><body><h1>Access denied</h1></body></html>""", status_code=403)

async def ranking_detail(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return HTMLResponse("""<html><body><h1>Invalid request data</h1></body></html>""", status_code=400)

    should_serve = True
    if AUTHORIZATION_NEEDED:
        should_serve = await api.database.check_whitelist(decrypted_fields) and not await api.database.check_blacklist(decrypted_fields)

    if should_serve:
        device_id = decrypted_fields[b'vid'][0].decode()
        song_id = int(decrypted_fields[b'song_id'][0].decode())
        mode = int(decrypted_fields[b'mode'][0].decode())
        button_labels = []
        difficulty_levels = []
        song_name = ""
        if (song_id == -1):
            song_name = "Total Score"
            difficulty_levels = []
            button_labels = ["All", "Mobile", "Arcade"]
        else:
            song_name = SONG_LIST[song_id]["name_en"]
            difficulty_levels = SONG_LIST[song_id]["difficulty_levels"]
            button_labels = ["Easy", "Normal", "Hard"]

        html = f"""<div style="text-align: center; font-size: 36px; margin-bottom: 20px;">{song_name}</div>"""

        button_modes = [1, 2, 3]

        if (len(difficulty_levels) == 6):
            button_labels.extend(["AC-Easy", "AC-Normal", "AC-Hard"])
            button_modes.extend([11, 12, 13])

        if song_id > 615:
            button_modes = [x for x in button_modes if x not in [1, 2, 3]]
            button_labels = [x for x in button_labels if x not in ["Easy", "Normal", "Hard"]]

        row_start = '<div class="button-row">'
        row_end = '</div>'
        row_content = []

        for i, (label, mode_value) in enumerate(zip(button_labels, button_modes)):
            if mode_value == mode:
                row_content.append(f"""<div class="bt_bg01_ac">{label}</div>""")
            else:
                encrypted_mass = encryptAES(("vid=" + device_id + "&song_id=" + str(song_id) + "&mode=" + str(mode_value) + "&dummy=").encode("utf-8"))
                row_content.append(f"""<a href="/ranking_detail.php?{encrypted_mass}" class="bt_bg01_xnarrow">{label}</a>""")

            if len(row_content) == 3:
                html += row_start + ''.join(row_content) + row_end
                row_content = []  # Reset row content

        play_results = None
        user_result = None
        device_result = None
        if USE_REDIS_CACHE:
            cache_key = f"{song_id}-{mode}"
            cached = await api.database.redis.get(cache_key)
        else:
            cached = False

        if (song_id == -1):
            # Filter out the mobile/AC modes
            if (mode == 1):
                exclude = []
            elif mode == 2:
                exclude = [11, 12, 13]
            else:
                exclude = [1, 2, 3]

            
            if cached and USE_REDIS_CACHE:
                sorted_players = json.loads(cached)

            else:
                query = select(api.database.result.c.vid, api.database.result.c.sid, api.database.result.c.mode, api.database.result.c.avatar, api.database.result.c.score)
                play_results = await api.database.database.fetch_all(query)

                query = select(api.database.daily_reward.c.device_id, api.database.daily_reward.c.title, api.database.daily_reward.c.avatar)
                device_results_raw = await api.database.database.fetch_all(query)
                device_results = {row["device_id"]: {"title": row["title"], "avatar": row["avatar"]} for row in device_results_raw}

                query = select(api.database.user.c.id, api.database.user.c.username, api.database.user.c.device_id)
                user_results_raw = await api.database.database.fetch_all(query)
                user_results = {row["id"]: {"username": row["username"], "device_id": row["device_id"]} for row in user_results_raw}
                
                query = select(api.database.user).where(api.database.user.c.device_id == device_id)
                cur_user = await api.database.database.fetch_one(query)

                player_scores = {}

                filtered_play_results = [play for play in play_results if int(play[2]) not in exclude]

                for play in filtered_play_results:
                    did = play[0]
                    sid = play[1]
                    avatar = play[3]
                    score = play[4]
                    username, title = None, None

                    if sid:
                        sid = int(sid)
                        if sid in user_results:
                            username = user_results[sid]["username"]
                            did = user_results[sid]["device_id"]
                    else:  # Guest
                        username = f"Guest({did[-6:]})"

                    # title is device-specific
                    title = device_results.get(did, {}).get("title", "1")

                    if username in player_scores:
                        player_scores[username]["score"] += int(score)
                        player_scores[username]["avatar"] = avatar  # But avatar is based on latest play submission
                        player_scores[username]["title"] = title
                    else:
                        player_scores[username] = {"score": int(score), "avatar": avatar, "title": title}

                sorted_players = sorted(player_scores.items(), key=lambda x: x[1]["score"], reverse=True)
                if USE_REDIS_CACHE:
                    await api.database.redis.set(cache_key, json.dumps(sorted_players), ex=300)

            username = cur_user[1] if cur_user else f"Guest({device_id[-6:]})"

            player_rank = None
            user_score = 0
            avatar = "1"
            title = "1"

            for rank, (player_name, data) in enumerate(sorted_players, start=1):
                if player_name == username:
                    player_rank = rank
                    user_score = data["score"]
                    avatar = data["avatar"]
                    title = data["title"]
                    break

            if player_rank is None:
                device_data = next((device for device in device_results if device[1] == device_id), None)
                if device_data:
                    avatar = device_data["avatar"]
                    title = device_data["title"]

            html += f"""
            <div class="player-element">
                <span class="rank">You<br>{"#" + str(player_rank) if player_rank else "N/A"}</span>
                <img src="/files/image/icon/avatar/{avatar}.png" class="avatar" alt="Player Avatar">
                <div class="player-info">
                    <div class="name">{username}</div>
                    <img src="/files/image/title/{title}.png" class="title" alt="Player Title">
                </div>
                <div class="player-score">{user_score}</div>
            </div>
            """

            html += """
            <div class="leaderboard-container">
            """
            # Loop leaderboard
            for rank, (username, data) in enumerate(sorted_players, start=1):
                html += f"""
                <div class="leaderboard-player">
                    <div class="rank">#{rank}</div>
                    <img class="avatar" src="/files/image/icon/avatar/{data['avatar']}.png" alt="Avatar">
                    <div class="leaderboard-info">
                        <div class="name">{username}</div>
                        <div class="title"><img src="/files/image/title/{data['title']}.png" alt="Title"></div>
                    </div>
                    <div class="leaderboard-score">{data['score']}</div>
                </div>
                """

        else:
            if cached and USE_REDIS_CACHE:
                play_results = json.loads(cached)

            else:
                query = select(api.database.result).where((api.database.result.c.id == song_id) & (api.database.result.c.mode == mode))
                play_results = await api.database.database.fetch_all(query)
                play_results = sorted(play_results, key=lambda x: int(x[8]), reverse=True)
                if USE_REDIS_CACHE:
                    await api.database.redis.set(cache_key, json.dumps(play_results), ex=300)

            query = select(api.database.user).where(api.database.user.c.device_id == device_id)
            user_result = await api.database.database.fetch_one(query)

            query = select(api.database.daily_reward).where(api.database.daily_reward.c.device_id == device_id)
            device_result = await api.database.database.fetch_one(query)

            user_id = user_result[0] if user_result else None
            username = user_result[1] if user_result else f"Guest({device_id[-6:]})"
            play_record = None

            if user_id:
                play_record = next((record for record in play_results if int(record[3]) == user_id), None)

            if not play_record:
                play_record = next((record for record in play_results if record[1] == device_id and record[3] is None), None)

            player_rank = None
            avatar_index = str(play_record[7]) if play_record else "1"
            user_score = play_record[8] if play_record else 0
            for rank, result_obj in enumerate(play_results, start=1):
                if user_result and int(result_obj[3]) == user_id:
                    player_rank = rank
                    break
                elif result_obj[1] == device_id and result_obj[3] is None:
                    player_rank = rank
                    break

            html += f"""
            <div class="player-element">
                <span class="rank">You<br>{"#" + str(player_rank) if player_rank else "N/A"}</span>
                <img src="/files/image/icon/avatar/{avatar_index}.png" class="avatar" alt="Player Avatar">
                <div class="player-info">
                    <div class="name">{username}</div>
                    <img src="/files/image/title/{device_result[9]}.png" class="title" alt="Player Title">
                </div>
                <div class="player-score">{user_score}</div>
            </div>
            """

            html += """
            <div class="leaderboard-container">
            """

            for rank, record in enumerate(play_results, start=1):
                username = f"Guest({record[1][-6:]})"
                device_info = None
                if record[3]:
                    query = select(api.database.user.c.username).where(api.database.user.c.id == record[3])
                    user_data = await api.database.database.fetch_one(query)
                    if user_data:
                        username = user_data["username"]

                    query = select(api.database.daily_reward.c.title).where(api.database.daily_reward.c.device_id == record[1])
                    device_title = await api.database.database.fetch_one(query)
                    if device_title:
                        device_info = device_title["title"]
                    else:
                        device_info = "1"

                avatar_id = record[7] if record[7] else 1
                avatar_url = f"/files/image/icon/avatar/{avatar_id}.png"

                score = record[8]

                html += f"""
                <div class="leaderboard-player">
                    <div class="rank">#{rank}</div>
                    <img class="avatar" src="{avatar_url}" alt="Avatar">
                    <div class="leaderboard-info">
                        <div class="name">{username}</div>
                        <div class="title"><img src="/files/image/title/{device_info}.png" alt="Title"></div>
                    </div>
                    <div class="leaderboard-score">{score}</div>
                </div>
                """

        html += "</div>"

        encrypted_mass = encryptAES(("vid=" + device_id + "&dummy=").encode("utf-8"))
        html += f"""
        <a href="/ranking.php?{encrypted_mass}" class="bt_bg01" style="margin: 20px auto; display: block; text-align: center;">
            Go Back
        </a>
        """

        file_path = os.path.join("files", "ranking.html")
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                html_content = file.read().format(text=html)
        except FileNotFoundError:
            return HTMLResponse("""<html><body><h1>Ranking file not found</h1></body></html>""", status_code=500)

        return HTMLResponse(html_content)
    else:
        return HTMLResponse("""<html><body><h1>Access denied</h1></body></html>""", status_code=403)

async def status(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return HTMLResponse("""<html><body><h1>Invalid request data</h1></body></html>""", status_code=400)

    should_serve = True
    if AUTHORIZATION_NEEDED:
        should_serve = await api.database.check_whitelist(decrypted_fields) and not await api.database.check_blacklist(decrypted_fields)

    if should_serve:
        device_id = decrypted_fields[b'vid'][0].decode()
        set_title = int(decrypted_fields[b'set_title'][0].decode()) if b'set_title' in decrypted_fields else None
        page_id = int(decrypted_fields[b'page_id'][0].decode()) if b'page_id' in decrypted_fields else 0

        if set_title:
            update_query = (
                update(api.database.daily_reward)
                .where(api.database.daily_reward.c.device_id == device_id)
                .values(title=set_title)
            )
            await api.database.execute(update_query)

        query = select(api.database.daily_reward).where(api.database.daily_reward.c.device_id == device_id)
        user_data = await api.database.database.fetch_one(query)

        user_name = f"Guest({device_id[-6:]})"
        if user_data:
            query = select(api.database.user.c.username).where(api.database.user.c.device_id == device_id)
            user_result = await api.database.database.fetch_one(query)
            if user_result:
                user_name = user_result["username"]

        html = ""
        if user_data:
            player_element = f"""
                <div class="player-element">
                    <img src="/files/image/icon/avatar/{user_data['avatar']}.png" class="avatar" alt="Player Avatar">
                    <div class="player-info">
                        <div class="name">{user_name}</div>
                        <img src="/files/image/title/{user_data['title']}.png" class="title" alt="Player Title">
                    </div>
                    <div class="player-score">Level {user_data['lvl']}</div>
                </div>
            """
            html += player_element

        page_name = ["Special", "Normal", "Master", "God"]
        buttons_html = '<div class="button-row">'
        for i, name in enumerate(page_name):
            if i == page_id:
                buttons_html += f"""
                    <div class="bt_bg01_ac">{name}</div>
                """
            else:
                encrypted_mass = encryptAES(f"vid={device_id}&page_id={i}&dummy=".encode("utf-8"))
                buttons_html += f"""
                    <a href="/status.php?{encrypted_mass}" class="bt_bg01_xnarrow">{name}</a>
                """
        buttons_html += '</div>'
        html += f"<div style='text-align: center; margin-top: 20px;'>{buttons_html}</div>"

        selected_titles = TITLE_LISTS.get(page_id, [])
        titles_html = '<div class="title-list">'
        for index, num in enumerate(selected_titles):
            if index % 2 == 0:
                if index != 0:
                    titles_html += '</div>'
                titles_html += '<div class="title-row">'

            if num == user_data["title"]:
                titles_html += f"""
                    <img src="/files/image/title/{num}.png" alt="Title {num}" class="title-image-selected">
                """
            else:
                encrypted_mass = encryptAES(f"vid={device_id}&title_id={num}&page_id={page_id}&dummy=".encode("utf-8"))
                titles_html += f"""
                    <a href="/set_title.php?{encrypted_mass}" class="title-link">
                        <img src="/files/image/title/{num}.png" alt="Title {num}" class="title-image">
                    </a>
                """
        titles_html += '</div></div>'
        html += titles_html

        file_path = os.path.join("files", "status.html")
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                html_content = file.read().format(text=html)
        except FileNotFoundError:
            return HTMLResponse("""<html><body><h1>Status file not found</h1></body></html>""", status_code=500)

        return HTMLResponse(html_content)
    
    else:
        return HTMLResponse("""<html><body><h1>Access denied</h1></body></html>""", status_code=403)
    
async def set_title(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return HTMLResponse("""<html><body><h1>Invalid request data</h1></body></html>""", status_code=400)

    should_serve = True
    if AUTHORIZATION_NEEDED:
        should_serve = await api.database.check_whitelist(decrypted_fields) and not await api.database.check_blacklist(decrypted_fields)

    if should_serve:
        device_id = decrypted_fields[b'vid'][0].decode()
        page_id = decrypted_fields[b'page_id'][0].decode()
        title_id = decrypted_fields[b'title_id'][0].decode()
        current_title = 1

        query = select(api.database.daily_reward.c.title).where(api.database.daily_reward.c.device_id == device_id)
        row = await api.database.database.fetch_one(query)
        if row:
            current_title = row["title"]

        confirm_url = encryptAES(
            f"vid={device_id}&page_id={page_id}&set_title={title_id}&dummy=".encode("utf-8")
        )
        go_back_url = encryptAES(
            f"vid={device_id}&page_id={page_id}&dummy=".encode("utf-8")
        )

        html = f"""
            <p>Would you like to change your title?<br>Current Title:</p>
            <img src="/files/image/title/{current_title}.png" alt="Current Title" class="title-image">
            <p>New Title:</p>
            <img src="/files/image/title/{title_id}.png" alt="New Title" class="title-image">
            <div class="button-container">
                <a href="/status.php?{confirm_url}" class="bt_bg01">Confirm</a>
                <a href="/status.php?{go_back_url}" class="bt_bg01">Go back</a>
            </div>
        """
        return HTMLResponse(inform_page(html, 1))
    
    else:
        return HTMLResponse("""<html><body><h1>Access denied</h1></body></html>""", status_code=403)

async def mission(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return HTMLResponse("""<html><body><h1>Invalid request data</h1></body></html>""", status_code=400)

    should_serve = True
    if AUTHORIZATION_NEEDED:
        should_serve = await api.database.check_whitelist(decrypted_fields) and not await api.database.check_blacklist(decrypted_fields)

    if should_serve:
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
        file_path = os.path.join("files", "mission.html")
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                html_content = file.read().format(text=html)
        except FileNotFoundError:
            return HTMLResponse("""<html><body><h1>Mission file not found</h1></body></html>""", status_code=500)

        return HTMLResponse(html_content)
    else:
        return HTMLResponse("""<html><body><h1>Access denied</h1></body></html>""", status_code=403)

routes = [
    Route('/ranking.php', ranking, methods=['GET']),
    Route('/ranking_detail.php', ranking_detail, methods=['GET']),
    Route('/set_title.php', set_title, methods=['GET']),
    Route('/mission.php', mission, methods=['GET']),
    Route('/status.php', status, methods=['GET']),
]