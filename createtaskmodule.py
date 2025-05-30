from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QStackedWidget, 
    QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QDateEdit, QComboBox, QListWidget,
    QDoubleSpinBox, QFormLayout, QMessageBox, QListWidgetItem
)
from PyQt5.QtCore import QDate
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QScrollArea, QFrame
from sqlite3 import Error
from datetime import date

from database import TaskManagerDB
from calendarmodule import TaskCalendar
from statisticsmodule import StatsDashboard
from historydatamodule import TaskHistoryPage

class CreateTaskModule(QWidget):    
    def __init__(self):
        super().__init__()
        self.db = TaskManagerDB()
        self.init_ui()

    def init_ui(self):
        """配置添加任务表单"""
        main_layout = QVBoxLayout()

        # 表单容器
        form_widget = QWidget()
        form_layout = QFormLayout()
        form_layout.setContentsMargins(50, 30, 50, 30)
        form_layout.setVerticalSpacing(20)
        
        # 任务名称（必填）
        self.task_name_input = QLineEdit()
        self.task_name_input.setPlaceholderText("输入任务名称（必填）")
        form_layout.addRow("任务名称：", self.task_name_input)
        
        # 任务描述
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(100)
        form_layout.addRow("任务描述：", self.desc_input)
        
        # 标签管理（多选）
        self.tag_list = QListWidget()
        self.tag_list.setSelectionMode(QListWidget.MultiSelection)
        self.load_existing_tags()  # 加载已有标签
        
        # 新标签输入
        self.new_tag_input = QLineEdit()
        self.new_tag_input.setPlaceholderText("输入新标签")
        add_tag_btn = QPushButton("添加标签")
        add_tag_btn.clicked.connect(self.add_new_tag)
        
        tag_management = QHBoxLayout()
        tag_management.addWidget(self.new_tag_input)
        tag_management.addWidget(add_tag_btn)
        
        form_layout.addRow("选择标签：", self.tag_list)
        form_layout.addRow("新建标签：", tag_management)
        
        # 截止日期（必填）
        self.due_date_edit = QDateEdit()
        self.due_date_edit.setDate(QDate.currentDate())
        self.due_date_edit.setCalendarPopup(True)
        form_layout.addRow("截止时间：", self.due_date_edit)
        
        # 财务相关字段
        self.expected_income_spin = QDoubleSpinBox()
        self.expected_income_spin.setRange(0, 999999.99)
        self.expected_income_spin.setPrefix("¥ ")
        form_layout.addRow("预计收入：", self.expected_income_spin)
        
        self.actual_income_spin = QDoubleSpinBox()
        self.actual_income_spin.setRange(0, 999999.99)
        self.actual_income_spin.setPrefix("¥ ")
        form_layout.addRow("实际收入：", self.actual_income_spin)
        
        self.expense_spin = QDoubleSpinBox()
        self.expense_spin.setRange(0, 999999.99)
        self.expense_spin.setPrefix("¥ ")
        form_layout.addRow("支出：", self.expense_spin)
        
        # 提交按钮
        submit_btn = QPushButton("保存任务")
        submit_btn.setObjectName("submitButton")
        submit_btn.clicked.connect(self.save_task)
        
        form_widget.setLayout(form_layout)
        main_layout.addWidget(form_widget)
        main_layout.addWidget(submit_btn, alignment=Qt.AlignCenter)

        self.setLayout(main_layout)

    def load_existing_tags(self):
        """加载已有标签到列表"""
        self.tag_list.clear()
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT tag_name FROM tags")
            tags = cursor.fetchall()
            for tag in tags:
                item = QListWidgetItem(tag[0])
                self.tag_list.addItem(item)
        except Error as e:
            print(f"加载标签失败: {e}")

    def add_new_tag(self):
        """添加新标签到系统和列表"""
        new_tag = self.new_tag_input.text().strip()
        if not new_tag:
            QMessageBox.warning(self, "输入错误", "标签名称不能为空")
            return
        
        try:
            # 检查是否已存在
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT tag_id FROM tags WHERE tag_name = ?", (new_tag,))
            if cursor.fetchone():
                QMessageBox.warning(self, "重复标签", "该标签已存在")
                return
            
            # 插入新标签
            cursor.execute("INSERT INTO tags (tag_name) VALUES (?)", (new_tag,))
            self.db.conn.commit()
            self.load_existing_tags()  # 刷新列表
            self.new_tag_input.clear()
        except Error as e:
            self.db.conn.rollback()
            QMessageBox.critical(self, "数据库错误", f"添加标签失败: {e}")

    def save_task(self):
        """保存任务到数据库"""
        # 收集数据
        task_data = {
            "name": self.task_name_input.text().strip(),
            "description": self.desc_input.toPlainText().strip(),
            "due_date": self.due_date_edit.date().toPyDate(),
            "expected_income": self.expected_income_spin.value(),
            "actual_income": self.actual_income_spin.value(),
            "expense": self.expense_spin.value(),
            "tags": [item.text() for item in self.tag_list.selectedItems()]
        }
        
        # 验证必填字段
        if not task_data["name"]:
            QMessageBox.warning(self, "输入错误", "任务名称不能为空")
            return
        if not task_data["due_date"]:
            QMessageBox.warning(self, "输入错误", "请选择截止时间")
            return
        
        try:
            # 保存到数据库
            task_id = self.db.create_task(
                name=task_data["name"],
                description=task_data["description"] or None,
                due_date=task_data["due_date"],
                expected_income=task_data["expected_income"] or None,
                tags=task_data["tags"]
            )
            
            # 保存财务数据（如果存在）
            if task_data["actual_income"] > 0 or task_data["expense"] > 0:
                self.db.conn.execute(
                    """UPDATE tasks SET 
                        actual_income = ?,
                        expense = ?
                    WHERE task_id = ?""",
                    (task_data["actual_income"], task_data["expense"], task_id)
                )
                self.db.conn.commit()

            #self.db.close()
            
            # 清空表单
            self.task_name_input.clear()
            self.desc_input.clear()
            self.due_date_edit.setDate(QDate.currentDate())
            self.expected_income_spin.setValue(0)
            self.actual_income_spin.setValue(0)
            self.expense_spin.setValue(0)
            self.tag_list.clearSelection()
            
            QMessageBox.information(self, "成功", "任务已保存！")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"发生错误: {str(e)}")
