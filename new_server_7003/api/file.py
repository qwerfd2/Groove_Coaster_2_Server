from starlette.responses import Response, FileResponse
from starlette.requests import Request
from starlette.routing import Route
from sqlalchemy import select
import os

from api.database import player_database, devices, binds, batch_tokens, log_download, get_downloaded_bytes
from config import AUTHORIZATION_MODE, DAILY_DOWNLOAD_LIMIT

async def serve_file(request: Request):
    auth_token = request.path_params['auth_token']
    folder = request.path_params['folder']
    filename = request.path_params['filename']

    if folder not in ["audio", "stage", "pak"]:
        return Response("Unauthorized", status_code=403)
    
    if not filename.endswith(".zip") and not filename.endswith(".pak"):
        return Response("Unauthorized", status_code=403)
    
    existing_batch_token = select(batch_tokens).where(batch_tokens.c.bind_token == auth_token)
    batch_result = await player_database.fetch_one(existing_batch_token)
    if batch_result:
        pass
    
    elif AUTHORIZATION_MODE == 0:
        existing_device = select(devices).where(devices.c.device_id == auth_token)
        result = await player_database.fetch_one(existing_device)
        if not result:
            return Response("Unauthorized", status_code=403)
        else:
            pass

    else:
        existing_bind = select(binds).where((binds.c.auth_token == auth_token) & (binds.c.is_verified == 1))
        result = await player_database.fetch_one(existing_bind)
        if not result:
            return Response("Unauthorized", status_code=403)
        else:
            daily_bytes = await get_downloaded_bytes(result['user_id'], 24)
            if daily_bytes >= DAILY_DOWNLOAD_LIMIT:
                return Response("Daily download limit exceeded", status_code=403)

    safe_filename = os.path.realpath(os.path.join(os.getcwd(), "files", "gc2", folder, filename))
    base_directory = os.path.realpath(os.path.join(os.getcwd(), "files", "gc2", folder))

    if not safe_filename.startswith(base_directory):
        return Response("Unauthorized", status_code=403)

    file_path = safe_filename

    if os.path.isfile(file_path):
        # get size of file
        if AUTHORIZATION_MODE != 0:
            file_size = os.path.getsize(file_path)
            await log_download(result['user_id'], filename, file_size)
        return FileResponse(file_path)
    else:
        return Response("File not found", status_code=404)


async def serve_public_file(request: Request):
    path = request.path_params['path']
    safe_filename = os.path.realpath(os.path.join(os.getcwd(), "files", path))
    base_directory = os.path.realpath(os.path.join(os.getcwd(), "files"))

    if not safe_filename.startswith(base_directory):
        return Response("Unauthorized", status_code=403)

    if os.path.isfile(safe_filename):
        return FileResponse(safe_filename)
    else:
        return Response("File not found", status_code=404)


routes = [
    Route("/files/gc2/{auth_token}/{folder}/{filename}", serve_file, methods=["GET"]),
    Route("/files/{path:path}", serve_public_file, methods=["GET"]),
]