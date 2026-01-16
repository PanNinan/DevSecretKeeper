import os
import sys
import traceback
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox
)

from core.storage import load_entries, save_entries
from ui.main_window import MainWindow


def excepthook(exc_type, exc_value, exc_tb):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("crash.log", "a", encoding="utf-8") as f:
        f.write(f"\n{'=' * 60}\n")
        f.write(f"崩溃时间: {timestamp}\n")
        f.write("".join(traceback.format_exception(exc_type, exc_value, exc_tb)))
    print("异常已记录到 crash.log")


sys.excepthook = excepthook


class PasswordDialog(QDialog):
    def __init__(self, first_run=False, verify_password_func=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("主密码" if not first_run else "首次使用")
        self.setFixedSize(320, 160)
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint)

        self.first_run = first_run
        self.verify_password_func = verify_password_func  # 用于验证密码的函数
        self.password = ""

        layout = QVBoxLayout(self)

        msg = "请设置主密码：" if first_run else "请输入主密码："
        layout.addWidget(QLabel(msg))

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.returnPressed.connect(self._on_ok_clicked)
        layout.addWidget(self.password_edit)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red; font-size: 10pt;")
        layout.addWidget(self.error_label)

        self.btn_ok = QPushButton("确定")
        self.btn_cancel = QPushButton("取消")
        self.btn_ok.clicked.connect(self._on_ok_clicked)
        self.btn_cancel.clicked.connect(self.reject)
        layout.addWidget(self.btn_ok)
        layout.addWidget(self.btn_cancel)

    def _on_ok_clicked(self):
        pwd = self.password_edit.text().strip()
        if not pwd:
            self.error_label.setText("❌ 密码不能为空")
            return

        if self.first_run:
            # 首次运行，无需验证
            self.password = pwd
            self.accept()
        else:
            # 非首次：尝试验证密码
            try:
                if self.verify_password_func:
                    self.verify_password_func(pwd)  # 如果抛异常，说明密码错
                self.password = pwd
                self.accept()
            except ValueError:
                self.error_label.setText("❌ 主密码错误，请重试")
                self.password_edit.selectAll()
                self.password_edit.setFocus()
            except Exception as e:
                self.error_label.setText(f"❌ 加载失败: {str(e)}")
                self.password_edit.selectAll()
                self.password_edit.setFocus()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    first_run = not os.path.exists("secrets.dat")
    def verify_password(pwd):
        load_entries(pwd)  # 如果密码错，会抛 ValueError

    while True:
        # 传入验证函数
        dialog = PasswordDialog(
            first_run=first_run,
            verify_password_func=None if first_run else verify_password
        )
        result = dialog.exec()

        if result == QDialog.Rejected:
            sys.exit(0)

        password = dialog.password

        if first_run:
            entries = []
            try:
                save_entries(entries, password)
                break
            except Exception as e:
                # 首次保存失败，重新循环
                QMessageBox.critical(None, "错误", f"无法保存初始数据:\n{str(e)}")
                continue
        else:
            # 密码已在 dialog 内部验证成功，直接加载
            try:
                entries = load_entries(password)
                break
            except Exception:
                # 理论上不会走到这里，但保险起见
                continue

        # 启动主窗口

    def save_wrapper():
        save_entries(entries, password)

    window = MainWindow(entries, save_wrapper, password)
    window.hide()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
