import os
import sqlite3
from typing import Dict, Any

import psycopg2
import pymysql


def test_database_connection(entry: Dict[str, Any]) -> str:
    db_type = entry.get("db_type", "").lower()
    print(entry)
    try:
        if db_type == "sqlite":
            path = entry.get("sqlite_path", "").strip()
            if not path:
                return "❌ 未指定数据库文件路径"
            if not os.path.exists(path):
                return f"❌ 文件不存在: {path}"
            # 尝试连接并执行简单查询
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            cursor.fetchone()
            conn.close()
            return "✅ SQLite 连接成功"

        elif db_type == "mysql":
            host = entry.get("host")
            port = int(entry.get("port", 3306))
            user = entry.get("username")
            password = entry.get("password")
            database = entry.get("database_name")
            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                connect_timeout=5
            )
            conn.close()
            return "✅ MySQL 连接成功"

        elif db_type == "postgresql":
            host = entry.get("host")
            port = int(entry.get("port", 5432))
            user = entry.get("username")
            password = entry.get("password")
            database = entry.get("database_name")
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                dbname=database,
                connect_timeout=5
            )
            conn.close()
            return "✅ PostgreSQL 连接成功"

        else:
            return "❌ 不支持的数据库类型"

    except Exception as e:
        return f"❌ 连接失败: {str(e)}"
