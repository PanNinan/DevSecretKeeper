from PySide6.QtWidgets import (
    QVBoxLayout,
    QPushButton, QMessageBox, QDialog, QLabel, QLineEdit
)


class ChangePasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("修改主密码")
        self.setModal(True)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("当前主密码："))
        self.old_pwd = QLineEdit()
        self.old_pwd.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.old_pwd)

        layout.addWidget(QLabel("新主密码："))
        self.new_pwd1 = QLineEdit()
        self.new_pwd1.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.new_pwd1)

        layout.addWidget(QLabel("确认新主密码："))
        self.new_pwd2 = QLineEdit()
        self.new_pwd2.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.new_pwd2)

        self.btn_ok = QPushButton("确定")
        self.btn_cancel = QPushButton("取消")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.setEnabled(False)

        layout.addWidget(self.btn_ok)
        layout.addWidget(self.btn_cancel)

        # 实时验证
        self.new_pwd1.textChanged.connect(self._validate)
        self.new_pwd2.textChanged.connect(self._validate)
        self.old_pwd.textChanged.connect(self._validate)

    def _validate(self):
        old = len(self.old_pwd.text()) > 0
        new1 = self.new_pwd1.text()
        new2 = self.new_pwd2.text()
        match = new1 == new2 and len(new1) >= 4
        self.btn_ok.setEnabled(old and match)

    def accept(self):
        if self.new_pwd1.text() != self.new_pwd2.text():
            QMessageBox.warning(self, "错误", "两次输入的新密码不一致！")
            return
        if len(self.new_pwd1.text()) < 4:
            QMessageBox.warning(self, "弱密码", "新密码至少需要4位！")
            return
        super().accept()

    def old_password(self):
        return self.old_pwd.text()

    def new_password(self):
        return self.new_pwd1.text()
