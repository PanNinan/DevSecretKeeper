from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QMessageBox, QWidget, QStackedWidget
)


class AddEntryDialog(QDialog):
    def __init__(self, parent=None, entry=None):
        super().__init__(parent)
        self.setWindowTitle("添加条目" if entry is None else "编辑条目")
        self.entry = entry or {}
        self.resize(400, 300)

        layout = QVBoxLayout(self)

        # 名称
        layout.addWidget(QLabel("名称:"))
        self.name_edit = QLineEdit(self.entry.get("name", ""))
        layout.addWidget(self.name_edit)

        # 类型选择
        layout.addWidget(QLabel("类型:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Website", "Server", "Database"])
        current_type = self.entry.get("type", "Website")
        self.type_combo.setCurrentText(current_type)
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        layout.addWidget(self.type_combo)

        # 表单区域：使用 QStackedWidget
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)

        # 创建各类型表单页
        self.website_page = self._create_website_form()
        self.server_page = self._create_server_form()
        self.database_page = self._create_database_form()

        self.stacked_widget.addWidget(self.website_page)
        self.stacked_widget.addWidget(self.server_page)
        self.stacked_widget.addWidget(self.database_page)

        # 根据初始类型显示对应页面
        self._update_stacked_index(current_type)

        # 底部按钮
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        # 初始化表单数据
        self._load_entry_data()

        self._load_entry()

    def _create_website_form(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("URL:"))
        self.url_edit = QLineEdit()
        layout.addWidget(self.url_edit)
        layout.addWidget(QLabel("用户名:"))
        self.web_user_edit = QLineEdit()
        layout.addWidget(self.web_user_edit)
        layout.addWidget(QLabel("密码:"))
        self.web_pwd_edit = QLineEdit()
        self.web_pwd_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.web_pwd_edit)
        layout.addStretch()
        return widget

    def _create_server_form(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("IP 地址:"))
        self.ip_edit = QLineEdit()
        layout.addWidget(self.ip_edit)
        layout.addWidget(QLabel("端口:"))
        self.port_edit = QLineEdit("22")
        layout.addWidget(self.port_edit)
        layout.addWidget(QLabel("用户名:"))
        self.srv_user_edit = QLineEdit()
        layout.addWidget(self.srv_user_edit)
        layout.addWidget(QLabel("密码:"))
        self.srv_pwd_edit = QLineEdit()
        self.srv_pwd_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.srv_pwd_edit)
        layout.addStretch()
        return widget

    def _create_database_form(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 数据库类型
        layout.addWidget(QLabel("数据库类型:"))
        self.db_type_combo = QComboBox()
        self.db_type_combo.addItems(["MySQL", "PostgreSQL"])
        self.db_type_combo.currentTextChanged.connect(self._on_db_type_changed)
        layout.addWidget(self.db_type_combo)

        # MySQL/PG 字段
        self.db_host_label = QLabel("主机:")
        self.db_host_edit = QLineEdit()
        self.db_port_label = QLabel("端口:")
        self.db_port_edit = QLineEdit()
        self.db_user_label = QLabel("用户名:")
        self.db_user_edit = QLineEdit()
        self.db_pwd_label = QLabel("密码:")
        self.db_pwd_edit = QLineEdit()
        self.db_pwd_edit.setEchoMode(QLineEdit.Password)
        self.db_name_label = QLabel("数据库名:")
        self.db_name_edit = QLineEdit()

        # 测试按钮
        self.test_db_btn = QPushButton("测试连接")
        self.test_db_btn.clicked.connect(self.test_connection)

        # 添加到布局（后面通过 _on_db_type_changed 控制显示）
        for w in [
            self.db_host_label, self.db_host_edit,
            self.db_port_label, self.db_port_edit,
            self.db_user_label, self.db_user_edit,
            self.db_pwd_label, self.db_pwd_edit,
            self.db_name_label, self.db_name_edit,
            self.test_db_btn
        ]:
            layout.addWidget(w)

        layout.addStretch()
        return widget

    def _update_stacked_index(self, typ: str):
        index_map = {"Website": 0, "Server": 1, "Database": 2}
        self.stacked_widget.setCurrentIndex(index_map.get(typ, 0))

    def _on_type_changed(self, typ: str):
        self._update_stacked_index(typ)
        # 可选：清空其他表单数据（避免混淆）
        # 或保留用户已输入内容（更友好）

    def _on_db_type_changed(self, db_type: str):
        is_sqlite = (db_type == "SQLite")
        # 隐藏/显示字段
        self.db_host_label.setVisible(True)
        self.db_host_edit.setVisible(True)
        self.db_port_label.setVisible(True)
        self.db_port_edit.setVisible(True)
        self.db_user_label.setVisible(True)
        self.db_user_edit.setVisible(True)
        self.db_pwd_label.setVisible(True)
        self.db_pwd_edit.setVisible(True)
        self.db_name_label.setVisible(True)
        self.db_name_edit.setVisible(True)

        # 设置默认端口
        if db_type == "MySQL":
            self.db_port_edit.setText("3306")
        elif db_type == "PostgreSQL":
            self.db_port_edit.setText("5432")

    def _browse_sqlite_file(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 SQLite 数据库", "", "SQLite 文件 (*.db *.sqlite);;所有文件 (*)"
        )
        if path:
            self.sqlite_path_edit.setText(path)

    def _create_new_sqlite_db(self):
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        import sqlite3
        path, _ = QFileDialog.getSaveFileName(
            self, "新建 SQLite 数据库", "", "SQLite 数据库 (*.db)"
        )
        if not path:
            return
        if not path.endswith(('.db', '.sqlite', '.sqlite3')):
            path += ".db"
        try:
            conn = sqlite3.connect(path)
            conn.execute("CREATE TABLE IF NOT EXISTS init (id INTEGER);")
            conn.close()
            self.sqlite_path_edit.setText(path)
            QMessageBox.information(self, "成功", f"数据库已创建：{path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def _load_entry_data(self):
        """从 self.entry 加载数据到 UI"""
        typ = self.entry.get("type", "Website")

        if typ == "Website":
            self.url_edit.setText(self.entry.get("url", ""))
            self.web_user_edit.setText(self.entry.get("username", ""))
            self.web_pwd_edit.setText(self.entry.get("password", ""))
        elif typ == "Server":
            self.ip_edit.setText(self.entry.get("ip", ""))
            self.port_edit.setText(self.entry.get("port", "22"))
            self.srv_user_edit.setText(self.entry.get("username", ""))
            self.srv_pwd_edit.setText(self.entry.get("password", ""))
        elif typ == "Database":
            db_type = self.entry.get("db_type", "MySQL")
            self.db_type_combo.setCurrentText(db_type)
            self._on_db_type_changed(db_type)  # 触发显示/隐藏

            if db_type == "SQLite":
                self.sqlite_path_edit.setText(self.entry.get("sqlite_path", ""))
            else:
                self.db_host_edit.setText(self.entry.get("host", ""))
                self.db_port_edit.setText(self.entry.get("port", "3306"))
                self.db_user_edit.setText(self.entry.get("username", ""))
                self.db_pwd_edit.setText(self.entry.get("password", ""))
            self.db_name_edit.setText(self.entry.get("database_name", ""))

    def accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "名称不能为空！")
            return

        typ = self.type_combo.currentText()
        entry = {"name": name, "type": typ}

        if typ == "Website":
            entry["url"] = self.url_edit.text().strip()
            entry["username"] = self.web_user_edit.text().strip()
            entry["password"] = self.web_pwd_edit.text().strip()
        elif typ == "Server":
            entry["ip"] = self.ip_edit.text().strip()
            entry["port"] = self.port_edit.text().strip()
            entry["username"] = self.srv_user_edit.text().strip()
            entry["password"] = self.srv_pwd_edit.text().strip()
        elif typ == "Database":
            db_type = self.db_type_combo.currentText()
            entry["db_type"] = db_type
            if db_type == "SQLite":
                entry["sqlite_path"] = self.sqlite_path_edit.text().strip()
            else:
                entry["host"] = self.db_host_edit.text().strip()
                entry["port"] = self.db_port_edit.text().strip()
                entry["username"] = self.db_user_edit.text().strip()
                entry["password"] = self.db_pwd_edit.text().strip()
            entry["database_name"] = self.db_name_edit.text().strip()

        self.entry = entry
        super().accept()

    def _load_entry(self):
        # 类型切换时更新默认端口（简化：启动时不自动切换）
        pass

    def test_connection(self, core=None):
        from core.db_tester import test_database_connection
        entry = {
            "db_type": self.db_type_combo.currentText(),
            "host": self.db_host_edit.text(),
            "port": self.db_port_edit.text(),
            "username": self.db_user_edit.text(),
            "password": self.db_pwd_edit.text(),
            "database_name": self.db_name_edit.text(),
        }
        result = test_database_connection(entry)
        self.test_result_label.setText(result)

    def _on_db_type_changed(self, db_type: str):
        # 隐藏/显示网络字段
        self.db_host_label.setVisible(True)
        self.db_host_edit.setVisible(True)
        self.db_port_label.setVisible(True)
        self.db_port_edit.setVisible(True)

        # 隐藏用户名/密码/数据库名（SQLite 不需要）
        self.db_user_label.setVisible(True)
        self.db_user_edit.setVisible(True)
        self.db_pwd_label.setVisible(True)
        self.db_pwd_edit.setVisible(True)
        self.db_name_label.setVisible(True)
        self.db_name_edit.setVisible(True)

        # 设置默认端口
        if db_type == "MySQL":
            self.db_port_edit.setText("3306")
        elif db_type == "PostgreSQL":
            self.db_port_edit.setText("5432")
