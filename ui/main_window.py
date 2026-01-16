import json
import os
import threading
import time
from datetime import datetime
from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget, QPushButton, QSystemTrayIcon, QMenu, QApplication,
    QMessageBox, QHBoxLayout, QDialog, QHeaderView, QFileDialog
)

from core.storage import save_entries, DATA_FILE, load_entries
from ui.add_entry_dialog import AddEntryDialog
from ui.change_password_dialog import ChangePasswordDialog


class MainWindow(QMainWindow):
    def __init__(self, entries, save_callback, master_password):
        super().__init__()
        self.tray_menu = None
        self.entries = entries
        self.save_callback = save_callback
        self.master_password = master_password
        self.setWindowTitle("开发者信息保管箱")
        self.resize(900, 600)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["名称", "类型", "位置/路径", "用户名", "密码", "操作", "测试"])
        layout.addWidget(self.table)

        self.setStyleSheet("""
                    QPushButton {
                        font-size: 9pt;
                        padding: 2px;
                        min-height: 20px;
                    }
                """)

        btn_add = QPushButton("添加条目")
        btn_add.clicked.connect(self.add_entry)
        layout.addWidget(btn_add)

        self.refresh_table()

        # 托盘图标
        self.setup_tray_icon()

        # 快捷键：Ctrl+Alt+K 呼出
        self.shortcut = QShortcut(QKeySequence("Ctrl+Alt+S"), self)
        self.shortcut.setContext(Qt.ApplicationShortcut)
        self.shortcut.activated.connect(self.show_and_raise)

        # 菜单
        security_menu = self.menuBar().addMenu("安全")
        change_pwd_action = security_menu.addAction("修改主密码")
        change_pwd_action.triggered.connect(self.change_master_password)

        # 数据导出
        file_menu = self.menuBar().addMenu("文件")
        export_action = file_menu.addAction("导出为 JSON")
        export_action.triggered.connect(self.export_to_json)

        # 数据导入
        import_action = file_menu.addAction("从 JSON 导入")
        import_action.triggered.connect(self.import_from_json)

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon = QIcon("./favicon.ico")  # 可替换为内置图标
        if icon.isNull():
            # 使用默认图标
            from PySide6.QtWidgets import QStyle
            icon = QApplication.style().standardIcon(QStyle.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("开发者信息保管箱")

        self.tray_menu = QMenu()
        show_action = self.tray_menu.addAction("显示")
        show_action.triggered.connect(self.show_and_raise)
        quit_action = self.tray_menu.addAction("退出")
        quit_action.triggered.connect(self.quit_app)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show_and_raise()

    def show_and_raise(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def quit_app(self):
        self.tray_icon.hide()
        QApplication.quit()

    def closeEvent(self, event):
        # 点关闭只隐藏到托盘
        self.hide()
        event.ignore()
        self.tray_icon.showMessage("已最小化", "程序仍在后台运行", QSystemTrayIcon.Information, 2000)

    def refresh_table(self):
        self.setMinimumWidth(800)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setRowCount(len(self.entries))
        for row, entry in enumerate(self.entries):
            self.table.setItem(row, 0, QTableWidgetItem(entry.get("name", "")))
            self.table.setItem(row, 1, QTableWidgetItem(entry.get("type", "")))
            # 根据类型决定显示什么作为“位置”
            if entry.get("type") == "Website":
                location = entry.get("url", "")
            elif entry.get("type") == "Server":
                location = entry.get("ip", "")
            elif entry.get("type") == "Database":
                db_type = entry.get("db_type", "")
                if db_type == "SQLite":
                    location = entry.get("sqlite_path", "")
                else:
                    location = f"{entry.get('host', '')}:{entry.get('port', '')}"
            else:
                location = ""

            self.table.setItem(row, 2, QTableWidgetItem(location))
            self.table.setItem(row, 3, QTableWidgetItem(entry.get("username", "")))
            self.table.setItem(row, 4, QTableWidgetItem(entry.get("password", "")))

            # 操作（复制 / 编辑 / 删除）
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)  # 减少内边距
            action_layout.setSpacing(5)

            # 复制密码按钮
            copy_btn = QPushButton("复制密码")
            copy_btn.clicked.connect(lambda *args, e=entry: self.copy_password(e))
            # copy_btn.clicked.connect(partial(self.copy_password, entry))

            # 编辑按钮
            edit_btn = QPushButton("编辑")
            edit_btn.setFixedWidth(50)
            edit_btn.clicked.connect(lambda *args, e=entry: self.edit_entry(e))
            # edit_btn.clicked.connect(partial(self.edit_entry, entry))

            # 删除按钮
            delete_btn = QPushButton("删除")
            delete_btn.setFixedWidth(50)
            delete_btn.setStyleSheet("QPushButton { color: red; }")
            delete_btn.clicked.connect(lambda *args, e=entry: self.delete_entry(e))
            # delete_btn.clicked.connect(partial(self.delete_entry, entry))

            # 添加到布局
            action_layout.addWidget(copy_btn)
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(delete_btn)
            action_layout.addStretch()

            self.table.setCellWidget(row, 5, action_widget)

            # 测试按钮（仅数据库）
            if entry.get("type") == "Database":
                btn_test = QPushButton("测试 DB")
                btn_test.clicked.connect(partial(self.test_db_connection, entry))
                self.table.setCellWidget(row, 6, btn_test)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(5, 180)  # 操作

    def edit_entry(self, entry):
        dialog = AddEntryDialog(entry=entry)
        if dialog.exec() == QDialog.Accepted:
            # 更新内存中的条目
            updated_entry = dialog.entry

            # 找到原条目并替换（根据引用或索引）
            # 简单做法：遍历查找（适合小数据量）
            for i, e in enumerate(self.entries):
                if e is entry:  # 因为是同一个对象引用
                    self.entries[i] = updated_entry
                    break
            else:
                # 如果没找到（比如从文件重新加载过），则按 name + type 匹配（不完美但可用）
                for i, e in enumerate(self.entries):
                    if e.get("name") == entry.get("name") and e.get("type") == entry.get("type"):
                        self.entries[i] = updated_entry
                        break

            # 保存并刷新
            save_entries(self.entries, self.master_password)
            self.refresh_table()

    def delete_entry(self, entry):
        from PySide6.QtWidgets import QMessageBox

        name = entry.get("name", "该条目")
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除「{name}」吗？此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # 从列表中移除
            self.entries = [e for e in self.entries if e is not entry]
            # 保存
            save_entries(self.entries, self.master_password)
            # 刷新表格
            self.refresh_table()

    def copy_password(self, entry):
        clipboard = QApplication.clipboard()
        pwd = entry.get("password", "")
        clipboard.setText(pwd)

        def clear_clipboard():
            time.sleep(10)
            if clipboard.text() == pwd:
                clipboard.clear()

        threading.Thread(target=clear_clipboard, daemon=True).start()
        QMessageBox.information(self, "已复制", "密码已复制（10秒后清除）")

    def test_db_connection(self, entry):
        from core.db_tester import test_database_connection
        result = test_database_connection(entry)
        QMessageBox.information(self, "连接测试", result)

    def add_entry(self):
        dialog = AddEntryDialog(self)
        if dialog.exec():
            self.entries.append(dialog.entry)
            self.save_callback()
            self.refresh_table()

    def export_to_json(self):
        """导出当前所有条目为 JSON 文件"""
        if not self.entries:
            QMessageBox.warning(self, "导出失败", "没有数据可导出！")
            return

        # 生成默认文件名：secrets_YYYYMMDD.json
        timestamp = datetime.now().strftime("%Y%m%d")
        default_filename = f"secrets_{timestamp}.json"

        # 弹出保存对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出数据为 JSON",
            default_filename,
            "JSON 文件 (*.json);;所有文件 (*)"
        )

        if not file_path:
            return  # 用户取消了

        try:
            # 确保文件扩展名为 .json
            if not file_path.lower().endswith(".json"):
                file_path += ".json"

            # 写入 JSON（支持中文、格式化）
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(
                    self.entries,
                    f,
                    ensure_ascii=False,  # 允许中文
                    indent=2  # 美化格式
                )

            QMessageBox.information(
                self,
                "导出成功",
                f"数据已成功导出到：\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "导出失败",
                f"导出时发生错误：\n{str(e)}"
            )

    def import_from_json(self):
        """从 JSON 文件导入数据，并合并到当前 entries（按 name 去重）"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 JSON 文件导入",
            "",
            "JSON 文件 (*.json);;所有文件 (*)"
        )

        if not file_path:
            return  # 用户取消

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                imported_data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "导入失败", f"无法读取文件：\n{str(e)}")
            return

        # 校验数据格式
        if not isinstance(imported_data, list):
            QMessageBox.critical(self, "格式错误", "JSON 文件必须是一个条目列表！")
            return

        valid_entries = []
        for idx, item in enumerate(imported_data):
            if not isinstance(item, dict):
                QMessageBox.warning(self, "跳过无效条目", f"第 {idx + 1} 项不是对象，已跳过。")
                continue
            if "name" not in item:
                QMessageBox.warning(self, "跳过无效条目", f"第 {idx + 1} 项缺少 'name' 字段，已跳过。")
                continue
            valid_entries.append(item)

        if not valid_entries:
            QMessageBox.information(self, "无有效数据", "文件中没有可导入的有效条目。")
            return

        # 按 name 去重：现有条目集合
        existing_names = {entry["name"] for entry in self.entries}

        # 筛选出新条目（name 不在现有集合中）
        new_entries = [e for e in valid_entries if e["name"] not in existing_names]
        duplicate_count = len(valid_entries) - len(new_entries)

        # 提示用户
        msg = f"找到 {len(valid_entries)} 个有效条目。\n"
        if duplicate_count > 0:
            msg += f"其中 {duplicate_count} 个已存在（按名称去重），将跳过。\n"
        msg += f"确定要导入 {len(new_entries)} 个新条目吗？"

        reply = QMessageBox.question(
            self,
            "确认导入",
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        if not new_entries:
            QMessageBox.information(self, "导入完成", "没有新条目需要导入。")
            return

        # 合并新条目
        self.entries.extend(new_entries)
        self.save_callback()  # 保存到本地存储
        self.refresh_table()  # 刷新表格

        QMessageBox.information(
            self,
            "导入成功",
            f"成功导入 {len(new_entries)} 个新条目！"
        )

    def change_master_password(self):
        dialog = ChangePasswordDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return

        old_pwd = dialog.old_password()
        new_pwd = dialog.new_password()

        try:
            # === 1. 用旧密码加载当前数据（验证）===
            if not os.path.exists(DATA_FILE):
                QMessageBox.warning(self, "错误", "数据文件不存在，无法修改密码。")
                return

            with open(DATA_FILE, "rb") as f:
                current_encrypted = f.read()

            # 尝试解密（验证旧密码）
            entries = load_entries(old_pwd)

            # === 2. 用新密码保存 ===
            save_entries(entries, new_pwd)

            # === 3. 更新应用状态 ===
            self.current_password = new_pwd  # 如果你缓存了密码（可选）
            self.entries = entries  # 确保内存数据一致
            # 注意：更安全的做法是不清缓存密码，但这里为了简单

            QMessageBox.information(self, "成功", "主密码已更新！")

        except ValueError as e:
            # 来自 load_entries 的“密码错误”
            QMessageBox.critical(self, "错误", "当前主密码错误，请重试。")
        except Exception as e:
            # 回滚：如果保存失败，用旧密码恢复（可选）
            try:
                with open(DATA_FILE, "wb") as f:
                    f.write(current_encrypted)  # 恢复原文件
            except:
                pass
            QMessageBox.critical(self, "错误", f"修改失败：{str(e)}")
