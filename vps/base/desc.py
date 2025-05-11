import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class ConfigCrypto:
    def __init__(self, master_key: str):
        self.master_key = hashlib.md5(master_key.encode()).digest()
        self.iv = hashlib.md5(master_key[::-1].encode()).digest()[:16]

    def encrypt(self, plaintext: str) -> str:
        cipher = AES.new(self.master_key, AES.MODE_CBC, self.iv)
        padded_data = pad(plaintext.encode(), AES.block_size)
        encrypted = cipher.encrypt(padded_data)
        return base64.b64encode(encrypted).decode()

    def decrypt(self, ciphertext: str) -> str:
        cipher = AES.new(self.master_key, AES.MODE_CBC, self.iv)
        encrypted = base64.b64decode(ciphertext)
        decrypted = cipher.decrypt(encrypted)
        return unpad(decrypted, AES.block_size).decode()
