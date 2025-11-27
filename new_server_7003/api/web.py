from starlette.requests import Request
from starlette.routing import Route
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
import secrets
from datetime import datetime
import time

from api.database import player_database, webs, is_admin, user_name_to_user_info, user_id_to_user_info_simple, get_user_export_data
from api.misc import verify_password, should_serve_web
from api.file import convert_user_export_data
from config import AUTHORIZATION_MODE, SAVE_EXPORT_COOLDOWN

async def is_user(request: Request):
    token = request.cookies.get("token")
    if not token:
        return False, None
    query = webs.select().where(webs.c.web_token == token)
    web_data = await player_database.fetch_one(query)
    if not web_data:
        return False, None
    if web_data['permission'] < 1:
        return False, None
    
    if AUTHORIZATION_MODE > 0:
        result = await should_serve_web(web_data['user_id'])
        if not result:
            return False, None


    return True, web_data

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
            web_token=token,
            updated_at=datetime.utcnow()
        )
    else:
        query = webs.insert().values(
            user_id=user_info['id'],
            permission=1,
            web_token=token,
            last_save_export=0,
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
    
    query = webs.select().where(webs.c.web_token == token)
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
            "next_save_export": web_record['last_save_export'] + SAVE_EXPORT_COOLDOWN,
        }
        return JSONResponse({"status": "success", "data": response_data})


    else:
        return JSONResponse({"status": "failed", "message": "Invalid action."}, status_code=400)
    
async def user_center_page(request: Request):
    serve, web_data = await is_user(request)
    if not serve:
        response = RedirectResponse(url="/login")
        response.delete_cookie(key="token")
        return response
    
    with open("web/user.html", "r", encoding="utf-8") as file:
        html_template = file.read()
        is_adm = await is_admin(request.cookies.get("token"))
        if is_adm:
            admin_button = f"""
            <div class="container mt-4">
                <button class="btn btn-light" onclick="window.location.href='/admin'">Admin Panel</button>
            </div>
            """
            html_template += admin_button

    return HTMLResponse(content=html_template)

async def user_center_export_data(request: Request):
    serve, web_data = await is_user(request)
    if not serve:
        response = RedirectResponse(url="/login")
        response.delete_cookie(key="token")
        return response
    
    user_id = web_data['user_id']
    last_save_export = web_data['last_save_export']
    current_time = time.time()

    if current_time - last_save_export < SAVE_EXPORT_COOLDOWN:
        wait_time = int(SAVE_EXPORT_COOLDOWN - (current_time - last_save_export))
        return JSONResponse({"status": "failed", "message": f"Please wait {wait_time} seconds before exporting again."}, status_code=429)
    
    user_json_data_set = await get_user_export_data(user_id)
    user_xlsx_stream = await convert_user_export_data(user_json_data_set)

    headers = {
        "Content-Disposition": 'attachment; filename="export.xlsx"'
    }

    update_query = webs.update().where(webs.c.user_id == user_id).values(
        last_save_export=int(current_time),
        updated_at=datetime.utcnow()
    )
    await player_database.execute(update_query)

    return StreamingResponse(
        user_xlsx_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )

routes = [
    Route("/login", web_login_page, methods=["GET"]),
    Route("/login/", web_login_page, methods=["GET"]),
    Route("/login/login", web_login_login, methods=["POST"]),
    Route("/usercenter", user_center_page, methods=["GET"]),
    Route("/usercenter/api", user_center_api, methods=["POST"]),
    Route("/usercenter/export_data", user_center_export_data, methods=["GET"]),
]