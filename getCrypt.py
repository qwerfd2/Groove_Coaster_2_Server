from Crypto.Cipher import AES
str = input("enter string:")
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

print(decryptAES(str))