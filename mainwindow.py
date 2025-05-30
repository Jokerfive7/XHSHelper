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
from createtaskmodule import CreateTaskModule
from kanbanmodule import KanbanPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("任务管理系统")
        self.setMinimumSize(1100, 600)
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
        self.history_page = self.create_subpage("历史任务页面")
        self.analysis_page = self.create_subpage("数据分析页面")
        
        # 添加所有页面到堆叠容器
        self.stacked_widget.addWidget(self.main_page)
        self.stacked_widget.addWidget(self.add_task_page)
        self.stacked_widget.addWidget(self.kanban_page)
        self.stacked_widget.addWidget(self.history_page)
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

        #日历
        self.calendar = TaskCalendar()
        self.calendar.setObjectName("mainCalendar")
        
        # 按钮容器
        button_layout = QHBoxLayout()
        button_layout.setSpacing(30)
        
        # 功能按钮
        buttons = [
            ("添加任务", self.show_add_task),
            ("查看看板", self.show_kanban),
            ("历史任务", self.show_history),
            ("数据分析", self.show_analysis)
        ]
        
        for text, callback in buttons:
            btn = QPushButton(text)
            btn.setMinimumSize(150, 80)
            btn.setObjectName("navButton")
            btn.clicked.connect(callback)
            button_layout.addWidget(btn)
        
        main_layout.addWidget(title)
        main_layout.addWidget(self.calendar)
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
        back_btn.clicked.connect(self.show_main)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(back_btn)
        
        # 内容区域（后续可添加具体组件）
        if title_text == "添加任务页面":
            layout.addWidget(CreateTaskModule())

        if title_text == "任务看板页面":
            layout.addWidget(KanbanPage())
        
        if title_text == "历史任务页面":
            layout.addWidget(TaskHistoryPage())

        if title_text == "数据分析页面":
            layout.addWidget(StatsDashboard())

        
        layout.addLayout(header)
        page.setLayout(layout)
        return page

    def update_task_status(self, task_id: int, new_status: str):
        """更新任务状态"""
        try:
            self.db.conn.execute(
                "UPDATE tasks SET status = ? WHERE task_id = ?",
                (new_status, task_id)
            )
            self.db.conn.commit()
            self.load_kanban_tasks()  # 刷新看板
        except Error as e:
            QMessageBox.critical(self, "更新失败", f"状态更新失败: {e}")
    
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
            QScrollArea {
                border: none;
                background: #F7FAFC;
            }
            QComboBox {
                padding: 4px;
                border: 1px solid #CBD5E0;
                border-radius: 4px;
                font-size: 12px;
            }
                           
        """)
    
    # ---- 页面切换方法 ----
    def show_main(self):
        self.stacked_widget.setCurrentIndex(0)
        self.calendar.load_month_tasks(
            self.calendar.yearShown(), 
            self.calendar.monthShown()
        )

    def show_add_task(self):
        self.stacked_widget.setCurrentIndex(1)
    
    def show_kanban(self):
        self.stacked_widget.setCurrentIndex(2)
        #self.load_kanban_tasks()
    
    def show_history(self):
        self.stacked_widget.setCurrentIndex(3)
    
    def show_analysis(self):
        self.stacked_widget.setCurrentIndex(4)