
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route
from datetime import datetime

from api.misc import is_alphanumeric, inform_page, generate_salt, check_email, generate_otp
from api.database import player_database, accounts, binds, decrypt_fields_to_user_info, get_bind, verify_user_code, user_name_to_user_info
from api.crypt import decrypt_fields
from api.email_hook import send_email_to_user
from api.decorators import require_authorization, validate_form_fields, check_discord_api_key

@require_authorization(mode_required=[1])
async def send_email(request: Request):
    form = await request.form()
    email = form.get("email")

    if not email:
        return inform_page("FAILED:<br>Missing email.", 0)
    
    email_valid = check_email(email)
    if not email_valid:
        return inform_page("FAILED:<br>Invalid email format.", 0)

    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return inform_page("FAILED:<br>Invalid request data.", 0)
    
    account_record, device_record = await decrypt_fields_to_user_info(decrypted_fields)
    if not account_record:
        return inform_page("FAILED:<br>User does not exist.", 0)
    
    bind_state = await get_bind(account_record['id'])
    if bind_state and bind_state['is_verified'] == 1:
        return inform_page("FAILED:<br>Your account is already verified.", 0)

    response_message = await send_email_to_user(email, account_record['id'])
    return inform_page(response_message, 0)

@require_authorization(mode_required=[1, 2])
async def verify_user(request: Request):
    form = await request.form()
    code = form.get("code")

    if not code:
        return inform_page("FAILED:<br>Missing verification code.", 0)

    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return inform_page("FAILED:<br>Invalid request data.", 0)
    
    account_record, device_record = await decrypt_fields_to_user_info(decrypted_fields)
    if not account_record:
        return inform_page("FAILED:<br>User does not exist.", 0)
    
    bind_state = await get_bind(account_record['id'])
    if bind_state and bind_state['is_verified'] == 1:
        return inform_page("FAILED:<br>Your account is already verified.", 0)

    response_message = await verify_user_code(code, account_record['id'])
    return inform_page(response_message, 0)

@require_authorization(mode_required=[2])
@validate_form_fields(["username", "bind_token", "discord_id"])
@check_discord_api_key()
async def discord_get_token(request: Request, form):
    username = form.get("username")
    bind_token = form.get("bind_token")
    discord_id = form.get("discord_id")

    if len(username) < 6 or len(username) > 20 or not is_alphanumeric(username):
        return JSONResponse({"state": 0, "message": "Invalid username."}, status_code=400)

    user_info = await user_name_to_user_info(username)
    user_info = dict(user_info) if user_info else None
    if not user_info:
        return JSONResponse({"state": 0, "message": "User does not exist."}, status_code=404)
    
    user_id = user_info['id']
    
    bind_state = await get_bind(user_info['id'])
    if bind_state and bind_state['is_verified'] == 1:
        return JSONResponse({"state": 0, "message": "User is already binded. If you want to rebind, contact the administrator."}, status_code=400)

    if bind_state and bind_state['is_verified'] < 0:
        return JSONResponse({"state": 0, "message": "This account cannot be binded now. Please contact the administrator."}, status_code=400)

    binded_search_query = binds.select().where(binds.c.bind_acc == discord_id).where(binds.c.is_verified == 1)
    binded_search_record = await player_database.fetch_one(binded_search_query)

    if binded_search_record:
        return JSONResponse({"state": 0, "message": "This Discord ID is already binded to another account. Please contact the administrator to remove the prior bind."}, status_code=400)
    
    expected_token = await generate_salt(user_id)
    if bind_token != expected_token:
        return JSONResponse({"state": 0, "message": "Invalid bind token."}, status_code=400)
    
    if bind_state:
        if (datetime.utcnow() - bind_state['bind_date']).total_seconds() < 60:
            return JSONResponse({"state": 0, "message": "Too many requests. Please wait a while before retrying."}, status_code=400)

    verify_code, hash_code = generate_otp()
    if bind_state:
        await player_database.execute(binds.update().where(binds.c.user_id == user_id).values(
            bind_acc=discord_id,
            bind_code=verify_code,
            bind_date=datetime.utcnow()
        ))
    else:
        query = binds.insert().values(
            user_id=user_id,
            bind_acc=discord_id,
            bind_code=verify_code,
            is_verified=0,
            bind_date=datetime.utcnow()
        )
        await player_database.execute(query)

    return JSONResponse({"state": 1, "message": "Verification code generated. Enter the following code in-game: " + verify_code})

@require_authorization(mode_required=[2])
@validate_form_fields(["discord_id"])
@check_discord_api_key()
async def discord_get_bind(request: Request, form):
    discord_id = form.get("discord_id")

    query = binds.select().where(binds.c.bind_acc == discord_id).where(binds.c.is_verified == 1)
    bind_record = await player_database.fetch_one(query)
    bind_record = dict(bind_record) if bind_record else None
    if not bind_record:
        return JSONResponse({"state": 0, "message": "No verified bind found for this Discord ID."}, status_code=404)
    
    user_query = accounts.select().where(accounts.c.id == bind_record['user_id'])
    user_record = await player_database.fetch_one(user_query)

    user_record = dict(user_record) if user_record else None
    if not user_record:
        return JSONResponse({"state": 0, "message": "User associated with this bind does not exist."}, status_code=405)
    
    return JSONResponse({"state": 1, "message": "Your account is binded to: " + user_record['username']})

@require_authorization(mode_required=[2])
@validate_form_fields(["discord_id"])
@check_discord_api_key()
async def discord_ban(request: Request, form):
    discord_id = form.get("discord_id")
    
    query = binds.select().where(binds.c.bind_acc == discord_id).where(binds.c.is_verified == 1)
    bind_record = await player_database.fetch_one(query)

    bind_record = dict(bind_record) if bind_record else None

    if not bind_record:
        return JSONResponse({"state": 0, "message": "No verified bind found for this Discord ID."}, status_code=404)
    
    update_query = binds.update().where(binds.c.id == bind_record['id']).values(
        is_verified=-1
    )
    await player_database.execute(update_query)

    return JSONResponse({"state": 1, "message": "The account associated with this Discord ID has been banned."})

@require_authorization(mode_required=[2])
@validate_form_fields(["discord_id"])
@check_discord_api_key()
async def discord_unban(request: Request, form):
    discord_id = form.get("discord_id")
    
    query = binds.select().where(binds.c.bind_acc == discord_id).where(binds.c.is_verified == -1)
    bind_record = await player_database.fetch_one(query)
    bind_record = dict(bind_record) if bind_record else None

    if not bind_record:
        return JSONResponse({"state": 0, "message": "No unbannable banned bind found for this Discord ID."}, status_code=404)
    
    update_query = binds.update().where(binds.c.id == bind_record['id']).values(
        is_verified=1
    )
    await player_database.execute(update_query)
    return JSONResponse({"state": 1, "message": "The account associated with this Discord ID has been unbanned."})

routes = [
    Route('/send_email', send_email, methods=['POST']),
    Route('/discord_get_token', discord_get_token, methods=['POST']),
    Route('/discord_get_bind', discord_get_bind, methods=['POST']),
    Route('/discord_ban', discord_ban, methods=['POST']),
    Route('/discord_unban', discord_unban, methods=['POST']),
    Route('/verify', verify_user, methods=['POST'])
]