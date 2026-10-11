"""bot/encryption.py — AES-like XOR + hashing (lab)"""
import hashlib, secrets, base64

def hash_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def random_key(n=32) -> bytes:
    return secrets.token_bytes(n)

def xor_crypt(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

def encrypt_b64(plaintext: str, key: bytes) -> str:
    return base64.b64encode(xor_crypt(plaintext.encode(), key)).decode()

def decrypt_b64(token: str, key: bytes) -> str:
    return xor_crypt(base64.b64decode(token), key).decode()
