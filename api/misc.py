import requests
import json
import binascii
import bcrypt
import re
import xml.etree.ElementTree as ET
from config import MODEL, TUNEFILE, SKIN

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
                    FMAX_RES = json.loads(json.loads(response.text)['source'])
                except (json.JSONDecodeError, KeyError):
                    FMAX_RES = 500
            else:
                FMAX_RES = response.status_code
        except requests.RequestException:
            FMAX_RES = 400
    
    fetch()

def parse_res(res):
    parsed_data = []
    if isinstance(res, int):
        return "Failed to fetch version info: Error " + str(res)
    
    for item in res:
        if item.get("isOpen"):
            version = item.get("version", "Unknown Version")
            changelog = "<br>".join(item.get("changeLog", {}).get("en", []))
            parsed_data.append(f"<strong>Version: {version}</strong><p><strong>Changelog:</strong><br>{changelog}</p>")
    return "".join(parsed_data)

def crc32_decimal(data):
    crc32_hex = binascii.crc32(data.encode())
    return int(crc32_hex & 0xFFFFFFFF)

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password

def verify_password(password, hashed_password):
    if type(hashed_password) == str:
        hashed_password = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

def is_alphanumeric(username):
    pattern = r"^[a-zA-Z0-9]+$"
    return bool(re.match(pattern, username))

def get_model_pak(host):
    mid = ET.Element("model_pak")
    rid = ET.Element("date")
    uid = ET.Element("url")
    rid.text = MODEL
    uid.text = host + "files/gc2/model" + MODEL + ".pak"
    mid.append(rid)
    mid.append(uid)
    return mid

def get_tune_pak(host):
    mid = ET.Element("tuneFile_pak")
    rid = ET.Element("date")
    uid = ET.Element("url")
    rid.text = TUNEFILE
    uid.text = host + "files/gc2/tuneFile" + TUNEFILE + ".pak"
    mid.append(rid)
    mid.append(uid)
    return mid

def get_skin_pak(host):
    mid = ET.Element("skin_pak")
    rid = ET.Element("date")
    uid = ET.Element("url")
    rid.text = SKIN
    uid.text = host + "files/gc2/skin" + SKIN + ".pak"
    mid.append(rid)
    mid.append(uid)
    return mid
    
def get_m4a_path(host):
    mid = ET.Element("m4a_path")
    mid.text = host + "files/gc2/audio/"
    return mid

def get_stage_path(host):
    mid = ET.Element("stage_path")
    mid.text = host + "files/gc2/stage/"
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
    with open("files/inform.html", "r") as file:
        return file.read().format(text=text, img=mode)