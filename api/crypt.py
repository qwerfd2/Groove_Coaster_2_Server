from Crypto.Cipher import AES
import re
import urllib.parse
from starlette.requests import Request

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

async def decrypt_fields(request: Request):
    url = str(request.url)
    match = re.search(r'\?(.*)', url)
    if match:
        original_field = match.group(1)
        decrypted_fields = urllib.parse.parse_qs(decryptAES(match.group(1))[:-1])

        return decrypted_fields, original_field
    else:
        return None, None