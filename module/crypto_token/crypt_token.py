

import time
import base64
from cryptography.fernet import Fernet


def generate_dynamic_key():
    """Генерирует динамическую часть ключа на основе времени."""
    dynamic_part = str(int(time.time()) % 100).zfill(2).encode()  # Время, преобразованное в строку
    return dynamic_part

def generate_full_key():
    """Генерирует ключ."""
    dynamic_part = generate_dynamic_key()
    key = Fernet.generate_key()
    full_key = dynamic_part + key
    return base64.urlsafe_b64encode(full_key[:32])  # Обязательная длина 32 байта


def __decrypt_data(key: bytes, data: bytes):
    """Расшифровывает токен."""
    try:
        cipher = Fernet(key)
        token = cipher.decrypt(data).decode()
        return token
    except Exception as e:
        print(f"Ошибка при расшифровке токена: {e}")
        return None



if __name__ == "__main__":
    token = b'TOKEN'

    full_key = generate_full_key()
    print("Полный ключ:", full_key.decode())

    cipher = Fernet(full_key)
    encrypted_token = cipher.encrypt(token)
    print("Зашифрованный токен:", encrypted_token.decode())

    print(f"Дешифрованный токен: {__decrypt_data(full_key, encrypted_token)}")
