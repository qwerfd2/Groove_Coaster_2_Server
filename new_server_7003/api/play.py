from starlette.responses import Response
from starlette.requests import Request
from starlette.routing import Route
import json
import copy
import xml.etree.ElementTree as ET
from datetime import datetime

from config import COIN_REWARD

from api.database import player_database, results, decrypt_fields_to_user_info, set_device_data_using_decrypted_fields, results_query, set_user_data_using_decrypted_fields, clear_rank_cache
from api.crypt import decrypt_fields
from api.template import START_STAGES, EXP_UNLOCKED_SONGS, RESULT_XML
from api.misc import should_serve

async def score_delta(mode, old_score, new_score):
    mobile_modes = [1, 2, 3]
    arcade_modes = [11, 12, 13]
    if mode in mobile_modes:
        return new_score - old_score, 0, new_score - old_score
    elif mode in arcade_modes:
        return 0, new_score - old_score, new_score - old_score
    else:
        return 0, 0, 0

async def result_request(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return Response("""<response><code>10</code><message>Invalid request data.</message></response>""", media_type="application/xml")

    should_serve_result = await should_serve(decrypted_fields)

    if not should_serve_result:
        return Response("""<response><code>403</code><message>Access denied.</message></response>""", media_type="application/xml")

    device_id = decrypted_fields[b'vid'][0].decode()
    user_info, device_info = await decrypt_fields_to_user_info(decrypted_fields)

    tree = copy.deepcopy(RESULT_XML)
    root = tree.getroot()

    stts = decrypted_fields[b'stts'][0].decode()
    song_id = int(decrypted_fields[b'id'][0].decode())
    mode = int(decrypted_fields[b'mode'][0].decode())
    avatar = int(decrypted_fields[b'avatar'][0].decode())
    score = int(decrypted_fields[b'score'][0].decode())
    high_score = decrypted_fields[b'high_score'][0].decode()
    play_rslt = decrypted_fields[b'play_rslt'][0].decode()
    item = int(decrypted_fields[b'item'][0].decode())
    device_os = decrypted_fields[b'os'][0].decode()
    os_ver = decrypted_fields[b'os_ver'][0].decode()
    ver = decrypted_fields[b'ver'][0].decode()

    stts = "[" + stts + "]"
    high_score = "[" + high_score + "]"
    play_rslt = "[" + play_rslt + "]"

    try:
        stts = json.loads(stts)
        high_score = json.loads(high_score)
        play_rslt = json.loads(play_rslt)
    except:
        return Response("""<response><code>10</code><message>Invalid request data.</message></response>""", media_type="application/xml")

    cache_key = f"{song_id}-{mode}"

    # delete cache with key

    await clear_rank_cache(cache_key)

    # Start results processing

    target_row_id = 0
    rank = None

    user_id = user_info['id'] if user_info else None

    if user_id:

        query_param = {
            "song_id": song_id,
            "mode": mode,
            "user_id": user_id
        }
        records = await results_query(query_param)
        
        mobile_delta, arcade_delta, total_delta = 0, 0, 0

        if len(records) != 0:
            # user row exists
            target_row_id = records[0]['id']
            if score > records[0]['score']:
                mobile_delta, arcade_delta, total_delta = await score_delta(mode, records[0]['score'], score)
                update_query = results.update().where(results.c.id == records[0]['id']).values(
                    device_id=device_id,
                    stts=stts,
                    avatar=avatar,
                    score=score,
                    high_score=high_score,
                    play_rslt=play_rslt,
                    item=item,
                    os=device_os,
                    os_ver=os_ver,
                    ver=ver
                )
                await player_database.execute(update_query)

        else:
            # insert new row

            mobile_delta, arcade_delta, total_delta = await score_delta(mode, 0, score)
            insert_query = results.insert().values(
                device_id=device_id,
                user_id=user_id,
                stts=stts,
                song_id=song_id,
                mode=mode,
                avatar=avatar,
                score=score,
                high_score=high_score,
                play_rslt=play_rslt,
                item=item,
                os=device_os,
                os_ver=os_ver,
                ver=ver,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            result = await player_database.execute(insert_query)
            target_row_id = result

        # Calculate final rank for client display
    
        query_param = {
            "song_id": song_id,
            "mode": mode
        }

        records = await results_query(query_param)

        rank = None
        for idx, record in enumerate(records, start=1):
            if record["id"] == target_row_id:
                rank = idx
                break

        # Update user score delta

        if total_delta:
            update_data = {
                "mobile_delta": user_info['mobile_delta'] + mobile_delta,
                "arcade_delta": user_info['arcade_delta'] + arcade_delta,
                "total_delta": user_info['total_delta'] + total_delta
            }
            await set_user_data_using_decrypted_fields(decrypted_fields, update_data)

    # Unlocking mission stages and updating avatars

    my_stage = set(device_info["my_stage"]) if device_info and device_info["my_stage"] else set(START_STAGES)

    current_exp = stts[0]
    for song in EXP_UNLOCKED_SONGS:
        if song["lvl"] <= current_exp:
            my_stage.add(song["id"])

    my_stage = sorted(my_stage)

    update_data = {
        "lvl": current_exp,
        "avatar": int(avatar),
        "my_stage": my_stage
    }

    # add coins, skip 4max placeholder songs

    if int(song_id) not in range(616, 1024) or int(mode) not in range(0, 4):
        coin_mp = user_info['coin_mp'] if user_info else 1

        current_coin = device_info["coin"] if device_info and device_info["coin"] else 0
        updated_coin = current_coin + COIN_REWARD * coin_mp

        update_data["coin"] = updated_coin

    await set_device_data_using_decrypted_fields(decrypted_fields, update_data)

    after_element = root.find('.//after')
    after_element.text = str(rank)
    xml_response = ET.tostring(tree.getroot(), encoding='unicode')
    return Response(xml_response, media_type="application/xml")

routes = [
    Route('/result.php', result_request, methods=['GET'])
]