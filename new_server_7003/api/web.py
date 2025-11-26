from starlette.requests import Request
from starlette.routing import Route
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse
import secrets
from datetime import datetime

from api.database import player_database, webs, is_admin, user_name_to_user_info, user_id_to_user_info_simple
from api.misc import read_user_save_file, verify_password, should_serve_web
from config import AUTHORIZATION_MODE

async def is_user(request: Request):
    token = request.cookies.get("token")
    if not token:
        return False
    query = webs.select().where(webs.c.token == token)
    web_data = await player_database.fetch_one(query)
    if not web_data:
        return False
    if web_data['permission'] < 1:
        return False
    
    if AUTHORIZATION_MODE > 0:
        return await should_serve_web(web_data['user_id'])

    return True

async def web_login_page(request: Request):
    with open("web/login.html", "r", encoding="utf-8") as file:
        html_template = file.read()
    return HTMLResponse(content=html_template)

async def web_login_login(request: Request):
    form_data = await request.json()
    username = form_data.get("username")
    password = form_data.get("password")

    user_info = await user_name_to_user_info(username)
    if not user_info:
        return JSONResponse({"status": "failed", "message": "Invalid username or password."}, status_code=400)
    
    if not verify_password(password, user_info['password_hash']):
        return JSONResponse({"status": "failed", "message": "Invalid username or password."}, status_code=400)
    
    should_serve = await should_serve_web(user_info['id'])
    if not should_serve:
        return JSONResponse({"status": "failed", "message": "Access denied."}, status_code=403)
    
    token = secrets.token_hex(64)
    web_query = webs.select().where(webs.c.user_id == user_info['id'])
    web_result = await player_database.fetch_one(web_query)
    if web_result:
        if web_result['permission'] < 1:
            return JSONResponse({"status": "failed", "message": "Access denied."}, status_code=403)
        
        query = webs.update().where(webs.c.user_id == user_info['id']).values(
            token=token
        )
    else:
        query = webs.insert().values(
            user_id=user_info['id'],
            permission=1,
            web_token=token,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    await player_database.execute(query)

    return JSONResponse({"status": "success", "message": token})


async def user_center_api(request: Request):
    form_data = await request.json()
    token = form_data.get("token")
    if not token:
        return JSONResponse({"status": "failed", "message": "Token is required."}, status_code=400)
    
    query = webs.select().where(webs.c.token == token)
    web_record = await player_database.fetch_one(query)
    if not web_record:
        return JSONResponse({"status": "failed", "message": "Invalid token."}, status_code=403)
    
    if web_record['permission'] == 2 and form_data.get("user_id"):
        user_id = int(form_data.get("user_id") )
    elif web_record['permission'] == 2:
        user_id = int(web_record['user_id'])
    else:
        user_id = int(web_record['user_id'])
    
    action = form_data.get("action")

    if action == "basic":
        user_info = await user_id_to_user_info_simple(user_id)
        if not user_info:
            return JSONResponse({"status": "failed", "message": "User not found."}, status_code=404)
        
        response_data = {
            "username": user_info['username'],
            "last_save_export": web_record['last_save_export'].isoformat() if web_record['last_save_export'] else "None",
        }
        return JSONResponse({"status": "success", "data": response_data})


    else:
        return JSONResponse({"status": "failed", "message": "Invalid action."}, status_code=400)
    
async def user_center_page(request: Request):
    usr = await is_user(request)
    if not usr:
        response = RedirectResponse(url="/login")
        return response
    
    with open("web/user.html", "r", encoding="utf-8") as file:
        html_template = file.read()
        is_adm = await is_admin(request)
        if is_adm:
            admin_button = f"""
            <div class="container mt-4">
            <button class="btn btn-light" onclick="window.location.href='/admin'">Admin Panel</button>
            </div>
            """
            html_template += admin_button

    return HTMLResponse(content=html_template)

routes = [
    Route("/login", web_login_page, methods=["GET"]),
    Route("/login/", web_login_page, methods=["GET"]),
    Route("/login/login", web_login_login, methods=["POST"]),
    Route("/usercenter", user_center_page, methods=["GET"]),
    Route("/usercenter/api", user_center_api, methods=["POST"])
]