import os

'''
Do not change the name of this file.
不要改动这个文件的名称。 
'''
'''
IP and port of the server FOR THE DOWNLOAD LINKS.
下载链接：服务器的IP和端口。
If you want to use a domain name, set it in OVERRIDE_HOST
若想使用域名，请在OVERRIDE_HOST中设置。
'''

HOST = "192.168.0.106"
PORT = 9068
OVERRIDE_HOST = None

ACTUAL_HOST = "192.168.0.106"
ACTUAL_PORT = 9068

'''
Redis leaderboard caching configuration.
Redis排行榜缓存设置。
'''

REDIS_ADDRESS = "localhost"
USE_REDIS_CACHE = False

'''
Datecode of the 3 pak files.
三个pak文件的时间戳。
'''

MODEL = "202504125800"
TUNEFILE = "202507315816"
SKIN = "202404191149"

'''
Groove Coin-related settings.
GCoin相关设定。
'''  
STAGE_PRICE = 1
AVATAR_PRICE = 1
ITEM_PRICE = 2
COIN_REWARD = 1
START_COIN = 10

FMAX_PRICE = 300
EX_PRICE = 150

'''
Only the whitelisted playerID can use the service. Blacklist has priority over whitelist.
只有白名单的玩家ID才能使用服务。黑名单优先于白名单。
'''
AUTHORIZATION_NEEDED = False

'''
SSL证书路径 - 留空则使用HTTP
SSL certificate path. If left blank, use HTTP.
'''

SSL_CERT = None
SSL_KEY = None

'''
是否开启批量下载功能
Whether to enable batch download functionality.
'''

BATCH_DOWNLOAD_ENABLED = True
THREAD_COUNT = 3

'''
Starlette default debug
Starlette内置Debug
'''  

DEBUG = True

ROOT_FOLDER = os.path.dirname(os.path.abspath(__file__))