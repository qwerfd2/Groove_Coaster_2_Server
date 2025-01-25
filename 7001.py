from flask import Flask, request, jsonify, send_file
from config import Config
import os
import sqlite3
import binascii
import bcrypt
import re
from datetime import datetime
import xml.etree.ElementTree as ET
from Crypto.Cipher import AES
import urllib.parse
import json

# Found in: aesManager::initialize()
# Used for: Crypting parameter bytes sent by client
# Credit: https://github.com/Walter-o/gcm-downloader
AES_CBC_KEY = b"oLxvgCJjMzYijWIldgKLpUx5qhUhguP1"

# Found in: aesManager::decryptCBC() and aesManager::encryptCBC()
# Used for: Crypting parameter bytes sent by client
# Credit: https://github.com/Walter-o/gcm-downloader
AES_CBC_IV = b"6NrjyFU04IO9j9Yo"

# Decrypt AES encrypted data, takes in a hex string
# Credit: https://github.com/Walter-o/gcm-downloader
def decryptAES(data, key=AES_CBC_KEY, iv=AES_CBC_IV):
    return AES.new(key, AES.MODE_CBC, iv).decrypt(bytes.fromhex(data))

# Encrypt data with AES, takes in a bytes object
# Credit: https://github.com/Walter-o/gcm-downloader
def encryptAES(data, key=AES_CBC_KEY, iv=AES_CBC_IV):
    while len(data) % 16 != 0:
        data += b"\x00"
    encryptedData = AES.new(key, AES.MODE_CBC, iv).encrypt(data)
    return encryptedData.hex()

start_stages = [3,4,5,7,9,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,214]
# 214 is tutorial song.

start_avatars = []

exclude_stage_exp_pre_100 = [0,1,2,6,8,10,11,12,13,14,15,16,17,18,19,20,21,53,74,75] # not used for now, just archiving
exclude_stage_exp = [121,134,166,167,168,169,170,215,225] # 134 and 170 unoccupied dummy tracks (filled with Departure -Remix-),
#121 (and 93-96 lady gaga songs) removed (can be enabled by patching stageParam:isAvailable, or change the last byte before next song's name - 1 from 01 to 03 in stage_param.dat. 
# Rest are exp unlocked songs.
exclude_avatar_exp = [28,29]

stage_price = 1
avatar_price = 1
item_price = 2
coin_reward = 1

app = Flask(__name__)
app.config.from_object(Config)

DATABASE = 'player.db'
def create_table():
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        cursor.execute( """
            CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(20) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            device_id VARCHAR(512),
            data TEXT,
            crc DECIMAL(10,0),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""")

        cursor.execute( """
            CREATE TABLE IF NOT EXISTS daily_reward (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id VARCHAR(512),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            my_stage TEXT,
            my_avatar TEXT,
            items TEXT,
            day INT
        );""")

        cursor.execute( """
            CREATE TABLE IF NOT EXISTS result (
            rid INTEGER PRIMARY KEY AUTOINCREMENT,
            vid VARCHAR(512) NOT NULL,
            tid VARCHAR(512) NOT NULL,
            sid VARCHAR(512) NOT NULL,
            stts VARCHAR(64),
            id VARCHAR(8),
            mode VARCHAR(4),
            avatar VARCHAR(4),
            score VARCHAR(16),
            high_score VARCHAR(128),
            play_rslt VARCHAR(128),
            item VARCHAR(16),
            os VARCHAR(16),
            os_ver VARCHAR(16),
            ver VARCHAR(16),
            mike VARCHAR(8),
            FOREIGN KEY (vid) REFERENCES user(device_id)
        );""")
        cursor.execute( """
            CREATE TABLE IF NOT EXISTS whitelist (
            id VARCHAR(512) PRIMARY KEY
        );""")
        cursor.execute( """
            CREATE TABLE IF NOT EXISTS blacklist (
            id VARCHAR(512) PRIMARY KEY,
            reason VARCHAR(256)
        );""")
        connection.commit()

create_table()

## Helper function

def crc32_decimal(data):
    crc32_hex = binascii.crc32(data.encode())
    return int(crc32_hex & 0xFFFFFFFF)

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password

def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

def is_alphanumeric(username):
    pattern = r"^[a-zA-Z0-9]+$"
    return bool(re.match(pattern, username))

decrypted_fields = ""
original_field = ""

@app.before_request
def before_request():
    url = request.url
    match = re.search(r'\?(.*)', url)
    if match:
        global decrypted_fields
        global original_field
        original_field = match.group(1)
        decrypted_fields = urllib.parse.parse_qs(decryptAES(match.group(1))[:-1])
        
def get_model_pak(host):
    mid = ET.Element("model_pak")
    rid = ET.Element("date")
    uid = ET.Element("url")
    rid.text = app.config['MODEL']
    uid.text = host + "files/gc2/model" + app.config['MODEL'] + ".pak"
    mid.append(rid)
    mid.append(uid)
    return mid

def get_tune_pak(host):
    mid = ET.Element("tuneFile_pak")
    rid = ET.Element("date")
    uid = ET.Element("url")
    rid.text = app.config['TUNEFILE']
    uid.text = host + "files/gc2/tuneFile" + app.config['TUNEFILE'] + ".pak"
    mid.append(rid)
    mid.append(uid)
    return mid

def get_skin_pak(host):
    mid = ET.Element("skin_pak")
    rid = ET.Element("date")
    uid = ET.Element("url")
    rid.text = app.config['SKIN']
    uid.text = host + "files/gc2/skin" + app.config['SKIN'] + ".pak"
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

def get_user_data(uid, data_field):
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        query = f"SELECT {data_field} FROM user WHERE device_id = ?"
        cursor.execute(query, (uid[b'vid'][0].decode(),))
        result = cursor.fetchone()
        return result
    
def set_user_data(uid, data_field, new_data):
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        query = f"UPDATE user SET {data_field} = ? WHERE device_id = ?"
        cursor.execute(query, (new_data, uid[b'vid'][0].decode()))
        connection.commit()
        
def check_whitelist(uid):
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM whitelist")
        for row in cursor.fetchall():
            if row[0] == uid[b'vid'][0].decode():
                return True
        return False
    
def check_blacklist(uid):
    user = get_user_data(uid, "username")
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM blacklist")
        for row in cursor.fetchall():
            if len(row[0]) > 20:
                if row[0] == uid[b'vid'][0].decode():
                    return False
            elif user is not None:
                if row[0] == user[0]:
                    return False
        return True
    
def inform_page(text, mode):
    if mode == 0:
        mode = "/files/web/ttl_taitoid.png"
    elif mode == 1:
        mode = "/files/web/ttl_information.png"
    elif mode == 2:
        mode = "/files/web/ttl_buy.png"
    with open("files/inform.html", "r") as file:
        return file.read().format(text=text, img=mode)

#Serving CDN files
root_folder = os.path.dirname(os.path.abspath(__file__))
allowed_folders = ["files"]

@app.route('/info.php', methods=['GET'])
def info():
    file_path = os.path.join(root_folder, "files/history.html")
    return send_file(file_path)
    
@app.route('/history.php', methods=['GET'])
def history():
    file_path = os.path.join(root_folder, "files/history.html")
    return send_file(file_path)
    
@app.route('/start.php', methods=['GET'])
def start():
    global decrypted_fields
    file_path = os.path.join(root_folder, "files/start.xml")
    
    # Parse the XML file
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        return jsonify({"error": "Failed to parse XML", "details": str(e)}), 500

    # Retrieve user information
    user = get_user_data(decrypted_fields, "username")
    userID = get_user_data(decrypted_fields, "id")
    
    # Check authorization and access
    should_serve = True
    if app.config.get('AUTHORIZATION_NEEDED', False):
        should_serve = check_whitelist(decrypted_fields) and check_blacklist(decrypted_fields)

    if should_serve:
        # Base host string for generating URLs
        host_string = f"http://{app.config['HOST']}:{app.config['PORT']}/"
        device_id = decrypted_fields[b'vid'][0].decode()
        # Append additional XML nodes
        for generator in [get_model_pak, get_tune_pak, get_skin_pak, get_m4a_path, get_stage_path]:
            try:
                root.append(generator(host_string))
            except Exception as e:
                return jsonify({"error": f"Failed to generate element from {generator.__name__}", "details": str(e)}), 500

        daily_reward_elem = root.find(".//login_bonus")
        if daily_reward_elem is None:
            return jsonify({"error": "Missing <daily_reward> element in XML"}), 500

        # Parse last_count from <daily_reward>
        last_count_elem = daily_reward_elem.find("last_count")
        if last_count_elem is None or not last_count_elem.text.isdigit():
            return jsonify({"error": "Invalid or missing last_count in XML"}), 500
        last_count = int(last_count_elem.text)
        now_count = 1

        with sqlite3.connect(DATABASE) as connection:
            cursor = connection.cursor()

            # Check for an existing row
            cursor.execute("SELECT day, timestamp FROM daily_reward WHERE device_id = ?", (device_id,))
            row = cursor.fetchone()

            if row:
                current_day, last_timestamp = row
                last_date = datetime.strptime(last_timestamp, "%Y-%m-%d %H:%M:%S")
                current_date = datetime.now()

                # Check if one day has passed
                if (current_date.date() - last_date.date()).days >= 1:
                    now_count = current_day + 1
                    # Reset to day 1 if it exceeds last_count
                    if now_count > last_count:
                        now_count = 1

                else:
                    now_count = current_day

            # Add or update <now_count> in <daily_reward>
            now_count_elem = daily_reward_elem.find("now_count")
            if now_count_elem is None:
                now_count_elem = ET.Element("now_count")
                daily_reward_elem.append(now_count_elem)
            now_count_elem.text = str(now_count)

            with sqlite3.connect(DATABASE) as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT my_avatar, my_stage, coin FROM daily_reward WHERE device_id = ?", (device_id,))
                result = cursor.fetchone()

                if (result):
                    my_avatar = set(json.loads(result[0])) if result[0] else start_avatars
                    my_stage = set(json.loads(result[1])) if result[1] else start_stages
                    coin = result[2] if result[2] is not None else 10
                else:
                    my_avatar = start_avatars
                    my_stage = start_stages
                    coin = 10

                coin_elem = ET.Element("my_coin")
                coin_elem.text = str(coin)
                root.append(coin_elem)

                # Add `my_avatar` elements to XML
                for avatar_id in my_avatar:
                    avatar_elem = ET.Element("my_avatar")
                    avatar_elem.text = str(avatar_id)
                    root.append(avatar_elem)

                # Add `my_stage` elements to XML
                for stage_id in my_stage:
                    stage_elem = ET.Element("my_stage")
                    stage_id_elem = ET.Element("stage_id")
                    stage_id_elem.text = str(stage_id)
                    stage_elem.append(stage_id_elem)

                    ac_mode_elem = ET.Element("ac_mode")
                    ac_mode_elem.text = "1"
                    stage_elem.append(ac_mode_elem)
                    root.append(stage_elem)

        if user:
            tid = ET.Element("taito_id")
            tid.text = user[0]
            root.append(tid)

            sid_elem = ET.Element("sid")
            sid_elem.text = str(userID[0])
            root.append(sid_elem)

            try:
                sid = get_stage_zero()
                root.append(sid)
            except Exception as e:
                return jsonify({"error": "Failed to retrieve stage zero", "details": str(e)}), 500

        # Serialize XML to string and return
        xml_response = ET.tostring(root, encoding='unicode')
        return xml_response
    else:
        return jsonify({"error": "Access denied"}), 403

@app.route('/sync.php', methods=['POST','GET'])
def sync():
    global decrypted_fields
    device_id = decrypted_fields[b'vid'][0].decode()
    file_path = os.path.join(root_folder, "files/sync.xml")
    tree = ET.parse(file_path)
    root = tree.getroot()
    user = get_user_data(decrypted_fields, "username")
    should_serve = True
    if app.config['AUTHORIZATION_NEEDED']:
        should_serve = check_whitelist(decrypted_fields)
    if should_serve:
        should_serve = check_blacklist(decrypted_fields)
    if should_serve:
        host_string = "http://" + app.config['HOST'] + ":" + str(app.config['PORT']) + "/"
        model_pak = get_model_pak(host_string)
        tune_pak = get_tune_pak(host_string)
        skin_pak = get_skin_pak(host_string)
        root.append(model_pak)
        root.append(tune_pak)
        root.append(skin_pak)
        m4a_path = get_m4a_path(host_string)
        stage_path = get_stage_path(host_string)
        root.append(m4a_path)
        root.append(stage_path)

        with sqlite3.connect(DATABASE) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT my_avatar, my_stage, coin, item FROM daily_reward WHERE device_id = ?", (device_id,))
            result = cursor.fetchone()

            if (result):
                my_avatar = set(json.loads(result[0])) if result[0] else start_avatars
                my_stage = set(json.loads(result[1])) if result[1] else start_stages
                coin = result[2] if result[2] is not None else 10
                items = json.loads(result[3]) if result[3] else []
            else:
                my_avatar = start_avatars
                my_stage = start_stages
                coin = 10
                items = []
            coin_elem = ET.Element("my_coin")
            coin_elem.text = str(coin)
            root.append(coin_elem)

            for item in items:
                item_elem = ET.Element("add_item")
                item_id_elem = ET.Element("id")
                item_id_elem.text = str(item)
                item_elem.append(item_id_elem)
                item_num_elem = ET.Element("num")
                item_num_elem.text = "9"
                item_elem.append(item_num_elem)
                root.append(item_elem)

            if (len(items) > 0):
                with sqlite3.connect(DATABASE) as connection:
                    cursor = connection.cursor()
                    cursor.execute("""UPDATE daily_reward SET item = ? WHERE device_id = ?""", ("[]", device_id))
                    cursor.close()

            # Add `my_avatar` elements to XML
            for avatar_id in my_avatar:
                avatar_elem = ET.Element("my_avatar")
                avatar_elem.text = str(avatar_id)
                root.append(avatar_elem)

            # Add `my_stage` elements to XML
            for stage_id in my_stage:
                stage_elem = ET.Element("my_stage")
                stage_id_elem = ET.Element("stage_id")
                stage_id_elem.text = str(stage_id)
                stage_elem.append(stage_id_elem)

                ac_mode_elem = ET.Element("ac_mode")
                ac_mode_elem.text = "1"
                stage_elem.append(ac_mode_elem)
                root.append(stage_elem)
        
        if user:
            tid = ET.Element("taito_id")
            tid.text = user[0]
            root.append(tid)
            sid = get_stage_zero()
            root.append(sid)
            kid = ET.Element("friend_num")
            kid.text = "9"
            root.append(kid)
        xml = ET.tostring(tree.getroot(), encoding='unicode')
        return xml
    else:
        return jsonify({"error": "Access denied"}), 403

@app.route('/confirm_tier.php', methods=['GET'])
def tier():
    file_path = os.path.join(root_folder, "files/tier.xml")
    return send_file(file_path)

@app.route('/login_bonus.php', methods=['GET'])
def bonus():
    global decrypted_fields
    device_id = decrypted_fields[b'vid'][0].decode()

    file_path = os.path.join(root_folder, "files/start.xml")
    
    # Parse the XML file
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        return jsonify({"error": "Failed to parse XML", "details": str(e)}), 500

    daily_reward_elem = root.find(".//login_bonus")
    last_count_elem = daily_reward_elem.find("last_count")
    if last_count_elem is None or not last_count_elem.text.isdigit():
        return jsonify({"error": "Invalid or missing last_count in XML"}), 500
    last_count = int(last_count_elem.text)

    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()

        # Check for an existing row
        cursor.execute("SELECT day, timestamp FROM daily_reward WHERE device_id = ?", (device_id,))
        row = cursor.fetchone()

        time = datetime.now()
        formatted_time = time.strftime("%Y-%m-%d %H:%M:%S")

        if row:
            current_day, last_timestamp = row
            last_date = datetime.strptime(last_timestamp, "%Y-%m-%d %H:%M:%S")

            # Check if one day has passed
            if (time.date() - last_date.date()).days >= 1:

                current_day = current_day + 1

                if (current_day > last_count):
                    current_day = 1
 
                # Update the table
                cursor.execute("""UPDATE daily_reward SET timestamp = ?, day = ? WHERE device_id = ?""", (formatted_time, current_day, device_id))

                # return 0 obj
                xml_response = "<response><code>0</code></response>"
            else:
                now_count = current_day
                xml_response = "<response><code>1</code></response>"
                # return 1 obj
        else:
            # No row exists; create a new one
            cursor.execute("""
                INSERT INTO daily_reward (device_id, day, timestamp, my_avatar, my_stage, coin, item)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (device_id, 1, formatted_time, json.dumps(start_avatars), json.dumps(start_stages), 10, "[]"))
            xml_response = "<response><code>0</code></response>"
            # return 0 obj

    return xml_response, 200, {'Content-Type': 'application/xml'}

@app.route('/gcm/php/register.php', methods=['GET'])
def reg():
    global decrypted_fields
    return "", 200

@app.route('/result.php', methods=['GET'])
def result():
    global decrypted_fields
    device_id = decrypted_fields[b'vid'][0].decode()
    file_path = os.path.join(root_folder, "files/result.xml")
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Increment coin for user
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT coin FROM daily_reward WHERE device_id = ?", (device_id,))
        row = cursor.fetchone()

        if row:
            current_coin = row[0] if row[0] else 10
            # Increment the coin value by 1
            updated_coin = current_coin + coin_reward
            cursor.execute("UPDATE daily_reward SET coin = ? WHERE device_id = ?", (updated_coin, device_id))

    # Save the record
    vid = decrypted_fields[b'vid'][0].decode()
    stts = decrypted_fields[b'stts'][0].decode()
    id = decrypted_fields[b'id'][0].decode()
    mode = decrypted_fields[b'mode'][0].decode()
    avatar = decrypted_fields[b'avatar'][0].decode()
    score = decrypted_fields[b'score'][0].decode()
    high_score = decrypted_fields[b'high_score'][0].decode()
    play_rslt = decrypted_fields[b'play_rslt'][0].decode()
    item = decrypted_fields[b'item'][0].decode()

    device_os = decrypted_fields[b'os'][0].decode()
    os_ver = decrypted_fields[b'os_ver'][0].decode()
    tid = decrypted_fields[b'tid'][0].decode()
    ver = decrypted_fields[b'ver'][0].decode()
    mike = decrypted_fields[b'mike'][0].decode()

    do_insert = False
    do_update_sid = False
    do_update_vid = False
    last_row_id = 0

    #parse whether or not the device is logged in to taito ID

    sid = ""
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        select_command = """SELECT id FROM user WHERE device_id = ?;"""
        cursor.execute(select_command, (vid,))
        result = cursor.fetchone()  # Fetch one row from the result
        cursor.close()

        # Check if a row was found
        if result:
            sid = result[0]


    if sid != "":
        with sqlite3.connect(DATABASE) as connection:
            cursor = connection.cursor()
            check_command = """
            SELECT rid, score FROM result WHERE id = ? and mode = ? and sid = ? ORDER BY CAST(score AS INTEGER) DESC;
            """
            cursor.execute(check_command, (id, mode, sid))
            records = cursor.fetchall()
            cursor.close()
            if len(records) > 0:
                # check to see if update is needed
                last_row_id = records[0][0]
                if (score > records[0][1]):
                    do_update_sid = True
            else:
                # create the record
                do_insert = True
    else:
        with sqlite3.connect(DATABASE) as connection:
            cursor = connection.cursor()
            check_command = """
            SELECT rid, score FROM result WHERE id = ? and mode = ? and sid = ? and vid = ? ORDER BY CAST(score AS INTEGER) DESC;
            """
            cursor.execute(check_command, (id, mode, "", vid))
            records = cursor.fetchall()
            cursor.close()
            if len(records) > 0:
                # check to see if update is needed
                last_row_id = records[0][0]
                if (score > records[0][1]):
                    do_update_vid = True
            else:
                # create the record
                do_insert = True 

    
    if do_insert:
        print("result - inserting")
        insert_command = """
        INSERT INTO result (vid, stts, id, mode, avatar, score, high_score, play_rslt, item, os, os_ver, tid, sid, ver, mike)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        with sqlite3.connect(DATABASE) as connection:
            cursor = connection.cursor()
            cursor.execute(insert_command, (vid, stts, id, mode, avatar, score, high_score, play_rslt, item, device_os, os_ver, tid, sid, ver, mike))
            last_row_id = cursor.lastrowid
            cursor.close()
            connection.commit()
    elif do_update_sid:
        print("result - update based off taito id")
        update_command = """UPDATE result
        SET stts = ?, avatar = ?, score = ?, high_score = ?, play_rslt = ?, item = ?, os = ?, os_ver = ?, tid = ?, ver = ?, mike = ?, vid = ?
        WHERE sid = ? AND id = ? AND mode = ?;
        """
        with sqlite3.connect(DATABASE) as connection:
            cursor = connection.cursor()
            cursor.execute(update_command, (stts, avatar, score, high_score, play_rslt, item, device_os, os_ver, tid, ver, mike, vid, sid, id, mode))
            cursor.close()
            connection.commit()
    elif do_update_vid:
        print("result - updatin based off device id")
        update_command = """UPDATE result
        SET stts = ?, avatar = ?, score = ?, high_score = ?, play_rslt = ?, item = ?, os = ?, os_ver = ?, sid = ?, ver = ?, mike = ?
        WHERE vid = ? AND id = ? AND mode = ?;
        """
        with sqlite3.connect(DATABASE) as connection:
            cursor = connection.cursor()
            cursor.execute(update_command, (stts, avatar, score, high_score, play_rslt, item, device_os, os_ver, sid, ver, mike, vid, id, mode))
            cursor.close()
            connection.commit()
            
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        select_command = """
        SELECT rid, score FROM result WHERE id = ? and mode = ? ORDER BY CAST(score AS INTEGER) DESC;
        """
        cursor.execute(select_command, (id, mode))
        records = cursor.fetchall()
        cursor.close()

        rank = None
        for idx, record in enumerate(records, start=1):
            if record[0] == last_row_id:
                rank = idx
                break
    
        after_element = root.find('.//after')
        after_element.text = str(rank)
        xml = ET.tostring(tree.getroot(), encoding='unicode')
        return xml

@app.route('/ttag.php', methods=['GET'])
def ttag():
    global decrypted_fields
    global original_field
    user = get_user_data(decrypted_fields, "username")
    if user:
        with open("files/profile.html", "r") as file:
            html_content = file.read().format(pid=original_field, user=user[0])
    else:
        with open("files/register.html", "r") as file:
            html_content = file.read().format(pid=original_field)
    return html_content, 200


@app.route('/mission.php/', methods=['GET'])
def mission():
    return inform_page("This feature is not available in Private Server.", 1)

@app.route('/status.php/', methods=['GET'])
def status():
    return inform_page("This feature is not available in Private Server.", 1)

@app.route('/ranking.php/', methods=['GET'])
def ranking():
    return inform_page("This feature is not available in Private Server.", 1)

@app.route('/web_shop.php', methods=['GET'])
def web_shop():
    global decrypted_fields
    should_serve = True
    if app.config['AUTHORIZATION_NEEDED']:
        should_serve = check_whitelist(decrypted_fields)
    if should_serve:
        should_serve = check_blacklist(decrypted_fields)
    if should_serve:
        cnt_type = decrypted_fields[b'cnt_type'][0].decode()
        device_id = decrypted_fields[b'vid'][0].decode()
        inc = 0
        buttons_html = ""
        # Define the path for the HTML template
        html_path = f"files/web_shop_{cnt_type}.html"
        with sqlite3.connect(DATABASE) as connection:
            cursor = connection.cursor()
            query = "SELECT my_stage, my_avatar, coin FROM daily_reward WHERE device_id = ?"
            cursor.execute(query, (device_id,))
            result = cursor.fetchone()
            cursor.close()

        # Parse my_stage field (if exists), default to an empty set
        my_stage = set(json.loads(result[0])) if result[0] else start_stages
        my_avatar = set(json.loads(result[1])) if result[1] else start_avatars
        coin = result[2] if result[2] else 0

        if (cnt_type == "1"):
            for idx, i in enumerate(range(90, 616)):
                if i not in my_stage:
                    if i not in exclude_stage_exp:
                        # Add a button for this stage
                        buttons_html += f"""
                            <button style="width: 180px; height: 180px; margin: 10px; background-size: cover; background-image: url('/files/image/icon/shop/{i}.jpg');"
                                    onclick="window.location.href='wwic://web_shop_detail?&cnt_type={cnt_type}&cnt_id={i}'">
                            </button>
                        """

                        # Add a new row every 4 buttons
                        inc += 1
                        if inc % 4 == 0:
                            buttons_html += "<br>"

        elif (cnt_type == "2"):
            for idx, i in enumerate(range(15, 173)):
                if i not in my_avatar:
                    if i not in exclude_avatar_exp:
                        buttons_html += f"""
                            <button style="width: 180px; height: 180px; margin: 10px; background-color: black; background-size: contain; background-repeat: no-repeat; background-position: center center; background-image: url('/files/image/icon/avatar/{i}.png');"
                                    onclick="window.location.href='wwic://web_shop_detail?&cnt_type={cnt_type}&cnt_id={i}'">
                            </button>
                        """
                        # Add a new row every 4 buttons
                        inc += 1
                        if inc % 4 == 0:
                            buttons_html += "<br>"
            
        elif (cnt_type == "3"):
            inc = 1
            for idx, i in enumerate(range(1, 11)):
                buttons_html += f"""
                        <button style="width: 180px; height: 180px; margin: 10px; background-size: cover; background-image: url('/files/image/icon/item/{i}.png');"
                                onclick="window.location.href='wwic://web_shop_detail?&cnt_type={cnt_type}&cnt_id={i}'">
                        </button>
                    """
                # Add a new row every 4 buttons
                if (idx + 1) % 4 == 0:
                    buttons_html += "<br>"
            
        if (inc == 0):
            buttons_html += f"""<div>Everything has been purchased!</div>"""
        # Read and format the HTML template
        with open(html_path, "r", encoding="utf-8") as file:
            html_content = file.read().format(text=buttons_html, coin=coin)
            return html_content
    else:
        return jsonify({"error": "Access denied"}), 403

@app.route('/web_shop_detail.php', methods=['GET'])
def web_shop_detail():
    global decrypted_fields
    cnt_type = decrypted_fields[b'cnt_type'][0].decode()
    cnt_id = int(decrypted_fields[b'cnt_id'][0].decode())
    device_id = decrypted_fields[b'vid'][0].decode()

    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        query = "SELECT coin FROM daily_reward WHERE device_id = ?"
        cursor.execute(query, (device_id,))
        result = cursor.fetchone()
        cursor.close()

    coin = result[0] if result and result[0] else 0
    your_html = ""

    if (cnt_type == "1"):
        your_html = f"""
        <div class="image-container">
            <img src="/files/image/icon/shop/{cnt_id}.jpg" alt="Item Image" style="width: 180px; height: 180px;" />
        </div>
        <p>Would you like to purchase this song?{cnt_id}</p>
        <div>
            <img src="/files/web/coin_icon.png" class="coin-icon" style="width: 40px; height: 40px;" alt="Coin Icon" />
            <span style="color: #FFFFFF; font-size: 44px; font-family: Hiragino Kaku Gothic ProN, sans-serif;">{stage_price}</span>
        </div>
        """
        
    elif (cnt_type == "2"):
        your_html = f"""
        <div class="image-container">
            <img src="/files/image/icon/avatar/{cnt_id}.png" alt="Item Image" style="width: 180px; height: 180px; background-color: black; object-fit: contain; " />
        </div>
        <p>Would you like to purchase this avatar?</p>
        <div>
            <img src="/files/web/coin_icon.png" class="coin-icon" alt="Coin Icon" />
            <span>{avatar_price}</span>
        </div>
        """
        
    elif (cnt_type == "3"):
        your_html = f"""
        <div class="image-container">
            <img src="/files/image/icon/item/{cnt_id}.png" alt="Item Image" style="width: 180px; height: 180px;" />
        </div>
        <p>Would you like to purchase this item?</p>
        <div>
            <img src="/files/web/coin_icon.png" class="coin-icon" alt="Coin Icon" />
            <span>{item_price}</span>
        </div>
        """

    your_html += f"""
        <br>
        <div class="buttons" style="margin-top: 20px;">
            <a href="wwic://web_purchase_coin?cnt_type={cnt_type}&cnt_id={cnt_id}&num=1" class="bt_bg01" >Buy</a><br>
            <a href="wwic://web_shop?cnt_type={cnt_type}" class="bt_bg01" >Go Back</a>
        </div>
    """
    html_path = f"files/web_shop_detail.html"
    with open(html_path, "r", encoding="utf-8") as file:
        html_content = file.read().format(text=your_html, coin=coin)
        return html_content

@app.route('/buy_by_coin.php', methods=['GET'])
def buy_by_coin():
    global decrypted_fields
    cnt_type = decrypted_fields[b'cnt_type'][0].decode()
    cnt_id = int(decrypted_fields[b'cnt_id'][0].decode())
    num = int(decrypted_fields[b'num'][0].decode())
    device_id = decrypted_fields[b'vid'][0].decode()
    fail_url = """<?xml version="1.0" encoding="UTF-8"?><response><code>1</code><result_url>coin_error.php</result_url></response>"""

    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()

        # Fetch user data
        query = "SELECT my_stage, my_avatar, coin, item FROM daily_reward WHERE device_id = ?"
        cursor.execute(query, (device_id,))
        result = cursor.fetchone()

        if not result:
            return fail_url

        my_stage, my_avatar, coin, item = result
        coin = int(coin) if coin else 0

        # Process based on cnt_type
        if cnt_type == "1":
            if coin < stage_price:
                return fail_url
            
            stages = set(json.loads(my_stage)) if my_stage else set()
            if cnt_id not in stages:
                coin -= stage_price
                stages.add(cnt_id)
            else:
                return fail_url
            my_stage = json.dumps(list(stages))

        elif cnt_type == "2":
            if coin < avatar_price:
                return fail_url

            avatars = set(json.loads(my_avatar)) if my_avatar else set()
            if cnt_id not in avatars:
                coin -= avatar_price
                avatars.add(cnt_id)
            else:
                return fail_url
            my_avatar = json.dumps(list(avatars))

        elif cnt_type == "3":
            if coin < item_price:
                return fail_url

            # Deduct coin and append to item (no duplicate check)
            coin -= item_price
            items = json.loads(item) if item else []
            items.append(cnt_id)
            item = json.dumps(items)

        else:
            return fail_url

        # Update the database with the new values
        update_query = """
            UPDATE daily_reward
            SET my_stage = ?, my_avatar = ?, coin = ?, item = ?
            WHERE device_id = ?
        """
        cursor.execute(update_query, (my_stage, my_avatar, coin, item, device_id))
        connection.commit()

        response = ET.Element("response")

        # Add the main elements
        ET.SubElement(response, "code").text = "0"
        ET.SubElement(response, "result_url").text = "web_shop_result.php"
        ET.SubElement(response, "cnt_type").text = cnt_type
        ET.SubElement(response, "cnt_id").text = str(cnt_id)
        ET.SubElement(response, "num").text = str(num)

        # Conditionally add the stage_id
        if cnt_type == "1":
            ET.SubElement(response, "stage_id").text = str(cnt_id)

        # Convert the XML tree to a string
        response_string = ET.tostring(response, encoding="utf-8", method="xml").decode("utf-8")
        return response_string
    
@app.route('/web_shop_result.php', methods=['GET'])
def web_shop_result():
    return inform_page("SUCCESS:<br>Purchase successful.<br>Please close this page and the reward will arrive shortly.<br>If it took too long, try restarting the game.", 2)

@app.route('/coin_error.php', methods=['GET'])
def coin_error():
    return inform_page("FAILED:<br>Either you don't have enough coin,<br>or there were a duplicate order, and the reward will arrive shortly.", 2)

@app.route('/name_reset/', methods=['POST'])
def name_reset():
    global decrypted_fields
    username = request.form['username']
    password = request.form['password']
    if len(username) < 6 or len(username) > 21:
        return inform_page("FAILED:<br>Username must be between 6 and 20<br>characters long.", 0)
    if is_alphanumeric(username) == False:
        return inform_page("FAILED:<br>Username must consist entirely of<br>alphanumeric character.", 0)
    if username == password:
        return inform_page("FAILED:<br>Username cannot be the same as password.", 0)
    if check_blacklist(decrypted_fields) == False:
        return inform_page("FAILED:<br>Your account is banned and you are<br>not allowed to perform this action.", 0)
    user = get_user_data(decrypted_fields, "username")
    if user:
        user = user[0]
        with sqlite3.connect(DATABASE) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id FROM user WHERE username=?", (username,))
            exist = cursor.fetchone()
            cursor.close()
            if exist:
                return inform_page("FAILED:<br>Another user already has this name.", 0)
            password_hash = get_user_data(decrypted_fields, "password_hash")
            if password_hash:
                if verify_password(password, password_hash[0]):
                    set_user_data(decrypted_fields, "username", username)
                    return inform_page("SUCCESS:<br>Username updated.", 0)
                else:
                    return inform_page("FAILED:<br>Password is not correct.<br>Please try again.", 0)
            else:
                return inform_page("FAILED:<br>User have no password hash.<br>This should not happen.", 0)
    else:
        return inform_page("FAILED:<br>User does not exist.<br>This should not happen.", 0)

@app.route('/password_reset/', methods=['POST'])
def password_reset():
    global decrypted_fields
    old_password = request.form['old']
    password = request.form['new']
    user = get_user_data(decrypted_fields, "username")
    if user:
        user = user[0]
        if user == password:
            return inform_page("FAILED:<br>Username cannot be the same as password.", 0)
        if len(password) < 6:
            return inform_page("FAILED:<br>Password must have 6 or above characters.", 0)
        old_hash = get_user_data(decrypted_fields, "password_hash")
        if old_hash:
            if verify_password(old_password, old_hash[0]):
                hash_new = hash_password(password)
                set_user_data(decrypted_fields, "password_hash", hash_new)
                return inform_page("SUCCESS:<br>Password updated.", 0)
            else:
                return inform_page("FAILED:<br>Old password is not correct<br>Please try again.", 0)
        else:
            return inform_page("FAILED:<br>User have no password hash<br>This should not happen.", 0)
    else:
        return inform_page("FAILED:<br>User does not exist<br>This should not happen.", 0)

@app.route('/register/', methods=['POST'])
def register():
    global decrypted_fields
    username = request.form['username']
    password = request.form['password']
    if username == password:
        return inform_page("FAILED:<br>Username cannot be the same as password.", 0)
    if len(username) < 6 or len(username) > 20:
        return inform_page("FAILED:<br>Username must be between 6 and 20<br>characters long.", 0)
    if len(password) < 6:
        return inform_page("FAILED:<br>Password must have<br>6 or above characters.", 0)
    if is_alphanumeric(username) == False:
        return inform_page("FAILED:<br>Username must consist entirely of<br>alphanumeric character.", 0)
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM user WHERE username=?", (username,))
        user = cursor.fetchone()
        cursor.close()
        if user:
            return inform_page("FAILED:<br>Another user already has this name.", 0)
        cursor = connection.cursor()
        cursor.execute('''INSERT INTO user (username, password_hash, device_id, data, crc, timestamp) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', (username, hash_password(password), decrypted_fields[b'vid'][0].decode(), "", 0, ""))
        connection.commit()
        cursor.close()
        return inform_page("SUCCESS:<br>Account is registered.<br>You can now backup/restore your save file.<br>You can only log into one device at a time.", 0)

@app.route('/logout/', methods=['POST'])
def logout():
    global decrypted_fields
    if check_blacklist(decrypted_fields) == False:
        return inform_page("FAILED:<br>Your account is banned and you are<br>not allowed to perform this action.", 0)
    set_user_data(decrypted_fields, "device_id", '')
    return inform_page("Logout success.", 0)
    
@app.route('/login/', methods=['POST'])
def login():
    global decrypted_fields
    username = request.form['username']
    password = request.form['password']
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM user WHERE username = ?", (username,))
        user = cursor.fetchone()
        ##side channel attack goes brrrrr
        if user:
            cursor = connection.cursor()
            cursor.execute("SELECT password_hash FROM user WHERE id = ?", (user[0],))
            password_hash = cursor.fetchone()[0]
            if verify_password(password, password_hash):
                cursor.execute("UPDATE user SET device_id = ? WHERE id = ?", (decrypted_fields[b'vid'][0].decode(), user[0],))
                connection.commit()
                cursor.close()
                return inform_page("SUCCESS:<br>You are logged in.", 0)
            else:
                return inform_page("FAILED:<br>Username or password incorrect.", 0)
        else:
            return inform_page("FAILED:<br>Username or password incorrect.", 0)
        
@app.route('/load.php', methods=['GET'])
def load():
    global decrypted_fields
    data = get_user_data(decrypted_fields, "data")
    if data is not None:
        if data[0] == "":
            return """<response><code>12</code><message><ja>セーブデータが無いか、セーブデータが破損しているため、ロードできませんでした。</ja><en>Unable to load; either no save data exists, or the save data is corrupted.</en><fr>Chargement impossible : les données de sauvegarde sont absentes ou corrompues.</fr><it>Impossibile caricare. Non esistono dati salvati o quelli esistenti sono danneggiati.</it></message></response>"""
        else:
            crc = get_user_data(decrypted_fields, "crc")
            date = get_user_data(decrypted_fields, "timestamp")
            data = data[0]
            date = date[0]
            crc = crc[0]
            xml_data = """<?xml version="1.0" encoding="UTF-8"?><response><code>0</code>
                <data>{data}</data>
                <crc>{crc}</crc>
                <date>{date}</date>
                </response>""".format(data=data,crc=crc,date=date)
            return xml_data
    else:
        return """<response><code>10</code><message><ja>この機能を使用するには、まずアカウントを登録する必要があります。</ja><en>You need to register an account first before this feature can be used.</en><fr>Vous devez d'abord créer un compte avant de pouvoir utiliser cette fonctionnalité.</fr><it>È necessario registrare un account prima di poter utilizzare questa funzione.</it></message></response>"""
    
@app.route('/save.php', methods=['POST'])
def save():
    global decrypted_fields
    data = request.data.decode('utf-8')
    with sqlite3.connect(DATABASE) as connection:
        username = get_user_data(decrypted_fields, "username")
        if username:
            ## calculate crc and update both
            crc = crc32_decimal(data)
            time = datetime.now()
            formatted_time = time.strftime("%Y-%m-%d %H:%M:%S")
            cursor = connection.cursor()
            cursor.execute("UPDATE user SET data = ?, crc = ?, timestamp = ? WHERE device_id = ?", (data, crc, formatted_time , decrypted_fields[b'vid'][0].decode(),))
            connection.commit()
            cursor.close()
            return """<response><code>0</code></response>"""
        else:
            return """<response><code>10</code></response>"""
        
@app.route('/delete_account.php', methods=['GET'])
def delete_account():
    return """<?xml version="1.0" encoding="UTF-8"?><response><code>0</code><taito_id></taito_id></response>"""

@app.route('/<path:path>', methods=['GET'])
def get_file(path):
    file_path = os.path.join(root_folder, path)
    f_path = path.split("/")[0]
    if f_path not in allowed_folders:
        return jsonify({"error": "Access denied"}), 403
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return jsonify({"error": "File not found"}), 404

#Main
if __name__ == '__main__':
    if app.config['SSL_CERT'] and app.config['SSL_KEY']:
        app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config['DEBUG'], ssl_context=(app.config['SSL_CERT'], app.config['SSL_KEY']))
    else:
        app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config['DEBUG'])