from starlette.responses import HTMLResponse
from starlette.requests import Request
from starlette.routing import Route
import os
import json
import time

from api.database import database, batch_token
from config import THREAD_COUNT

async def batch_handler(request: Request):
    data = await request.json()
    token = data.get("token")
    platform = data.get("platform")
    if not token:
        return HTMLResponse(content="Token is required", status_code=400)
    
    if platform not in ["Android", "iOS"]:
        return HTMLResponse(content="Invalid platform", status_code=400)

    query = batch_token.select().where(batch_token.c.token == token)
    result = await database.fetch_one(query)

    if not result:
        return HTMLResponse(content="Invalid token", status_code=400)

    if result['expire_at'] < int(time.time()):
        return HTMLResponse(content="Token expired", status_code=400)
    
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