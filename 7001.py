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

try:
    with open("song_list.json", 'r', encoding="utf-8") as file:
        song_list = json.load(file)
except Exception as e:
    print(f"An unexpected error occurred when loading song_list.json: {e}")

try:
    with open("avatar_list.json", 'r', encoding="utf-8") as file:
        avatar_list = json.load(file)
except Exception as e:
    print(f"An unexpected error occurred when loading avatar_list.json: {e}")

try:
    with open("item_list.json", 'r', encoding="utf-8") as file:
        item_list = json.load(file)
except Exception as e:
    print(f"An unexpected error occurred when loading item_list.json: {e}")

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

start_stages = [7,23,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,88,89,90,91,92,93,94,95,96,97,98,99,214]
# 214 is tutorial song.

start_avatars = []

exclude_stage_exp = [121,134,166,167,168,169,170,213,214,215,225,277] # 134 and 170 unoccupied dummy tracks (filled with Departure -Remix-),
#121 (and 93-96 lady gaga songs) removed (can be enabled by patching stageParam:isAvailable, or change the last byte before next song's name - 1 from 01 to 03 in stage_param.dat. 
# Rest are exp unlocked songs.
exclude_avatar_exp = [28,29]

try:
    with open("exp_unlocked_songs.json", 'r', encoding="utf-8") as file:
        exp_unlocked_songs = json.load(file)
except Exception as e:
    print(f"An unexpected error occurred when loading exp_unlocked_songs.json: {e}")

special_titles = [1, 2, 4431, 4432, 4601, 4602, 4611, 4612, 4621, 4622, 4631, 4632, 5111, 5112, 5121, 5122, 5131, 5132, 10001, 10002, 20001, 20002, 20003, 20004, 20005, 20006, 30001, 30002, 40001, 40002, 50001, 50002, 60001, 60002, 70001, 70002, 80001, 80002, 90001, 90002, 100001, 100002, 110001, 110002, 120001, 120002, 130001, 130002, 140001, 140002, 140003, 140004, 150001, 150002, 150003, 150004, 160001, 160002, 160003, 160004, 170001, 170002, 170003, 170004, 180001, 180002, 180003, 180004, 190001, 190002, 190003, 190004, 200001, 200002, 200003, 200004, 210001, 210002, 210003, 210004, 210005, 210006, 210007, 210008, 210009, 210010, 210011, 210012, 210013, 210014, 240001, 240002, 240003, 240004, 240005, 240006, 240007, 240008, 240009, 240010, 240011, 240012]

god_titles = [220001, 220002, 220003, 220004, 220005, 220006, 220007, 220008, 220009, 220010, 220011, 220012, 220013, 220014, 220015, 220016, 220017, 220018, 220019, 220020, 220021, 220022, 220023, 220024, 220025, 220026, 220027, 220028, 220029, 220030, 220031, 220032, 220033, 220034, 220035, 220036, 220037, 220038, 220039, 220040, 220041, 220042, 220043, 220044, 220045, 220046, 220047, 220048, 220049, 220050, 220051, 220052, 220053, 220054, 220055, 220056, 220057, 220058, 220059, 220060, 220061, 220062, 220063, 220064, 220065, 220066, 220067, 220068, 220069, 220070, 220071, 220072, 220073, 220074, 220075, 220076, 220077, 220078, 220079, 220080, 220081, 220082, 220083, 220084, 220085, 220086, 220087, 220088, 220089, 220090, 220091, 220092, 220093, 220094, 220095, 220096, 220097, 220098, 220099, 220100, 220101, 220102]

master_titles = [12, 22, 32, 42, 52, 62, 72, 82, 92, 102, 112, 122, 132, 142, 152, 162, 172, 182, 192, 202, 212, 222, 232, 242, 252, 262, 272, 282, 292, 302, 312, 322, 332, 342, 352, 362, 372, 382, 392, 402, 412, 422, 432, 442, 452, 462, 472, 482, 492, 502, 512, 522, 532, 542, 552, 562, 572, 582, 592, 602, 612, 622, 632, 642, 652, 662, 672, 682, 692, 702, 712, 722, 732, 742, 752, 762, 772, 782, 792, 802, 812, 822, 832, 842, 852, 862, 872, 882, 892, 902, 912, 922, 972, 982, 992, 1002, 1012, 1022, 1032, 1042, 1052, 1062, 1072, 1082, 1092, 1102, 1112, 1122, 1132, 1142, 1152, 1162, 1172, 1182, 1192, 1202, 1222, 1232, 1242, 1252, 1262, 1272, 1282, 1292, 1302, 1312, 1322, 1332, 1342, 1352, 1362, 1372, 1382, 1392, 1402, 1412, 1422, 1432, 1442, 1452, 1462, 1472, 1482, 1492, 1502, 1512, 1522, 1532, 1542, 1552, 1562, 1572, 1582, 1592, 1602, 1612, 1622, 1632, 1642, 1652, 1662, 1672, 1682, 1692, 1702, 1712, 1722, 1732, 1742, 1752, 1762, 1772, 1782, 1792, 1802, 1812, 1822, 1832, 1842, 1852, 1862, 1872, 1882, 1892, 1902, 1912, 1922, 1932, 1942, 1952, 1962, 1972, 1982, 1992, 2002, 2012, 2022, 2032, 2042, 2052, 2062, 2072, 2082, 2092, 2102, 2112, 2122, 2132, 2152, 2162, 2172, 2182, 2192, 2202, 2212, 2222, 2232, 2242, 2252, 2262, 2272, 2282, 2292, 2302, 2312, 2322, 2332, 2342, 2352, 2362, 2372, 2382, 2392, 2402, 2412, 2422, 2432, 2442, 2452, 2462, 2472, 2482, 2492, 2502, 2512, 2522, 2532, 2542, 2552, 2562, 2572, 2582, 2592, 2602, 2612, 2622, 2632, 2642, 2652, 2662, 2672, 2682, 2692, 2702, 2712, 2722, 2732, 2742, 2752, 2762, 2782, 2792, 2802, 2812, 2822, 2832, 2842, 2852, 2862, 2872, 2882, 2892, 2902, 2912, 2922, 2932, 2942, 2952, 2962, 2972, 2982, 2992, 3002, 3012, 3022, 3032, 3042, 3052, 3062, 3072, 3082, 3092, 3102, 3112, 3122, 3132, 3142, 3152, 3162, 3172, 3182, 3192, 3202, 3212, 3222, 3232, 3242, 3252, 3262, 3272, 3282, 3292, 3302, 3312, 3322, 3332, 3342, 3352, 3362, 3372, 3382, 3392, 3402, 3412, 3422, 3432, 3442, 3452, 3462, 3472, 3482, 3492, 3502, 3512, 3522, 3532, 3542, 3552, 3562, 3572, 3582, 3592, 3602, 3612, 3622, 3632, 3642, 3652, 3662, 3672, 3682, 3692, 3702, 3712, 3722, 3732, 3742, 3752, 3762, 3772, 3782, 3792, 3802, 3812, 3822, 3832, 3842, 3852, 3862, 3872, 3882, 3892, 3902, 3912, 3922, 3932, 3942, 3952, 3962, 3982, 3992, 4002, 4012, 4022, 4032, 4042, 4052, 4062, 4072, 4082, 4092, 4102, 4112, 4122, 4132, 4142, 4152, 4162, 4172, 4182, 4192, 4202, 4212, 4222, 4232, 4242, 4252, 4262, 4272, 4282, 4292, 4302, 4312, 4322, 4332, 4342, 4352, 4362, 4372, 4382, 4392, 4402, 4412, 4422, 4442, 4452, 4462, 4472, 4482, 4492, 4502, 4512, 4522, 4532, 4542, 4552, 4562, 4572, 4582, 4592, 4642, 4652, 4662, 4672, 4682, 4692, 4702, 4712, 4722, 4732, 4742, 4752, 4762, 4772, 4782, 4792, 4802, 4812, 4822, 4832, 4842, 4862, 4872, 4882, 4892, 4902, 4912, 4922, 4932, 4942, 4952, 4962, 4972, 4982, 4992, 5002, 5012, 5022, 5032, 5042, 5052, 5062, 5072, 5082, 5092, 5102, 5142, 5152, 5162, 5172, 5182, 5192, 5202, 5212, 5222, 5232, 5242, 5252, 5262, 5272, 5282, 5292, 5302, 5312, 5322, 5332, 5342, 5352, 5362, 5372, 5382, 5392, 5402, 5412, 5422, 5432, 5442, 5452, 5462, 5472, 5482, 5492, 5502, 5512, 5522, 5532, 5542, 5552, 5562, 5572, 5582, 5592, 5602, 5612, 5622, 5632, 5642, 5652, 5662, 5672, 5682, 5692, 5702, 5712, 5722, 5732, 5742, 5752, 5762, 5772, 5782, 5792, 5802, 5812, 5822, 5832, 5842, 5852, 5862, 5872, 5882, 5892, 5902, 5912, 5922, 5932, 5942, 5952, 5962, 5972, 5982, 5992, 6002, 6012, 6022, 6032, 6042, 6052, 6062, 6072, 6082, 6092, 6102, 6112, 6122, 6132, 6142, 6152]

normal_titles = [11, 21, 31, 41, 51, 61, 71, 81, 91, 101, 111, 121, 131, 141, 151, 161, 171, 181, 191, 201, 211, 221, 231, 241, 251, 261, 271, 281, 291, 301, 311, 321, 331, 341, 351, 361, 371, 381, 391, 401, 411, 421, 431, 441, 451, 461, 471, 481, 491, 501, 511, 521, 531, 541, 551, 561, 571, 581, 591, 601, 611, 621, 631, 641, 651, 661, 671, 681, 691, 701, 711, 721, 731, 741, 751, 761, 771, 781, 791, 801, 811, 821, 831, 841, 851, 861, 871, 881, 891, 901, 911, 921, 971, 981, 991, 1001, 1011, 1021, 1031, 1041, 1051, 1061, 1071, 1081, 1091, 1101, 1111, 1121, 1131, 1141, 1151, 1161, 1171, 1181, 1191, 1201, 1221, 1231, 1241, 1251, 1261, 1271, 1281, 1291, 1301, 1311, 1321, 1331, 1341, 1351, 1361, 1371, 1381, 1391, 1401, 1411, 1421, 1431, 1441, 1451, 1461, 1471, 1481, 1491, 1501, 1511, 1521, 1531, 1541, 1551, 1561, 1571, 1581, 1591, 1601, 1611, 1621, 1631, 1641, 1651, 1661, 1671, 1681, 1691, 1701, 1711, 1721, 1731, 1741, 1751, 1761, 1771, 1781, 1791, 1801, 1811, 1821, 1831, 1841, 1851, 1861, 1871, 1881, 1891, 1901, 1911, 1921, 1931, 1941, 1951, 1961, 1971, 1981, 1991, 2001, 2011, 2021, 2031, 2041, 2051, 2061, 2071, 2081, 2091, 2101, 2111, 2121, 2131, 2151, 2161, 2171, 2181, 2191, 2201, 2211, 2221, 2231, 2241, 2251, 2261, 2271, 2281, 2291, 2301, 2311, 2321, 2331, 2341, 2351, 2361, 2371, 2381, 2391, 2401, 2411, 2421, 2431, 2441, 2451, 2461, 2471, 2481, 2491, 2501, 2511, 2521, 2531, 2541, 2551, 2561, 2571, 2581, 2591, 2601, 2611, 2621, 2631, 2641, 2651, 2661, 2671, 2681, 2691, 2701, 2711, 2721, 2731, 2741, 2751, 2761, 2781, 2791, 2801, 2811, 2821, 2831, 2841, 2851, 2861, 2871, 2881, 2891, 2901, 2911, 2921, 2931, 2941, 2951, 2961, 2971, 2981, 2991, 3001, 3011, 3021, 3031, 3041, 3051, 3061, 3071, 3081, 3091, 3101, 3111, 3121, 3131, 3141, 3151, 3161, 3171, 3181, 3191, 3201, 3211, 3221, 3231, 3241, 3251, 3261, 3271, 3281, 3291, 3301, 3311, 3321, 3331, 3341, 3351, 3361, 3371, 3381, 3391, 3401, 3411, 3421, 3431, 3441, 3451, 3461, 3471, 3481, 3491, 3501, 3511, 3521, 3531, 3541, 3551, 3561, 3571, 3581, 3591, 3601, 3611, 3621, 3631, 3641, 3651, 3661, 3671, 3681, 3691, 3701, 3711, 3721, 3731, 3741, 3751, 3761, 3771, 3781, 3791, 3801, 3811, 3821, 3831, 3841, 3851, 3861, 3871, 3881, 3891, 3901, 3911, 3921, 3931, 3941, 3951, 3961, 3981, 3991, 4001, 4011, 4021, 4031, 4041, 4051, 4061, 4071, 4081, 4091, 4101, 4111, 4121, 4131, 4141, 4151, 4161, 4171, 4181, 4191, 4201, 4211, 4221, 4231, 4241, 4251, 4261, 4271, 4281, 4291, 4301, 4311, 4321, 4331, 4341, 4351, 4361, 4371, 4381, 4391, 4401, 4411, 4421, 4441, 4451, 4461, 4471, 4481, 4491, 4501, 4511, 4521, 4531, 4541, 4551, 4561, 4571, 4581, 4591, 4641, 4651, 4661, 4671, 4681, 4691, 4701, 4711, 4721, 4731, 4741, 4751, 4761, 4771, 4781, 4791, 4801, 4811, 4821, 4831, 4841, 4861, 4871, 4881, 4891, 4901, 4911, 4921, 4931, 4941, 4951, 4961, 4971, 4981, 4991, 5001, 5011, 5021, 5031, 5041, 5051, 5061, 5071, 5081, 5091, 5101, 5141, 5151, 5161, 5171, 5181, 5191, 5201, 5211, 5221, 5231, 5241, 5251, 5261, 5271, 5281, 5291, 5301, 5311, 5321, 5331, 5341, 5351, 5361, 5371, 5381, 5391, 5401, 5411, 5421, 5431, 5441, 5451, 5461, 5471, 5481, 5491, 5501, 5511, 5521, 5531, 5541, 5551, 5561, 5571, 5581, 5591, 5601, 5611, 5621, 5631, 5641, 5651, 5661, 5671, 5681, 5691, 5701, 5711, 5721, 5731, 5741, 5751, 5761, 5771, 5781, 5791, 5801, 5811, 5821, 5831, 5841, 5851, 5861, 5871, 5881, 5891, 5901, 5911, 5921, 5931, 5941, 5951, 5961, 5971, 5981, 5991, 6001, 6011, 6021, 6031, 6041, 6051, 6061, 6071, 6081, 6091, 6101, 6111, 6121, 6131, 6141, 6151]

title_lists = {
    0: special_titles,
    1: normal_titles,
    2: master_titles,
    3: god_titles,
}

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
            item TEXT,
            day INT,
            coin INT,
            lvl INT,
            title INT,
            avatar INT       
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
    elif mode == 3:
        mode = "/files/web/ttl_title.png"
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

            for avatar_id in my_avatar:
                avatar_elem = ET.Element("my_avatar")
                avatar_elem.text = str(avatar_id)
                root.append(avatar_elem)

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

        if row is not None:
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
            print("bonus-add profile")
            cursor.execute("""
                INSERT INTO daily_reward (device_id, day, timestamp, my_avatar, my_stage, coin, item, lvl, title, avatar)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (device_id, 1, formatted_time, json.dumps(start_avatars), json.dumps(start_stages), 10, "[]", 1, 1, 1))
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
                last_row_id = records[0][0]
                if (score > records[0][1]):
                    do_update_sid = True
            else:
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
                last_row_id = records[0][0]
                if (score > records[0][1]):
                    do_update_vid = True
            else:
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

    # Update player profile regardless. Check for exp unlocked songs too
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()

        query_command = "SELECT my_stage FROM daily_reward WHERE device_id = ?"
        cursor.execute(query_command, (device_id,))
        result = cursor.fetchone()

        my_stage = set(json.loads(result[0])) if result and result[0] else set(start_stages)

        current_exp = int(stts.split(",")[0])
        for song in exp_unlocked_songs:
            if song["lvl"] <= current_exp:
                my_stage.add(song["id"])

        my_stage = sorted(my_stage)

        update_command = """
        UPDATE daily_reward SET lvl = ?, avatar = ?, my_stage = ? WHERE device_id = ?;
        """
        cursor.execute(update_command, (current_exp, int(avatar), json.dumps(my_stage), device_id))
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

@app.route('/web_shop.php', methods=['GET', 'POST'])
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
            for idx, i in enumerate(range(100, 616)):
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

@app.route('/web_shop_detail.php', methods=['GET', 'POST'])
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
    html = ""

    if (cnt_type == "1"):
        song = song_list[cnt_id]
        difficulty_levels = "/".join(map(str, song.get("difficulty_levels", [])))
        song_stage_price = stage_price
        if (len(song["difficulty_levels"]) == 6):
            song_stage_price = stage_price * 2
        html = f"""
        <div class="image-container">
            <img src="/files/image/icon/shop/{cnt_id}.jpg" alt="Item Image" style="width: 180px; height: 180px;" />
        </div>
        <p>Would you like to purchase this song?</p>
        <div>
            <p>{song.get("name_en")} - {song.get("author_en")}</p>
            <p>Difficulty Levels: {difficulty_levels}</p>
        </div>
        <div>
            <img src="/files/web/coin_icon.png" class="coin-icon" style="width: 40px; height: 40px;" alt="Coin Icon" />
            <span style="color: #FFFFFF; font-size: 44px; font-family: Hiragino Kaku Gothic ProN, sans-serif;">{song_stage_price}</span>
        </div>
        """

    elif (cnt_type == "2"):
        avatar = next((item for item in avatar_list if item.get("id") == cnt_id), None)
        if avatar:
            html = f"""
            <div class="image-container">
                <img src="/files/image/icon/avatar/{cnt_id}.png" alt="Item Image" style="width: 180px; height: 180px; background-color: black; object-fit: contain;" />
            </div>
            <p>Would you like to purchase this avatar?</p>
            <div>
                <p>{avatar.get("name")}</p>
                <p>Effect: {avatar.get("effect")}</p>
            </div>
            <div>
                <img src="/files/web/coin_icon.png" class="coin-icon" style="width: 40px; height: 40px;" alt="Coin Icon" />
                <span>{avatar_price}</span>
            </div>
            """
        else:
            html = "<p>Avatar not found.</p>"

    elif (cnt_type == "3"):
        item = next((item for item in item_list if item.get("id") == cnt_id), None)
        if item:
            html = f"""
            <div class="image-container">
                <img src="/files/image/icon/item/{cnt_id}.png" alt="Item Image" style="width: 180px; height: 180px;" />
            </div>
            <p>Would you like to purchase this item?</p>
            <div>
                <p>{item.get("name")}</p>
                <p>Effect: {item.get("effect")}</p>
            </div>
            <div>
                <img src="/files/web/coin_icon.png" class="coin-icon" style="width: 40px; height: 40px;" alt="Coin Icon" />
                <span>{item_price}</span>
            </div>
            """
        else:
            html = "<p>Item not found.</p>"


    html += f"""
        <br>
        <div class="buttons" style="margin-top: 20px;">
            <a href="wwic://web_purchase_coin?cnt_type={cnt_type}&cnt_id={cnt_id}&num=1" class="bt_bg01" >Buy</a><br>
            <a href="wwic://web_shop?cnt_type={cnt_type}" class="bt_bg01" >Go Back</a>
        </div>
    """

    with open(f"files/web_shop_detail.html", "r", encoding="utf-8") as file:
        html_content = file.read().format(text=html, coin=coin)
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
            song_stage_price = stage_price
            if (len(song_list[cnt_id]["difficulty_levels"]) == 6):
                song_stage_price = song_stage_price * 2

            if coin < song_stage_price:
                return fail_url
            
            stages = set(json.loads(my_stage)) if my_stage else set()
            if cnt_id not in stages:
                coin -= song_stage_price
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
    global decrypted_fields
    cnt_type = decrypted_fields[b'cnt_type'][0].decode()
    return inform_page(f"""SUCCESS:<br>Purchase successful.<br>Please close this page and the reward will arrive shortly.<br>If it took too long, try restarting the game.<br><a href='wwic://web_shop?cnt_type={cnt_type}' class='bt_bg01' >Go Back</a>""", 2)

@app.route('/coin_error.php', methods=['GET'])
def coin_error():
    return inform_page(f"""FAILED:<br>Either you don't have enough coin,<br>or there were a duplicate order, and the reward will arrive shortly.""", 2)

@app.route('/ranking.php/', methods=['GET'])
def ranking():
    global decrypted_fields
    device_id = decrypted_fields[b'vid'][0].decode()

    html = "<ul class='song-list'>"
    for index, song in enumerate(song_list):
        encrypted_mass = encryptAES(("vid=" + device_id + "&song_id=" + str(index) + "&mode=3&dummy=").encode("utf-8"))
        song_name = song.get("name_en", "Unknown")
        href = f"/ranking_detail.php?{encrypted_mass}"
        html += f'''
            <li class="song-item">
                <a href="{href}" class="song-button">{song_name}</a>
            </li>
        '''
    html += "</ul>"

    with open(f"files/ranking.html", "r", encoding="utf-8") as file:
        html_content = file.read().format(text=html)
        return html_content

@app.route('/ranking_detail.php/', methods=['GET'])
def ranking_detail():
    global decrypted_fields
    device_id = decrypted_fields[b'vid'][0].decode()
    song_id = int(decrypted_fields[b'song_id'][0].decode())
    mode = int(decrypted_fields[b'mode'][0].decode())

    song_name = song_list[song_id]["name_en"]
    difficulty_levels = song_list[song_id]["difficulty_levels"]

    html = f"""
        <div style="text-align: center; font-size: 36px; margin-bottom: 20px;">
            {song_name}
        </div>
    """

    button_labels = ["easy", "normal", "hard"]
    button_modes = [1, 2, 3]

    if (len(difficulty_levels) == 6):
        button_labels.extend(["ac-easy", "ac-normal", "ac-hard"])
        button_modes.extend([11, 12, 13])

    row_start = '<div class="button-row">'
    row_end = '</div>'
    row_content = []

    for i, (label, mode_value) in enumerate(zip(button_labels, button_modes)):
        if mode_value == mode:
            row_content.append(f"""
                <div class="bt_bg01_ac">
                    {label.capitalize()}
                </div>
            """)
        else:
            encrypted_mass = encryptAES(("vid=" + device_id + "&song_id=" + str(song_id) + "&mode=" + str(mode_value) + "&dummy=").encode("utf-8"))
            row_content.append(f"""
                <a href="/ranking_detail.php?{encrypted_mass}" class="bt_bg01">
                    {label.capitalize()}
                </a>
            """)

        if len(row_content) == 3:
            html += row_start + ''.join(row_content) + row_end
            row_content = []  # Reset row content

    play_results = None
    user_result = None
    device_result = None
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        query = "SELECT * FROM result WHERE id = ? AND mode = ? ORDER BY CAST(score AS INTEGER) DESC"
        cursor.execute(query, (song_id, mode))
        play_results = cursor.fetchall()

        query = "SELECT * FROM user WHERE device_id = ?"
        cursor.execute(query, (device_id,))
        user_result = cursor.fetchone()

        query = "SELECT * FROM daily_reward WHERE device_id = ?"
        cursor.execute(query, (device_id,))
        device_result = cursor.fetchone()

    user_id = user_result[0] if user_result else None
    username = user_result[1] if user_result else f"Guest({device_id[-6:]})"
    play_record = None

    # Check if the user's device ID is in play_results
    if user_id:
        play_record = next((record for record in play_results if int(record[3]) == user_id), None)

    if not play_record:
        play_record = next((record for record in play_results if record[1] == device_id and record[3] is None), None)

    player_rank = None
    avatar_index = str(play_record[7]) if play_record else "1"
    user_score = play_record[8] if play_record else 0
    for rank, result in enumerate(play_results, start=1):
        if user_result and int(result[3]) == user_id:
            player_rank = rank
            break
        elif result[1] == device_id and result[3] is None:
            player_rank = rank
            break
    # Generate player element
    html += f"""
    <div class="player-element">
        <span class="rank">You<br>{"#" + str(player_rank) if player_rank else "N/A"}</span>
        <img src="/files/image/icon/avatar/{avatar_index}.png" class="avatar" alt="Player Avatar">
        <div class="player-info">
            <div class="name">{username}</div>
            <img src="/files/image/title/{device_result[9]}.png" class="title" alt="Player Title">
        </div>
        <div class="player-score">{user_score}</div>
    </div>
    """
    # main leaderboard
    html += """
    <div class="leaderboard-container">
    """

    for rank, record in enumerate(play_results, start=1):
        username = f"Guest({record[1][-6:]})"
        device_info = None
        if record[3]:
            cursor.execute("SELECT username FROM user WHERE id = ?", (record[3],))
            user_data = cursor.fetchone()
            if user_data:
                username = user_data[0]
            cursor.execute("SELECT title FROM daily_reward WHERE device_id = ?", (record[1],))
            device_title = cursor.fetchone()
            if device_title:
                device_info = device_title[0]

        avatar_id = record[7] if record[7] else 1
        avatar_url = f"/files/image/icon/avatar/{avatar_id}.png"

        score = record[8]

        html += f"""
        <div class="leaderboard-player">
            <div class="rank">#{rank}</div>
            <img class="avatar" src="{avatar_url}" alt="Avatar">
            <div class="leaderboard-info">
                <div class="name">{username}</div>
                <div class="title"><img src="/files/image/title/{device_info}.png" alt="Title"></div>
            </div>
            <div class="leaderboard-score">{score}</div>
        </div>
        """

    html += "</div>"
    encrypted_mass = encryptAES(("vid=" + device_id + "&dummy=").encode("utf-8"))
    html += f"""
    <a href="/ranking.php?{encrypted_mass}" class="bt_bg01_ifedup" style="margin: 20px auto; display: block; text-align: center;">
        Go Back
    </a>
    """

    with open(f"files/ranking.html", "r", encoding="utf-8") as file:
        html_content = file.read().format(text=html)
        return html_content

@app.route('/status.php/', methods=['GET'])
def status():
    global decrypted_fields
    device_id = decrypted_fields[b'vid'][0].decode()
    set_title = int(decrypted_fields[b'set_title'][0].decode()) if b'set_title' in decrypted_fields else None
    page_id = int(decrypted_fields[b'page_id'][0].decode()) if b'page_id' in decrypted_fields else 0

    if (set_title):
        with sqlite3.connect(DATABASE) as connection:
            cursor = connection.cursor()
            update_query = """
                UPDATE daily_reward SET title = ? WHERE device_id = ?
            """
            cursor.execute(update_query, (str(set_title), device_id))
            connection.commit()

    html = ""

    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()

        query = "SELECT * FROM daily_reward WHERE device_id = ?"
        cursor.execute(query, (device_id,))
        user_data = cursor.fetchone()
        user_name = user_data[1]

        query = "SELECT * FROM user WHERE device_id = ?"
        cursor.execute(query, (user_data[1],))
        user_result = cursor.fetchone()
        if user_result:
            user_name = user_result[1]
        
        if user_data:
            player_element = f"""
                <div class="player-element">
                    <img src="/files/image/icon/avatar/{user_data[10]}.png" class="avatar" alt="Player Avatar">
                    <div class="player-info">
                        <div class="name">{user_name}</div>
                        <img src="/files/image/title/{user_data[9]}.png" class="title" alt="Player Title">
                    </div>
                    <div class="player-score">Level {user_data[8]}</div>
                </div>
            """
            html += player_element

    page_name = ["Special", "Normal", "Master", "God"]

    buttons_html = '<div class="button-row">'

    for i in range(0, 4):
        if i == page_id:
            # Current button
            buttons_html += f"""
                <div class="bt_bg01_ac" >
                    {page_name[i]}
                </div>
            """
        else:
            encrypted_mass = encryptAES(f"vid={device_id}&page_id={i}&dummy=".encode("utf-8"))
            buttons_html += f"""
                <a href="/status.php?{encrypted_mass}" class="bt_bg01" >
                    {page_name[i]}
                </a>
            """
    buttons_html += '</div>'
    html += f"<div style='text-align: center; margin-top: 20px;'>{buttons_html}</div>"

    selected_titles = title_lists.get(page_id, [])

    titles_html = '<div class="title-list">'

    for index, num in enumerate(selected_titles):
        if index % 2 == 0:
            if index != 0:
                titles_html += '</div>'
            titles_html += '<div class="title-row">'

        if num == int(user_data[9]):
            titles_html += f"""
                <img src="/files/image/title/{num}.png" alt="Title {num}" class="title-image-selected">
            """
        else:
            encrypted_mass = encryptAES(f"vid={device_id}&title_id={num}&page_id={page_id}&dummy=".encode("utf-8"))
            titles_html += f"""
                <a href="/set_title.php?{encrypted_mass}" class="title-link">
                    <img src="/files/image/title/{num}.png" alt="Title {num}" class="title-image">
                </a>
            """

    titles_html += '</div></div>'

    html += titles_html

    with open(f"files/status.html", "r", encoding="utf-8") as file:
        html_content = file.read().format(text=html)
        return html_content

@app.route('/set_title.php/', methods=['GET'])
def set_title():
    global decrypted_fields
    device_id = decrypted_fields[b'vid'][0].decode()
    page_id = decrypted_fields[b'page_id'][0].decode()
    title_id = decrypted_fields[b'title_id'][0].decode()
    current_title = 1

    html = ""

    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        query = "SELECT title FROM daily_reward WHERE device_id = ?"
        cursor.execute(query, (device_id,))
        user_data = cursor.fetchone()
        if user_data:
            current_title = user_data[0]

    confirm_url = encryptAES(
        f"vid={device_id}&page_id={page_id}&set_title={title_id}&dummy=".encode("utf-8")
    )
    go_back_url = encryptAES(
        f"vid={device_id}&page_id={page_id}&dummy=".encode("utf-8")
    )

    html += f"""
        <p>Would you like to change your title?<br>Current Title:</p>
        <img src="/files/image/title/{current_title}.png" alt="Current Title" class="title-image">
        <p>New Title:</p>
        <img src="/files/image/title/{title_id}.png" alt="New Title" class="title-image">
        <div class="button-container">
            <a href="/status.php?{confirm_url}" class="bt_bg01">Confirm</a>
            <a href="/status.php?{go_back_url}" class="bt_bg01">Go back</a>
        </div>
    """

    return inform_page(html, 1)

@app.route('/mission.php/', methods=['GET'])
def mission():
    global exp_unlocked_songs, song_list

    html = f"""<div class="f90 a_center pt50" >Play Music to level up and unlock free songs!<br>Songs can only be unlocked when you play online.</div><div class='mission-list'>"""

    # Render the mission list
    for song in exp_unlocked_songs:
        song_id = song["id"]
        level_required = song["lvl"]
        song_name = song_list[song_id]["name_en"] if song_id < len(song_list) else "Unknown Song"
        
        html += f"""
            <div class="mission-row">
                <div class="mission-level">Level {level_required}</div>
                <div class="mission-song">{song_name}</div>
            </div>
        """

    html += "</div>"

    with open(f"files/mission.html", "r", encoding="utf-8") as file:
        html_content = file.read().format(text=html)
        return html_content

@app.route('/name_reset/', methods=['POST'])
def name_reset():
    global decrypted_fields
    username = request.form['username']
    password = request.form['password']
    if len(username) < 6 or len(username) > 21:
        return inform_page("FAILED:<br>Username must be between 6 and 20 characters long.", 0)
    if is_alphanumeric(username) == False:
        return inform_page("FAILED:<br>Username must consist entirely of alphanumeric character.", 0)
    if username == password:
        return inform_page("FAILED:<br>Username cannot be the same as password.", 0)
    if check_blacklist(decrypted_fields) == False:
        return inform_page("FAILED:<br>Your account is banned and you are not allowed to perform this action.", 0)
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
    # this only tricks the client to clear its local data for now
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