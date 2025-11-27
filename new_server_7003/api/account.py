from starlette.responses import Response, HTMLResponse
from starlette.requests import Request
from starlette.routing import Route
from datetime import datetime
import secrets

from api.misc import is_alphanumeric, inform_page, verify_password, hash_password, crc32_decimal, should_serve, generate_salt
from api.database import check_blacklist, user_name_to_user_info, decrypt_fields_to_user_info, set_user_data_using_decrypted_fields, get_user_from_save_id, create_user, logout_user, login_user, get_bind, read_user_save_file, write_user_save_file
from api.crypt import decrypt_fields
from config import AUTHORIZATION_MODE

async def name_reset(request: Request):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")

    if not username or not password:
        return inform_page("FAILED:<br>Missing username or password.", 0)

    if len(username) < 6 or len(username) > 20:
        return inform_page("FAILED:<br>Username must be between 6 and 20 characters long.", 0)

    if not is_alphanumeric(username):
        return inform_page("FAILED:<br>Username must consist entirely of alphanumeric characters.", 0)

    if username == password:
        return inform_page("FAILED:<br>Username cannot be the same as password.", 0)

    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return inform_page("FAILED:<br>Invalid request data.", 0)

    if not await check_blacklist(decrypted_fields):
        return inform_page("FAILED:<br>Your account is banned and you are not allowed to perform this action.", 0)

    user_info, device_info = await decrypt_fields_to_user_info(decrypted_fields)
    if user_info:
        existing_user_info = await user_name_to_user_info(username)
        if existing_user_info:
            return inform_page("FAILED:<br>Another user already has this name.", 0)

        password_hash = user_info['password_hash']
        if password_hash:
            if verify_password(password, password_hash):
                update_data = {
                    "username": username
                }
                await set_user_data_using_decrypted_fields(decrypted_fields, update_data)
                return inform_page("SUCCESS:<br>Username updated.", 0)
            else:
                return inform_page("FAILED:<br>Password is not correct.<br>Please try again.", 0)
        else:
            return inform_page("FAILED:<br>User has no password hash.<br>This should not happen.", 0)
    else:
        return inform_page("FAILED:<br>User does not exist.<br>This should not happen.", 0)

async def password_reset(request: Request):
    form = await request.form()
    old_password = form.get("old")
    new_password = form.get("new")

    if not old_password or not new_password:
        return inform_page("FAILED:<br>Missing old or new password.", 0)

    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return inform_page("FAILED:<br>Invalid request data.", 0)

    user_info, device_info = await decrypt_fields_to_user_info(decrypted_fields)

    if user_info:
        username = user_info['username']
        if username == new_password:
            return inform_page("FAILED:<br>Username cannot be the same as password.", 0)
        if len(new_password) < 6:
            return inform_page("FAILED:<br>Password must have 6 or more characters.", 0)

        old_hash = user_info['password_hash']
        if old_hash:
            if verify_password(old_password, old_hash):
                hashed_new_password = hash_password(new_password)
                updated_data = {
                    "password_hash": hashed_new_password
                }
                await set_user_data_using_decrypted_fields(decrypted_fields, updated_data)
                return inform_page("SUCCESS:<br>Password updated.", 0)
            else:
                return inform_page("FAILED:<br>Old password is not correct.<br>Please try again.", 0)
        else:
            return inform_page("FAILED:<br>User has no password hash.<br>This should not happen.", 0)
    else:
        return inform_page("FAILED:<br>User does not exist.<br>This should not happen.", 0)

async def user_coin_mp(request: Request):
    form = await request.form()
    mp = form.get("coin_mp")

    if not mp:
        return inform_page("FAILED:<br>Missing multiplier.", 0)
    
    mp = int(mp)

    if mp < 0 or mp > 5:
        return inform_page("FAILED:<br>Multiplier not acceptable.", 0)

    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return inform_page("FAILED:<br>Invalid request data.", 0)
    
    user_info, _ = await decrypt_fields_to_user_info(decrypted_fields)

    if user_info:
        update_data = {
            "coin_mp": mp
        }
        await set_user_data_using_decrypted_fields(decrypted_fields, update_data)
        return inform_page("SUCCESS:<br>Coin multiplier set to " + str(mp) + ".", 0)
    else:
        return inform_page("FAILED:<br>User does not exist.", 0)

async def save_migration(request: Request):
    form = await request.form()
    save_id = form.get("save_id")

    if not save_id:
        return inform_page("FAILED:<br>Missing save_id.", 0)

    if len(save_id) != 24 or not all(c in '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ' for c in save_id):
        return inform_page("FAILED:<br>Save ID not acceptable format.", 0)

    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return inform_page("FAILED:<br>Invalid request data.", 0)
    
    should_serve_result = await should_serve(decrypted_fields)

    if not should_serve_result:
        return inform_page("FAILED:<br>You cannot access this feature right now.", 0)

    user_info, _ = await decrypt_fields_to_user_info(decrypted_fields)
    if user_info:
        user_id = user_info['id']
        username = user_info['username']
        existing_save_user = await get_user_from_save_id(save_id)

        if existing_save_user['id'] == user_id:
            return inform_page("FAILED:<br>Save ID is already associated with your account.", 0)

        existing_save_data = ""
        if existing_save_user:
            existing_save_data = await read_user_save_file(existing_save_user['id'])

        if existing_save_data != "":
            update_data = {
                "save_crc": existing_save_user['crc'],
                "save_timestamp": existing_save_user['timestamp']
            }
            await set_user_data_using_decrypted_fields(decrypted_fields, update_data)
            await write_user_save_file(user_info['id'], existing_save_data)

            return inform_page("SUCCESS:<br>Save migration was applied. If this was done by mistake, press the Save button now.", 0)
        else:
            return inform_page("FAILED:<br>Save ID is not associated with a save file.", 0)

    else:
        return inform_page("FAILED:<br>User does not exist.", 0)

async def register(request: Request):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")

    if not username or not password:
        return inform_page("FAILED:<br>Missing username or password.", 0)

    if username == password:
        return inform_page("FAILED:<br>Username cannot be the same as password.", 0)

    if len(username) < 6 or len(username) > 20:
        return inform_page("FAILED:<br>Username must be between 6 and 20<br>characters long.", 0)

    if len(password) < 6:
        return inform_page("FAILED:<br>Password must have<br>6 or above characters.", 0)

    if not is_alphanumeric(username):
        return inform_page("FAILED:<br>Username must consist entirely of<br>alphanumeric characters.", 0)

    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return inform_page("FAILED:<br>Invalid request data.", 0)
    
    user_info, _ = await decrypt_fields_to_user_info(decrypted_fields)

    if user_info:
        return inform_page("FAILED:<br>Another user already has this name.", 0)

    await create_user(username, hash_password(password), decrypted_fields[b'vid'][0].decode())

    return inform_page("SUCCESS:<br>Account is registered.<br>You can now backup/restore your save file.<br>You can only log into one device at a time.", 0)

async def logout(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return inform_page("FAILED:<br>Invalid request data.", 0)

    if not await check_blacklist(decrypted_fields):
        return inform_page("FAILED:<br>Your account is banned and you are<br>not allowed to perform this action.", 0)

    device_id = decrypted_fields[b'vid'][0].decode()
    await logout_user(device_id)
    return inform_page("Logout success.", 0)

async def login(request: Request):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")

    if not username or not password:
        return inform_page("FAILED:<br>Missing username or password.", 0)

    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return inform_page("FAILED:<br>Invalid request data.", 0)

    user_record = await user_name_to_user_info(username)
    if user_record:
        user_id = user_record['id']

        password_hash_record = user_record['password_hash']
        if password_hash_record and verify_password(password, password_hash_record):
            device_id = decrypted_fields[b'vid'][0].decode()
            await login_user(user_id, device_id)

            return inform_page("SUCCESS:<br>You are logged in.", 0)
        else:
            return inform_page("FAILED:<br>Username or password incorrect.", 0)
    else:
        return inform_page("FAILED:<br>Username or password incorrect.", 0)

async def load(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return Response("""<response><code>10</code><message><ja>この機能を使用するには、まずアカウントを登録する必要があります。</ja><en>You need to register an account first before this feature can be used.</en><fr>Vous devez d'abord créer un compte avant de pouvoir utiliser cette fonctionnalité.</fr><it>È necessario registrare un account prima di poter utilizzare questa funzione.</it></message></response>""", media_type="application/xml")
    
    should_serve_result = await should_serve(decrypted_fields)

    if not should_serve_result:
        return Response("""<response><code>10</code><message><ja>この機能を使用するには、現在アクセスできません。</ja><en>You cannot access this feature right now.</en><fr>Vous ne pouvez pas accéder à cette fonctionnalité pour le moment.</fr><it>Non è possibile accedere a questa funzione in questo momento.</it></message></response>""", media_type="application/xml")

    user_info, device_info = await decrypt_fields_to_user_info(decrypted_fields)
    if not user_info:
        return Response( """<response><code>10</code><message><ja>この機能を使用するには、まずアカウントを登録する必要があります。</ja><en>You need to register an account first before this feature can be used.</en><fr>Vous devez d'abord créer un compte avant de pouvoir utiliser cette fonctionnalité.</fr><it>È necessario registrare un account prima di poter utilizzare questa funzione.</it></message></response>""", media_type="application/xml")
    data = await read_user_save_file(user_info['id'])
    if data and data != "":
        crc = user_info['save_crc']
        timestamp = user_info['save_timestamp']
        xml_data = f"""<?xml version="1.0" encoding="UTF-8"?><response><code>0</code>
            <data>{data}</data>
            <crc>{crc}</crc>
            <date>{timestamp}</date>
            </response>"""
        return Response(xml_data, media_type="application/xml")
    else:
        return Response( """<response><code>12</code><message><ja>セーブデータが無いか、セーブデータが破損しているため、ロードできませんでした。</ja><en>Unable to load; either no save data exists, or the save data is corrupted.</en><fr>Chargement impossible : les données de sauvegarde sont absentes ou corrompues.</fr><it>Impossibile caricare. Non esistono dati salvati o quelli esistenti sono danneggiati.</it></message></response>""", media_type="application/xml")

async def save(request: Request):
    decrypted_fields, _ = await decrypt_fields(request)
    if not decrypted_fields:
        return Response("""<response><code>10</code><message><ja>この機能を使用するには、まずアカウントを登録する必要があります。</ja><en>You need to register an account first before this feature can be used.</en><fr>Vous devez d'abord créer un compte avant de pouvoir utiliser cette fonctionnalité.</fr><it>È necessario registrare un account prima di poter utilizzare questa funzione.</it></message></response>""", media_type="application/xml")
    
    should_serve_result = await should_serve(decrypted_fields)

    if not should_serve_result:
        return Response("""<response><code>10</code><message><ja>この機能を使用するには、現在アクセスできません。</ja><en>You cannot access this feature right now.</en><fr>Vous ne pouvez pas accéder à cette fonctionnalité pour le moment.</fr><it>Non è possibile accedere a questa funzione in questo momento.</it></message></response>""", media_type="application/xml")

    data = await request.body()
    data = data.decode("utf-8")

    user_info, _ = await decrypt_fields_to_user_info(decrypted_fields)

    username = user_info['username']
    user_id = user_info['id']
    if username:
        crc = crc32_decimal(data)
        formatted_time = datetime.now()
        is_save_id_unique = False
        while not is_save_id_unique:
            save_id = ''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(24))

            existing_user = await get_user_from_save_id(save_id)
            if not existing_user:
                is_save_id_unique = True

        await write_user_save_file(user_info['id'], data)

        update_data = {
            "save_crc": crc,
            "save_id": save_id,
            "save_timestamp": formatted_time
        }
        await set_user_data_using_decrypted_fields(decrypted_fields, update_data)

        return Response("""<response><code>0</code></response>""", media_type="application/xml")
    else:
        return Response("""<response><code>10</code><message><ja>この機能を使用するには、まずアカウントを登録する必要があります。</ja><en>You need to register an account first before this feature can be used.</en><fr>Vous devez d'abord créer un compte avant de pouvoir utiliser cette fonctionnalité.</fr><it>È necessario registrare un account prima di poter utilizzare questa funzione.</it></message></response>""", media_type="application/xml")

async def ttag(request: Request):
    decrypted_fields, original_field = await decrypt_fields(request)
    if not decrypted_fields:
        return inform_page("FAILED:<br>Invalid request data.", 0)
    
    user_info, _ = await decrypt_fields_to_user_info(decrypted_fields)

    if user_info:
        username = user_info['username']
        user_id = user_info['id']
        gcoin_mp = user_info['coin_mp']
        savefile_id = user_info['save_id']
        if AUTHORIZATION_MODE == 0:
            bind_element = '<p>No bind required in current mode.</p>'
        elif AUTHORIZATION_MODE == 1:
            # Email auth mode
            bind_state = await get_bind(user_id)

            if bind_state and bind_state['is_verified'] == 1:
                bind_element = f'<p>Email verified: {bind_state["bind_acc"]}\nTo remove a bind, contact the administrator.</p>'
            else:
                bind_element = f"""
                    <form action="/send_email/?{original_field}" method="post">
                        <div class="f60 a_center">
                            <label for="email">Email:</label>
                            <br>
                            <input class="input" id="email" name="email" type="email">
                            <br>
                            <input class="bt_bg01_narrow" type="submit" value="Send Email">
                        </div>
                    </form>
                    <form action="/verify/?{original_field}" method="post">
                        <div class="f60 a_center">
                            <label for="code">Verification Code:</label>
                            <br>
                            <input class="input" id="code" name="code">
                            <br>
                            <input class="bt_bg01_narrow" type="submit" value="Verify">
                        </div>
                    </form>
                    """
            
        elif AUTHORIZATION_MODE == 2:
            bind_state = await get_bind(user_id)
            bind_code = await generate_salt(username, user_id)
            if bind_state and bind_state['is_verified'] == 1:
                bind_element = f'<p>Discord verified: {bind_state["bind_acc"]}<br>To remove a bind, contact the administrator.</p>'
            else:
                bind_element = f"""
                    <p>To receive a verification code, please join our Discord server 'https://discord.gg/vugfJdc2rk' and use the !bind command with your account name and the following code. Do not leak this code to others.</p>
                    <div class="f60 a_center">
                        <label>Your bind code:</label>
                        <br>
                        <input class="input" value="{bind_code}" readonly>
                    </div>
                    <form action="/verify/?{original_field}" method="post">
                        <div class="f60 a_center">
                            <label for="code">Verification Code:</label>
                            <br>
                            <input class="input" id="code" name="code">
                            <br>
                            <input class="bt_bg01_narrow" type="submit" value="Verify">
                        </div>
                    </form>
                    """

        with open("web/profile.html", "r") as file:
            html_content = file.read().format(
                bind_element=bind_element,
                pid=original_field,
                user=username,
                gcoin_mp_0='selected' if gcoin_mp == 0 else '',
                gcoin_mp_1='selected' if gcoin_mp == 1 else '',
                gcoin_mp_2='selected' if gcoin_mp == 2 else '',
                gcoin_mp_3='selected' if gcoin_mp == 3 else '',
                gcoin_mp_4='selected' if gcoin_mp == 4 else '',
                gcoin_mp_5='selected' if gcoin_mp == 5 else '',
                savefile_id=savefile_id,
                
            )
    else:
        with open("web/register.html", "r") as file:
            html_content = file.read().format(pid=original_field)

    return HTMLResponse(html_content)

routes = [
    Route('/name_reset/', name_reset, methods=['POST']),
    Route('/password_reset/', password_reset, methods=['POST']),
    Route('/coin_mp/', user_coin_mp, methods=['POST']),
    Route('/save_migration/', save_migration, methods=['POST']),
    Route('/register/', register, methods=['POST']),
    Route('/logout/', logout, methods=['POST']),
    Route('/login/', login, methods=['POST']),
    Route('/load.php', load, methods=['GET']),
    Route('/save.php', save, methods=['POST']),
    Route('/ttag.php', ttag, methods=['GET']),
]