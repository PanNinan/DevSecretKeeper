import json
import os

from .crypto import encrypt_data, decrypt_data

DATA_FILE = "secrets.dat"


def load_entries(password: str):
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "rb") as f:
        data = f.read()
    try:
        plain = decrypt_data(data, password)
        return json.loads(plain)
    except Exception as e:
        raise ValueError("主密码错误或数据损坏")


def save_entries(entries, password: str):
    plain = json.dumps(entries, ensure_ascii=False)
    encrypted = encrypt_data(plain, password)
    with open(DATA_FILE, "wb") as f:
        f.write(encrypted)
