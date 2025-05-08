import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QStackedWidget, 
    QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QDateTimeEdit, QComboBox, QListWidget,
    QDoubleSpinBox, QFormLayout, QMessageBox, QListWidgetItem
)
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import QDateTime
from PyQt5.QtCore import Qt, QSize
from sqlite3 import Error

from database import TaskManagerDB

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("任务管理系统")
        self.setMinimumSize(800, 600)
        self.db = TaskManagerDB()
        
        # 初始化主界面
        self.init_ui()
        self.apply_styles()
        
    def init_ui(self):
        """初始化界面组件"""
        # 创建堆叠式页面容器
        self.stacked_widget = QStackedWidget()
        
        # 创建主页面
        self.main_page = QWidget()
        self.setup_main_page()
        
        # 创建子页面
        self.add_task_page = self.create_subpage("添加任务页面")
        self.kanban_page = self.create_subpage("任务看板页面")
        self.schedule_page = self.create_subpage("今日日程页面")
        self.analysis_page = self.create_subpage("数据分析页面")
        
        # 添加所有页面到堆叠容器
        self.stacked_widget.addWidget(self.main_page)
        self.stacked_widget.addWidget(self.add_task_page)
        self.stacked_widget.addWidget(self.kanban_page)
        self.stacked_widget.addWidget(self.schedule_page)
        self.stacked_widget.addWidget(self.analysis_page)
        
        self.setCentralWidget(self.stacked_widget)
    
    def setup_main_page(self):
        """配置主页面布局"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)
        
        # 标题
        title = QLabel("任务管理系统")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("mainTitle")
        
        # 按钮容器
        button_layout = QHBoxLayout()
        button_layout.setSpacing(30)
        
        # 功能按钮
        buttons = [
            ("添加任务", self.show_add_task),
            ("查看看板", self.show_kanban),
            ("今日日程", self.show_schedule),
            ("数据分析", self.show_analysis)
        ]
        
        for text, callback in buttons:
            btn = QPushButton(text)
            btn.setMinimumSize(150, 80)
            btn.setObjectName("navButton")
            btn.clicked.connect(callback)
            button_layout.addWidget(btn)
        
        main_layout.addWidget(title)
        main_layout.addLayout(button_layout)
        self.main_page.setLayout(main_layout)
    
    def create_subpage(self, title_text: str) -> QWidget:
        """创建统一风格的子页面模板"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # 标题栏
        header = QHBoxLayout()
        title = QLabel(title_text)
        title.setObjectName("subTitle")
        
        # 返回按钮
        back_btn = QPushButton("返回主界面")
        back_btn.setObjectName("backButton")
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(back_btn)
        
        # 内容区域（后续可添加具体组件）
        if title_text == "添加任务页面":
            self.setup_add_task_page(layout)
        
        layout.addLayout(header)
        page.setLayout(layout)
        return page
    
    def setup_add_task_page(self, layout):
        """配置添加任务表单"""
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
        self.due_date_edit = QDateTimeEdit()
        self.due_date_edit.setDateTime(QDateTime.currentDateTime().addDays(1))
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
        layout.addWidget(form_widget)
        layout.addWidget(submit_btn, alignment=Qt.AlignCenter)

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
            "due_date": self.due_date_edit.dateTime().toPyDateTime(),
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
            
            # 清空表单
            self.task_name_input.clear()
            self.desc_input.clear()
            self.due_date_edit.setDateTime(QDateTime.currentDateTime().addDays(1))
            self.expected_income_spin.setValue(0)
            self.actual_income_spin.setValue(0)
            self.expense_spin.setValue(0)
            self.tag_list.clearSelection()
            
            QMessageBox.information(self, "成功", "任务已保存！")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"发生错误: {str(e)}")
    
    def apply_styles(self):
        """应用样式表"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F5F7FA;
            }
            #mainTitle {
                font-size: 32px;
                color: #2D3748;
                font-weight: bold;
                margin-bottom: 50px;
            }
            #navButton {
                background-color: #4A5568;
                color: white;
                border-radius: 8px;
                padding: 15px;
                font-size: 16px;
            }
            #navButton:hover {
                background-color: #2D3748;
            }
            #subTitle {
                font-size: 24px;
                color: #2D3748;
                font-weight: 500;
            }
            #backButton {
                background-color: #718096;
                color: white;
                border-radius: 5px;
                padding: 8px 15px;
            }
            #backButton:hover {
                background-color: #4A5568;
            }
            #submitButton {
                background-color: #48BB78;
                color: white;
                padding: 12px 30px;
                border-radius: 6px;
                font-size: 16px;
            }
            #submitButton:hover {
                background-color: #38A169;
            }
            QListWidget {
                border: 1px solid #CBD5E0;
                border-radius: 4px;
                padding: 5px;
            }
            QDateTimeEdit {
                padding: 5px;
            }
            QTextEdit {
                border: 1px solid #CBD5E0;
                border-radius: 4px;
                padding: 5px;
            }
                           
        """)
    
    # ---- 页面切换方法 ----
    def show_add_task(self):
        self.stacked_widget.setCurrentIndex(1)
    
    def show_kanban(self):
        self.stacked_widget.setCurrentIndex(2)
    
    def show_schedule(self):
        self.stacked_widget.setCurrentIndex(3)
    
    def show_analysis(self):
        self.stacked_widget.setCurrentIndex(4)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置全局字体
    font = QFont()
    font.setFamily("微软雅黑")
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())