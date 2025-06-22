from starlette.applications import Starlette
from starlette.responses import FileResponse, Response
from starlette.routing import Route
import os

# stupid loading sequence
from api.templates import init_templates
init_templates()

from api.database import database, init_db
from api.misc import get_4max_version_string

from api.user import routes as user_routes
from api.ranking import routes as rank_routes
from api.shop import routes as shop_routes
from api.play import routes as play_routes

from config import HOST, PORT, DEBUG, SSL_CERT, SSL_KEY, ROOT_FOLDER, ACTUAL_HOST, ACTUAL_PORT

if (os.path.isfile('./files/dlc_4max.html')):
    get_4max_version_string()

allowed_folders = ["files"]

async def serve_file(request):
    path = request.path_params['path']
    for folder in allowed_folders:
        if path.startswith(folder):
            file_path = os.path.join(ROOT_FOLDER, path)
            if os.path.isfile(file_path):
                return FileResponse(file_path)

    return Response("", status_code=404)

routes = []

routes = routes + user_routes + rank_routes + shop_routes + play_routes

routes.append(Route("/{path:path}", serve_file))

app = Starlette(debug=DEBUG, routes=routes)

@app.on_event("startup")
async def startup():
    await database.connect()
    await init_db()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

if __name__ == "__main__":
    import uvicorn
    ssl_context = (SSL_CERT, SSL_KEY) if SSL_CERT and SSL_KEY else None
    uvicorn.run(app, host=ACTUAL_HOST, port=ACTUAL_PORT, ssl_certfile=SSL_CERT, ssl_keyfile=SSL_KEY)

# Made By Tony  2025.5.10