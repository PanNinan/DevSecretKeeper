"""DevSecretKeeper 核心模块单元测试"""
import json
import os
import tempfile
import pytest

# 确保能导入 core 模块
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.crypto import encrypt_data, decrypt_data, derive_key


class TestCrypto:
    """加密模块测试"""

    def test_derive_key_deterministic(self):
        """相同密码+相同盐 → 相同密钥"""
        password = "test_password"
        salt = b"x" * 16
        key1 = derive_key(password, salt)
        key2 = derive_key(password, salt)
        assert key1 == key2
        assert len(key1) == 32  # AES-256

    def test_derive_key_different_passwords(self):
        """不同密码 → 不同密钥"""
        salt = b"y" * 16
        key1 = derive_key("password_a", salt)
        key2 = derive_key("password_b", salt)
        assert key1 != key2

    def test_encrypt_decrypt_roundtrip(self):
        """加密后能正确解密"""
        plaintext = "Hello, DevSecretKeeper! 你好世界 🌍"
        password = "my_secret_key"
        encrypted = encrypt_data(plaintext, password)
        decrypted = decrypt_data(encrypted, password)
        assert decrypted == plaintext

    def test_encrypt_produces_unique_ciphertext(self):
        """同一明文多次加密产生不同密文（随机盐）"""
        plaintext = "same content"
        password = "same password"
        ct1 = encrypt_data(plaintext, password)
        ct2 = encrypt_data(plaintext, password)
        assert ct1 != ct2
        # 但都能正确解密
        assert decrypt_data(ct1, password) == plaintext
        assert decrypt_data(ct2, password) == plaintext

    def test_decrypt_wrong_password_raises(self):
        """错误密码解密应抛出异常"""
        plaintext = "secret data"
        encrypted = encrypt_data(plaintext, "correct_password")
        with pytest.raises(Exception):
            decrypt_data(encrypted, "wrong_password")

    def test_decrypt_tampered_data_raises(self):
        """篡改密文后解密应抛出异常"""
        encrypted = encrypt_data("test", "password")
        tampered = encrypted[:-1] + bytes([(encrypted[-1] + 1) % 256])
        with pytest.raises(Exception):
            decrypt_data(tampered, "password")

    def test_empty_plaintext(self):
        """空字符串也能正确加解密"""
        encrypted = encrypt_data("", "password")
        assert decrypt_data(encrypted, "password") == ""


class TestStorage:
    """存储模块测试"""

    def test_save_and_load_entries(self):
        """保存后能正确加载"""
        from core.storage import save_entries, load_entries

        entries = [
            {"name": "GitHub", "type": "Website", "url": "https://github.com", "username": "user", "password": "pass123"},
            {"name": "DB Server", "type": "Server", "ip": "192.168.1.1", "port": "22", "username": "root", "password": "secret"},
        ]
        password = "master_password"

        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = os.path.join(tmpdir, "secrets.dat")
            # 临时替换 DATA_FILE 路径
            import core.storage
            original = core.storage.DATA_FILE
            core.storage.DATA_FILE = data_file
            try:
                save_entries(entries, password)
                loaded = load_entries(password)
                assert loaded == entries
                assert len(loaded) == 2
                assert loaded[0]["name"] == "GitHub"
            finally:
                core.storage.DATA_FILE = original

    def test_load_nonexistent_file(self):
        """不存在的数据文件返回空列表"""
        from core.storage import load_entries

        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = os.path.join(tmpdir, "nonexistent.dat")
            import core.storage
            original = core.storage.DATA_FILE
            core.storage.DATA_FILE = data_file
            try:
                assert load_entries("any_password") == []
            finally:
                core.storage.DATA_FILE = original

    def test_load_wrong_password_raises(self):
        """错误密码加载应抛出 ValueError"""
        from core.storage import save_entries, load_entries

        entries = [{"name": "Test", "type": "Website"}]

        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = os.path.join(tmpdir, "secrets.dat")
            import core.storage
            original = core.storage.DATA_FILE
            core.storage.DATA_FILE = data_file
            try:
                save_entries(entries, "correct_password")
                with pytest.raises(ValueError):
                    load_entries("wrong_password")
            finally:
                core.storage.DATA_FILE = original

    def test_save_and_load_chinese_content(self):
        """中文内容保存后能正确加载"""
        from core.storage import save_entries, load_entries

        entries = [
            {"name": "测试服务器", "type": "Server", "ip": "10.0.0.1", "port": "22", "username": "管理员", "password": "密码123"},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = os.path.join(tmpdir, "secrets.dat")
            import core.storage
            original = core.storage.DATA_FILE
            core.storage.DATA_FILE = data_file
            try:
                save_entries(entries, "主密码")
                loaded = load_entries("主密码")
                assert loaded == entries
                assert loaded[0]["name"] == "测试服务器"
                assert loaded[0]["username"] == "管理员"
            finally:
                core.storage.DATA_FILE = original


class TestDbTester:
    """数据库连接测试模块"""

    @classmethod
    def setup_class(cls):
        """跳过未安装数据库驱动的测试"""
        pytest.importorskip("psycopg2")
        pytest.importorskip("pymysql")

    def test_unsupported_db_type(self):
        """不支持的数据库类型返回错误信息"""
        from core.db_tester import test_database_connection

        result = test_database_connection({"db_type": "oracle"})
        assert "不支持" in result

    def test_sqlite_missing_path(self):
        """SQLite 未指定路径返回错误"""
        from core.db_tester import test_database_connection

        result = test_database_connection({"db_type": "sqlite", "sqlite_path": ""})
        assert "未指定" in result

    def test_sqlite_nonexistent_file(self):
        """SQLite 文件不存在返回错误"""
        from core.db_tester import test_database_connection

        result = test_database_connection({"db_type": "sqlite", "sqlite_path": "/nonexistent/path.db"})
        assert "不存在" in result

    def test_sqlite_connection_success(self):
        """SQLite 能成功连接到临时数据库"""
        from core.db_tester import test_database_connection

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE test (id INTEGER);")
            conn.close()

            result = test_database_connection({"db_type": "sqlite", "sqlite_path": db_path})
            assert "成功" in result
        finally:
            os.unlink(db_path)
