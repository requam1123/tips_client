# core/crypto.py
import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

def encrypt_password(password: str, public_key_pem: bytes) -> str:
    """接收明文密码和PEM公钥，返回Base64加密字符串"""
    try:
        public_key = serialization.load_pem_public_key(public_key_pem)
        encrypted_bytes = public_key.encrypt(
            password.encode('utf-8'),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.b64encode(encrypted_bytes).decode('utf-8')
    except Exception as e:
        print(f"Encryption Error: {e}")
        return ""