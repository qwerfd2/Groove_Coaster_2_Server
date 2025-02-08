class Config:
    '''
    Do not change the name of this file.
    不要改动这个文件的名称。 
    '''
    '''
    IP and port of the server.
    服务器的IP和端口。
    '''
    HOST = '192.168.0.106'
    PORT = 9068
    '''
    Datecode of the 3 pak files.
    三个pak文件的时间戳。
    '''
    MODEL = '202404221226'
    TUNEFILE = '202404221247'
    SKIN = '202404191148'
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
    SSL_CERT = ''  # *.pem
    SSL_KEY = ''  # *.key
    '''
    Flask default debug
    Flask内置Debug
    '''  
    DEBUG = True
