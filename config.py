import os

'''
Do not change the name of this file.
不要改动这个文件的名称。 
'''
'''
IP and port of the server.
服务器的IP和端口。
'''

HOST = "192.168.0.106"
PORT = 9070

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
TUNEFILE = "202504125800"
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
Starlette default debug
Starlette内置Debug
'''  

DEBUG = False

ROOT_FOLDER = os.path.dirname(os.path.abspath(__file__))