# DevSecretKeeper

<p align="center">
  <strong>开发者信息保管箱</strong> — 一款本地化的开发凭据管理桌面工具
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/PySide6-6.5+-green.svg" alt="PySide6">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg" alt="Platform">
</p>

---

## 功能特性

- 🔐 **主密码保护** — 使用 PBKDF2 + AES-256-GCM 加密，所有数据本地加密存储
- 🌐 **网站凭据管理** — 保存网站 URL、用户名、密码
- 🖥️ **服务器信息管理** — 记录服务器 IP、端口、SSH 账号
- 🗄️ **数据库连接管理** — 支持 MySQL / PostgreSQL / SQLite，可一键测试连接
- 📋 **一键复制密码** — 复制后 10 秒自动清除剪贴板，防止泄露
- 💾 **数据导入导出** — 支持 JSON 格式导入导出，按名称自动去重
- 🔑 **修改主密码** — 随时更换主密码，数据自动重新加密
- 📌 **系统托盘驻留** — 关闭窗口自动最小化到托盘，`Ctrl+Alt+S` 全局快捷键唤出
- 💥 **崩溃日志记录** — 异常自动写入 `crash.log`，方便排查问题

## 技术栈

| 层级 | 技术 |
|------|------|
| GUI 框架 | [PySide6](https://pypi.org/project/PySide6/) (Qt for Python) |
| 加密引擎 | [cryptography](https://pypi.org/project/cryptography/) — PBKDF2-SHA256 + AES-256-GCM |
| 数据库驱动 | [PyMySQL](https://pypi.org/project/PyMySQL/) / [psycopg2-binary](https://pypi.org/project/psycopg2-binary/) |
| 全局快捷键 | [keyboard](https://pypi.org/project/keyboard/) |

## 项目结构

```
DevSecretKeeper/
├── main.py                  # 入口：密码验证、异常钩子
├── requirements.txt         # 依赖清单
├── favicon.ico              # 应用图标
├── core/                    # 核心业务逻辑
│   ├── __init__.py
│   ├── crypto.py            # 加密/解密（AES-256-GCM）
│   ├── storage.py           # 数据持久化（secrets.dat）
│   └── db_tester.py         # 数据库连接测试
└── ui/                      # 界面层
    ├── __init__.py
    ├── main_window.py       # 主窗口（表格、托盘、菜单）
    ├── add_entry_dialog.py  # 添加/编辑条目对话框
    └── change_password_dialog.py  # 修改主密码对话框
```

## 快速开始

### 环境要求

- Python 3.9+
- Windows 或 Linux 桌面环境

### 安装与运行

```bash
# 克隆仓库
git clone https://github.com/PanNinan/DevSecretKeeper.git
cd DevSecretKeeper

# 安装依赖
pip install -r requirements.txt

# 启动应用
python main.py
```

### 首次使用

1. 启动后会弹出「设置主密码」对话框
2. 输入并确认主密码（至少 4 位）
3. 数据将加密保存到同目录下的 `secrets.dat`

## 使用说明

### 管理条目

- **添加**：点击主界面「添加条目」按钮，选择类型（Website / Server / Database）并填写信息
- **编辑**：点击表格行的「编辑」按钮修改条目
- **删除**：点击「删除」按钮，确认后移除（不可恢复）
- **复制密码**：点击「复制密码」，10 秒后自动清除剪贴板

### 数据库连接测试

对于 Database 类型条目，表格中会显示「测试 DB」按钮，支持：

- **SQLite** — 自动验证数据库文件是否存在并可访问
- **MySQL** — 测试指定主机的 MySQL 连接
- **PostgreSQL** — 测试指定主机的 PostgreSQL 连接

### 导入与导出

- **导出**：菜单 `文件 → 导出为 JSON`，选择保存位置
- **导入**：菜单 `文件 → 从 JSON 导入`，按名称自动去重合并

### 全局快捷键

- `Ctrl+Alt+S` — 从托盘唤出主窗口

## 数据安全

- 所有凭据使用 **AES-256-GCM** 对称加密，密钥由 **PBKDF2-HMAC-SHA256**（100,000 次迭代）从主密码派生
- 数据存储在本地 `secrets.dat` 文件中，**不上传任何网络服务**
- 密码复制到剪贴板后 **10 秒自动清除**
- 修改主密码时使用原子写入策略，失败自动回滚

## 开发

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v
```

### 打包为可执行文件

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=favicon.ico --name=DevSecretKeeper main.py
```

打包产物位于 `dist/DevSecretKeeper.exe`。

## GitHub Actions CI/CD

本项目使用 GitHub Actions 实现自动化：

| 工作流 | 触发条件 | 功能 |
|--------|----------|------|
| **CI** | push / PR | 代码检查 + 单元测试 |
| **Build** | tag `v*` | Windows/Linux 构建打包 |
| **Release** | Build 成功 | 创建 GitHub Release 并上传产物 |

详见 [.github/workflows/](.github/workflows/) 目录。

## 许可证

[MIT License](LICENSE) © 2026 ninan
