from starlette.responses import HTMLResponse
import requests
import json
import binascii
import secrets
import bcrypt
import hashlib
import re
import xml.etree.ElementTree as ET
from config import MODEL, TUNEFILE, SKIN, AUTHORIZATION_NEEDED, AUTHORIZATION_MODE, GRANDFATHERED_ACCOUNT_LIMIT, BIND_SALT
from api.database import get_bind, check_whitelist, check_blacklist, decrypt_fields_to_user_info, user_id_to_user_info_simple

FMAX_VER = None
FMAX_RES = None

def get_4max_version_string():
    url = "https://studio.code.org/v3/sources/3-aKHy16Y5XaAPXQHI95RnFOKlyYT2O95ia2HN2jKIs/main.json"
    global FMAX_VER
    try:
        with open("./files/4max_ver.txt", 'r') as file:
            FMAX_VER = file.read().strip()
    except Exception as e:
        print(f"An unexpected error occurred when loading files/4max_ver.txt: {e}")
    
    def fetch():
        global FMAX_RES
        try:
            response = requests.get(url)
            if 200 <= response.status_code <= 207:
                try:
                    response_json = response.json()
                    FMAX_RES = json.loads(response_json['source'])
                except (json.JSONDecodeError, KeyError):
                    
                    FMAX_RES = 500
            else:
                FMAX_RES = response.status_code
        except requests.RequestException:
            FMAX_RES = 400
    
    fetch()

def parse_res(res):
    parsed_data = []
    if isinstance(res, int) or res == None:
        return "Failed to fetch version info: Error " + str(res)
    
    for item in res:
        if item.get("isOpen"):
            version = item.get("version", 0)
            changelog = "<br>".join(item.get("changeLog", {}).get("en", []))
            parsed_data.append(f"<strong>Version: {version}</strong><p><strong>Changelog:</strong><br>{changelog}</p>")
    return "".join(parsed_data)

def crc32_decimal(data):
    crc32_hex = binascii.crc32(data.encode())
    return int(crc32_hex & 0xFFFFFFFF)

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def verify_password(password, hashed_password):
    if type(hashed_password) == str:
        hashed_password = hashed_password.encode('utf-8')

    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

def is_alphanumeric(username):
    pattern = r"^[a-zA-Z0-9]+$"
    return bool(re.match(pattern, username))

async def get_model_pak(decrypted_fields, user_id):
    mid = ET.Element("model_pak")
    rid = ET.Element("date")
    uid = ET.Element("url")

    host = await get_host_string()

    if AUTHORIZATION_MODE == 0:
        auth_token = decrypted_fields[b'vid'][0].decode()
        rid.text = MODEL
        uid.text = host + "files/gc2/" + auth_token + "/pak/model" + MODEL + ".pak"
    else:
        if user_id:
            bind_info = await get_bind(user_id)
            if bind_info and bind_info['is_verified'] == 1:
                auth_token = bind_info['auth_token']
                rid.text = MODEL
                uid.text = host + "files/gc2/" + auth_token + "/pak/model" + MODEL + ".pak"
            else:
                rid.text = "1"
                uid.text = host + "files/gc/model1.pak"
        else:
            rid.text = "1"
            uid.text = host + "files/gc/model1.pak"

    mid.append(rid)
    mid.append(uid)
    return mid

async def get_tune_pak(decrypted_fields, user_id):
    mid = ET.Element("tuneFile_pak")
    rid = ET.Element("date")
    uid = ET.Element("url")

    host = await get_host_string()

    if AUTHORIZATION_MODE == 0:
        auth_token = decrypted_fields[b'vid'][0].decode()
        rid.text = TUNEFILE
        uid.text = host + "files/gc2/" + auth_token + "/pak/tuneFile" + TUNEFILE + ".pak"
    else:
        if user_id:
            bind_info = await get_bind(user_id)
            if bind_info and bind_info['is_verified'] == 1:
                auth_token = bind_info['auth_token']
                rid.text = TUNEFILE
                uid.text = host + "files/gc2/" + auth_token + "/pak/tuneFile" + TUNEFILE + ".pak"
            else:
                rid.text = "1"
                uid.text = host + "files/gc/tuneFile1.pak"
        else:
            rid.text = "1"
            uid.text = host + "files/gc/tuneFile1.pak"

    mid.append(rid)
    mid.append(uid)
    return mid

async def get_skin_pak(decrypted_fields, user_id):
    mid = ET.Element("skin_pak")
    rid = ET.Element("date")
    uid = ET.Element("url")

    host = await get_host_string()

    if AUTHORIZATION_MODE == 0:
        auth_token = decrypted_fields[b'vid'][0].decode()
        rid.text = SKIN
        uid.text = host + "files/gc2/" + auth_token + "/pak/skin" + SKIN + ".pak"
    else:
        if user_id:
            bind_info = await get_bind(user_id)
            if bind_info and bind_info['is_verified'] == 1:
                auth_token = bind_info['auth_token']
                rid.text = SKIN
                uid.text = host + "files/gc2/" + auth_token + "/pak/skin" + SKIN + ".pak"
            else:
                rid.text = "1"
                uid.text = host + "files/gc/skin1.pak"
        else:
            rid.text = "1"
            uid.text = host + "files/gc/skin1.pak"

    mid.append(rid)
    mid.append(uid)
    return mid
    
async def get_m4a_path(decrypted_fields, user_id):
    host = await get_host_string()
    if AUTHORIZATION_MODE == 0:
        auth_token = decrypted_fields[b'vid'][0].decode()
        mid = ET.Element("m4a_path")
        mid.text = host + "files/gc2/" + auth_token + "/audio/"
    else:
        if user_id:
            bind_info = await get_bind(user_id)
            if bind_info and bind_info['is_verified'] == 1:
                mid = ET.Element("m4a_path")
                mid.text = host + "files/gc2/" + bind_info['auth_token'] + "/audio/"
            else:
                mid = ET.Element("m4a_path")
                mid.text = host
        else:
            mid = ET.Element("m4a_path")
            mid.text = host
        
    return mid

async def get_stage_path(decrypted_data, user_id):
    host = await get_host_string()
    if AUTHORIZATION_MODE == 0:
        auth_token = decrypted_data[b'vid'][0].decode()
        mid = ET.Element("stage_path")
        mid.text = host + "files/gc2/" + auth_token + "/stage/"
    else:
        if user_id:
            bind_info = await get_bind(user_id)
            if bind_info and bind_info['is_verified'] == 1:
                mid = ET.Element("stage_path")
                mid.text = host + "files/gc2/" + bind_info['auth_token'] + "/stage/"
            else:
                mid = ET.Element("stage_path")
                mid.text = host
        else:
            mid = ET.Element("stage_path")
            mid.text = host
    
    return mid

def get_stage_zero():
    sid = ET.Element("my_stage")
    did = ET.Element("stage_id")
    cid = ET.Element("ac_mode")
    did.text = "0"
    cid.text = "0"
    sid.append(did)
    sid.append(cid)
    return sid

def inform_page(text, mode):
    if mode == 0:
        mode = "/files/web/ttl_taitoid.png"
    elif mode == 1:
        mode = "/files/web/ttl_information.png"
    elif mode == 2:
        mode = "/files/web/ttl_buy.png"
    elif mode == 3:
        mode = "/files/web/ttl_title.png"
    elif mode == 4:
        mode = "/files/web/ttl_rank.png"
    elif mode == 5:
        mode = "/files/web/ttl_mission.png"
    elif mode == 6:
        mode = "/files/web/ttl_shop.png"
    with open("web/inform.html", "r") as file:
        return HTMLResponse(file.read().format(text=text, img=mode))
    
def safe_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None

def generate_otp():
    otp = ''.join(secrets.choice('0123456789') for _ in range(6))
    hashed_otp = hash_otp(otp)
    return otp, hashed_otp

def hash_otp(otp):
    return hashlib.sha256(otp.encode()).hexdigest()

def check_email(email):
    STRICT_EMAIL_REGEX = r"^[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*@[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*(?:\.[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)*\.[A-Za-z]{2,}$"
    return re.match(STRICT_EMAIL_REGEX, email) is not None

async def should_serve(decrypted_fields):
    should_serve = True
    if AUTHORIZATION_NEEDED:
        should_serve = await check_whitelist(decrypted_fields) and not await check_blacklist(decrypted_fields)
    
    if AUTHORIZATION_MODE and should_serve:
        user_info, device_info = await decrypt_fields_to_user_info(decrypted_fields, "id")
        bind_info = await get_bind(user_info["id"])
        if not bind_info or bind_info['is_verified'] != 1:
            should_serve = False

    return should_serve

async def should_serve_init(decrypted_fields):
    should_serve = True
    if AUTHORIZATION_NEEDED:
        should_serve = await check_whitelist(decrypted_fields) and not await check_blacklist(decrypted_fields)
    
    return should_serve

async def should_serve_web(user_id):
    user_id = safe_int(user_id)
    should_serve = True
    if AUTHORIZATION_MODE:
        bind_info = await get_bind(user_id)
        if not bind_info or bind_info['is_verified'] != 1:
            should_serve = False
        if user_id < GRANDFATHERED_ACCOUNT_LIMIT:
            should_serve = True

    return should_serve

async def generate_salt(user_id):
    user_info = await user_id_to_user_info_simple(user_id)
    user_pw_hash = user_info['password_hash']
    username = user_info['username']

    combined = f"{username}{user_id}{user_pw_hash}{BIND_SALT}".encode('utf-8')
    crc32_hash = binascii.crc32(combined) & 0xFFFFFFFF
    return str(crc32_hash)

async def get_host_string():
    from config import OVERRIDE_HOST, HOST, PORT
    host_string = OVERRIDE_HOST if OVERRIDE_HOST is not None else ("http://" + HOST + ":" + str(PORT) + "/")
    return host_string
