from cryptography.fernet import Fernet


proxy = 'http://127.0.0.1:10809'

tornt_cli_host = "192.168.1.xx"
tornt_cli_port = 9091
tornt_cli_type = "transmission"
tornt_cli_login = "transmission"

jellyfin = False
jellyfin_dir = "/jellyfin/library/"


def get_token() -> str:
    return "None"

def get_pass_rutreker() -> str:
    return "None"

def get_pass_defualt_torent_client() -> str:
    return "None"

def get_login_rutreker() -> str:
    return "None"

def __decrypt_data(key: bytes, data: bytes) -> str:
    """Расшифровывает токен."""
    try:
        cipher = Fernet(key)
        token = cipher.decrypt(data).decode()
        return token
    except Exception as e:
        print(f"Ошибка при расшифровке токена: {e}")
        return None

