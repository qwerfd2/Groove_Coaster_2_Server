from starlette.config import Config
import os
'''
Do not change the name of this file.
不要改动这个文件的名称。 
'''

config = Config("config.env")

'''
IP and port of the server.
服务器的IP和端口。
'''

HOST = config("HOST", default="192.168.0.106")
PORT = int(config("PORT", default=9070))

ACTUAL_HOST = config("ACTUAL_HOST", default="192.168.0.106")
ACTUAL_PORT = int(config("ACTUAL_PORT", default=9070))

'''
Datecode of the 3 pak files.
三个pak文件的时间戳。
'''

MODEL = config("MODEL", cast=str, default="202504125800")
TUNEFILE = config("TUNEFILE", cast=str, default="202504125800")
SKIN = config("SKIN", cast=str, default="202404191149")

'''
Groove Coin-related settings.
GCoin相关设定。
'''  

STAGE_PRICE = config("STAGE_PRICE", cast=int, default=1)
AVATAR_PRICE = config("AVATAR_PRICE", cast=int, default=1)
ITEM_PRICE = config("ITEM_PRICE", cast=int, default=2)
COIN_REWARD = config("COIN_REWARD", cast=int, default=1)
START_COIN = config("START_COIN", cast=int, default=10)

'''
Only the whitelisted playerID can use the service. Blacklist has priority over whitelist.
只有白名单的玩家ID才能使用服务。黑名单优先于白名单。
'''

AUTHORIZATION_NEEDED = config("AUTHORIZATION_NEEDED", cast=bool, default=False)

'''
SSL证书路径 - 留空则使用HTTP
SSL certificate path. If left blank, use HTTP.
'''

SSL_CERT = config("SSL_CERT", default=None)
SSL_KEY = config("SSL_KEY", default=None)

'''
Flask default debug
Flask内置Debug
'''  

DEBUG = config("DEBUG", cast=bool, default=False)

ROOT_FOLDER = os.path.dirname(os.path.abspath(__file__))
