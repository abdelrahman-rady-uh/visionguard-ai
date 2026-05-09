import hashlib
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from backend.config import SECRET_KEY_PATH


class SecurityService:
    def __init__(self):
        os.makedirs(os.path.dirname(SECRET_KEY_PATH), exist_ok=True)
        self.key = self._load_or_create_key()

    def _load_or_create_key(self):
        if os.path.exists(SECRET_KEY_PATH):
            with open(SECRET_KEY_PATH, "rb") as f:
                key = f.read()
            if len(key) == 32:
                return key
        key = AESGCM.generate_key(bit_length=256)
        with open(SECRET_KEY_PATH, "wb") as f:
            f.write(key)
        return key

    def sha256_file(self, file_path):
        sha = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                sha.update(chunk)
        return sha.hexdigest()

    def encrypt_file(self, src_path, encrypted_path):
        aesgcm = AESGCM(self.key)
        nonce = os.urandom(12)
        with open(src_path, "rb") as f:
            plaintext = f.read()
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        with open(encrypted_path, "wb") as f:
            f.write(nonce + ciphertext)
        return encrypted_path

    def decrypt_file(self, encrypted_path, output_path):
        aesgcm = AESGCM(self.key)
        with open(encrypted_path, "rb") as f:
            data = f.read()
        nonce, ciphertext = data[:12], data[12:]
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        with open(output_path, "wb") as f:
            f.write(plaintext)
        return output_path


def normalize_confidence(value):
    value = float(value)
    if value < 0:
        return 0.0
    if value > 100:
        return 100.0
    return round(value, 2)
