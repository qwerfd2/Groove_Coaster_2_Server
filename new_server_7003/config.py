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

HOST = "127.0.0.1"
PORT = 9068
OVERRIDE_HOST = None

ACTUAL_HOST = "127.0.0.1"
ACTUAL_PORT = 9068

'''
Datecode of the 3 pak files.
三个pak文件的时间戳。
'''

MODEL = "202504125800"
TUNEFILE = "202507315817"
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

SIMULTANEOUS_LOGINS = 2

'''
Only the whitelisted playerID can use the service. Blacklist has priority over whitelist.
只有白名单的玩家ID才能使用服务。黑名单优先于白名单。
'''
AUTHORIZATION_NEEDED = False

'''
In addition to the whitelist/blacklist, set this to use discord/email authorization.
除了白名单/黑名单之外，设置此项以使用Discord/电子邮件授权。
0: Default blacklist/whitelist only
1: Email authorization w/ whitelist/blacklist
2: Discord authorization w/ whitelist/blacklist
'''

AUTHORIZATION_MODE = 0

# For auth mode 1
SMTP_HOST = "smtp.test.com"
SMTP_PORT = 465
SMTP_USER = "test@test.com"
SMTP_PASSWORD = "test"

# For auth mode 2
DISCORD_BOT_SECRET = "test"
DISCORD_BOT_API_KEY = "test"
BIND_SALT = "SET YOUR SALT HERE"

# Daily download limit per account in bytes (only activates for AUTHORIZATION_MODE 1 and 2)

DAILY_DOWNLOAD_LIMIT = 1073741824  # 1 GB
GRANDFATHERED_ACCOUNT_LIMIT = 0  # Web center access, grandfathered old accounts get access regardless of auth mode

'''
SSL certificate path. If left blank, use HTTP.
SSL证书路径 - 留空则使用HTTP
'''

SSL_CERT = None
SSL_KEY = None

'''
Whether to enable batch download functionality.
是否开启批量下载功能
'''

BATCH_DOWNLOAD_ENABLED = True
THREAD_COUNT = 3


'''
Starlette default debug
Starlette内置Debug
'''  

DEBUG = True