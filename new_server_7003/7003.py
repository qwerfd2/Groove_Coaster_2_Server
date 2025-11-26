from starlette.applications import Starlette
import os

# stupid loading sequence
from api.template import init_templates
init_templates()

from api.database import player_database, cache_database, init_db
from api.misc import get_4max_version_string

from api.user import routes as user_routes
from api.account import routes as account_routes
from api.ranking import routes as rank_routes
from api.shop import routes as shop_routes
from api.play import routes as play_routes
from api.batch import routes as batch_routes
from api.web import routes as web_routes
from api.file import routes as file_routes
from api.discord_hook import routes as discord_routes
from api.admin import routes as admin_routes

from config import DEBUG, SSL_CERT, SSL_KEY, ACTUAL_HOST, ACTUAL_PORT, BATCH_DOWNLOAD_ENABLED, AUTHORIZATION_MODE

if (os.path.isfile('./files/4max_ver.txt')):
    get_4max_version_string()

if AUTHORIZATION_MODE == 1:
    from api.email_hook import init_email
    init_email()

routes = []

routes = routes + user_routes + account_routes + rank_routes + shop_routes + play_routes + web_routes + file_routes + discord_routes + admin_routes

if BATCH_DOWNLOAD_ENABLED:
    routes = routes + batch_routes

app = Starlette(debug=DEBUG, routes=routes)

@app.on_event("startup")
async def startup():
    await player_database.connect()
    await cache_database.connect()
    await init_db()

@app.on_event("shutdown")
async def shutdown():
    await player_database.disconnect()
    await cache_database.disconnect()

if __name__ == "__main__":
    import uvicorn
    ssl_context = (SSL_CERT, SSL_KEY) if SSL_CERT and SSL_KEY else None
    uvicorn.run(app, host=ACTUAL_HOST, port=ACTUAL_PORT, ssl_certfile=SSL_CERT, ssl_keyfile=SSL_KEY)

# Made By Tony  2025.11.21