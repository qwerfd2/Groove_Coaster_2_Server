from starlette.responses import Response
from starlette.requests import Request
from starlette.routing import Route
import os
import json
from sqlalchemy import select, update, insert
import xml.etree.ElementTree as ET

from config import ROOT_FOLDER, START_COIN, COIN_REWARD, AUTHORIZATION_NEEDED

from api.database import database, cache_database, ranking_cache, user, daily_reward, result, check_blacklist, check_whitelist
from api.crypt import decrypt_fields
from api.templates import START_STAGES, EXP_UNLOCKED_SONGS

async def result_request(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return Response("""<response><code>10</code><message>Invalid request data.</message></response>""", media_type="application/xml")

    should_serve = True
    if AUTHORIZATION_NEEDED:
        should_serve = await check_whitelist(decrypted_fields) and not await check_blacklist(decrypted_fields)

    if not should_serve:
        return Response("""<response><code>403</code><message>Access denied.</message></response>""", media_type="application/xml")

    device_id = decrypted_fields[b'vid'][0].decode()
    file_path = os.path.join(ROOT_FOLDER, "files/result.xml")
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        return Response(f"""<response><code>500</code><message>Error parsing XML: {str(e)}</message></response>""", media_type="application/xml")

    vid = decrypted_fields[b'vid'][0].decode()
    stts = decrypted_fields[b'stts'][0].decode()
    track_id = decrypted_fields[b'id'][0].decode()
    mode = decrypted_fields[b'mode'][0].decode()
    avatar = decrypted_fields[b'avatar'][0].decode()
    score = int(decrypted_fields[b'score'][0].decode())
    high_score = decrypted_fields[b'high_score'][0].decode()
    play_rslt = decrypted_fields[b'play_rslt'][0].decode()
    item = decrypted_fields[b'item'][0].decode()
    device_os = decrypted_fields[b'os'][0].decode()
    os_ver = decrypted_fields[b'os_ver'][0].decode()
    tid = decrypted_fields[b'tid'][0].decode()
    ver = decrypted_fields[b'ver'][0].decode()
    mike = decrypted_fields[b'mike'][0].decode()

    cache_key = f"{track_id}-{mode}"

    # delete cache with key first

    delete_query = ranking_cache.delete().where(ranking_cache.c.key == cache_key)
    await cache_database.execute(delete_query)

    # add coins, skip 4max placeholder songs

    if int(track_id) not in range(616, 1024) or int(mode) not in range(0, 4):
        query = select(daily_reward.c.coin).where(daily_reward.c.device_id == device_id)
        row = await database.fetch_one(query)
        query = select(user.c.coin_mp).where(user.c.device_id == device_id)
        coin_mp_row = await database.fetch_one(query)
        if coin_mp_row is None:
            coin_mp_row = {"coin_mp": 1}
        current_coin = row["coin"] if row and row["coin"] else START_COIN
        updated_coin = current_coin + COIN_REWARD * coin_mp_row["coin_mp"]

        update_query = (
            update(daily_reward)
            .where(daily_reward.c.device_id == device_id)
            .values(coin=updated_coin)
        )
        await database.execute(update_query)

    query = select(user.c.id).where(user.c.device_id == vid)
    user_row = await database.fetch_one(query)
    sid = user_row["id"] if user_row else ""

    do_insert = False
    do_update_sid = False
    do_update_vid = False
    last_row_id = 0

    if sid:
        query = select(result.c.rid, result.c.score).where(
            (result.c.id == track_id) &
            (result.c.mode == mode) &
            (result.c.sid == sid)
        ).order_by(result.c.score.desc())
        records = await database.fetch_all(query)
        if records:
            last_row_id = records[0]["rid"]
            if score > int(records[0]["score"]):
                do_update_sid = True
        else:
            do_insert = True
    else:
        query = select(result.c.rid, result.c.score).where(
            (result.c.id == track_id) &
            (result.c.mode == mode) &
            (result.c.sid == "") &
            (result.c.vid == vid)
        ).order_by(result.c.score.desc())
        records = await database.fetch_all(query)
        if records:
            last_row_id = records[0]["rid"]
            if score > records[0]["score"]:
                do_update_vid = True
        else:
            do_insert = True

    if do_insert:
        insert_query = insert(result).values(
            vid=vid, stts=stts, id=track_id, mode=mode, avatar=avatar,
            score=score, high_score=high_score, play_rslt=play_rslt, item=item,
            os=device_os, os_ver=os_ver, tid=tid, sid=sid, ver=ver, mike=mike
        )
        result_obj = await database.execute(insert_query)
        last_row_id = result_obj
    elif do_update_sid:
        update_query = (
            update(result)
            .where((result.c.sid == sid) & (result.c.id == track_id) & (result.c.mode == mode))
            .values(
                stts=stts, avatar=avatar, score=score, high_score=high_score,
                play_rslt=play_rslt, item=item, os=device_os, os_ver=os_ver,
                tid=tid, ver=ver, mike=mike, vid=vid
            )
        )
        await database.execute(update_query)
    elif do_update_vid:
        update_query = (
            update(result)
            .where((result.c.vid == vid) & (result.c.id == track_id) & (result.c.mode == mode))
            .values(
                stts=stts, avatar=avatar, score=score, high_score=high_score,
                play_rslt=play_rslt, item=item, os=device_os, os_ver=os_ver,
                sid=sid, ver=ver, mike=mike
            )
        )
        await database.execute(update_query)

    query = select(daily_reward.c.my_stage).where(daily_reward.c.device_id == device_id)
    row = await database.fetch_one(query)
    my_stage = set(json.loads(row["my_stage"])) if row and row["my_stage"] else set(START_STAGES)

    current_exp = int(stts.split(",")[0])
    for song in EXP_UNLOCKED_SONGS:
        if song["lvl"] <= current_exp:
            my_stage.add(song["id"])

    my_stage = sorted(my_stage)
    update_query = (
        update(daily_reward)
        .where(daily_reward.c.device_id == device_id)
        .values(lvl=current_exp, avatar=int(avatar), my_stage=json.dumps(my_stage))
    )
    await database.execute(update_query)

    query = select(result.c.rid, result.c.score).where(
        (result.c.id == track_id) & (result.c.mode == mode)
    ).order_by(result.c.score.desc())
    records = await database.fetch_all(query)

    rank = None
    for idx, record in enumerate(records, start=1):
        if record["rid"] == last_row_id:
            rank = idx
            break

    after_element = root.find('.//after')
    after_element.text = str(rank)
    xml_response = ET.tostring(tree.getroot(), encoding='unicode')
    return Response(xml_response, media_type="application/xml")

routes = [
    Route('/result.php', result_request, methods=['GET'])
]