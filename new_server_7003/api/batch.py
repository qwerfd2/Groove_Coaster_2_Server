from starlette.responses import HTMLResponse
from starlette.requests import Request
from starlette.routing import Route
from datetime import datetime
import os
import json
import time

from api.database import player_database, batch_tokens
from config import THREAD_COUNT

async def batch_handler(request: Request):
    data = await request.json()
    token = data.get("token")
    platform = data.get("platform")
    if not token:
        return HTMLResponse(content="Token is required", status_code=400)
    
    if platform not in ["Android", "iOS"]:
        return HTMLResponse(content="Invalid platform", status_code=400)

    query = batch_tokens.select().where(batch_tokens.c.token == token)
    result = await player_database.fetch_one(query)

    if not result:
        return HTMLResponse(content="Invalid token", status_code=400)

    if result['expire_at'] < int(time.time()):
        return HTMLResponse(content="Token expired", status_code=400)
    
    uses_left = result['uses_left']
    if uses_left > 0:
        uses_left -= 1
    
    else:
        uses_left = -1
        return HTMLResponse(content="No uses left", status_code=400)
    
    update_query = batch_tokens.update().where(batch_tokens.c.token == token).values(
        uses_left=uses_left,
        updated_at=datetime.utcnow()
    )
    await player_database.execute(update_query)
    
    with open(os.path.join('api/config/', 'download_manifest.json'), 'r', encoding='utf-8') as f:
            stage_manifest = json.load(f)

    if platform == "Android":
        with open(os.path.join('api/config/', 'download_manifest_android.json'), 'r', encoding='utf-8') as f:
            audio_manifest = json.load(f)
    else:
        with open(os.path.join('api/config/', 'download_manifest_ios.json'), 'r', encoding='utf-8') as f:
            audio_manifest = json.load(f)

    download_manifest = {
        "stage": stage_manifest,
        "audio": audio_manifest,
        "thread": THREAD_COUNT
    }

    return HTMLResponse(content=json.dumps(download_manifest), status_code=200)

routes = [
    Route("/batch", batch_handler, methods=["POST"]),
]