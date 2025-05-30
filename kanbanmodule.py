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

class KanbanPage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = TaskManagerDB()
        self.init_ui()
    
    def init_ui(self):
        """配置任务看板页面"""
        main_layout = QVBoxLayout()

        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 看板主体容器
        board_widget = QWidget()
        board_layout = QHBoxLayout()
        board_layout.setContentsMargins(20, 10, 20, 10)
        board_layout.setSpacing(20)
        
        # 定义四列状态
        self.status_columns = {
            "未开始": self.create_status_column("未开始", "#CBD5E0"),
            "进行中": self.create_status_column("进行中", "#63B3ED"),
            "已完成": self.create_status_column("已完成", "#68D391"),
            "已中断": self.create_status_column("已中断", "#FC8181")
        }
        
        # 添加各状态列到看板
        for column in self.status_columns.values():
            board_layout.addLayout(column["layout"])
        
        board_widget.setLayout(board_layout)
        scroll.setWidget(board_widget)
        main_layout.addWidget(scroll)

        self.setLayout(main_layout)
        
        # 加载任务数据
        self.load_kanban_tasks()

    def create_status_column(self, title: str, color: str) -> dict:
        """创建单个状态列"""
        column = {
            "layout": QVBoxLayout(),
            "widget": QWidget(),
            "title": title
        }
        
        # 标题样式
        title_widget = QLabel(title)
        title_widget.setStyleSheet(f"""
            background-color: {color};
            color: white;
            padding: 8px;
            border-radius: 4px;
            font-weight: bold;
        """)
        title_widget.setAlignment(Qt.AlignTop)
        
        # 任务列表容器
        #task_list = QVBoxLayout()
        #task_list.setSpacing(10)
        #task_list.addWidget(title_widget)
        #task_list.addStretch()
        
        column["layout"].setSpacing(10)
        column["layout"].addWidget(title_widget)
        column["layout"].addStretch()
        #column["layout"].addLayout(task_list)
        return column

    def load_kanban_tasks(self):
        """加载并展示所有任务"""
        # 清空现有任务卡片
        for column in self.status_columns.values():
            while column["layout"].count() > 2:
                item = column["layout"].takeAt(1)
                if item.widget():
                    item.widget().deleteLater()
        
        # 从数据库获取任务数据
        try:
            cursor = self.db.conn.execute("""
                SELECT t.task_id, t.name, t.status, t.due_date, 
                       GROUP_CONCAT(tag.tag_name, ', ') AS tags
                FROM tasks t
                LEFT JOIN task_tags tt ON t.task_id = tt.task_id
                LEFT JOIN tags tag ON tt.tag_id = tag.tag_id
                GROUP BY t.task_id
                ORDER BY t.due_date ASC
            """)
            
            #print(len(cursor.fetchall()))

            for task in cursor.fetchall():
                task_id = task[0]
                name = task[1]
                status = task[2]
                due_date = task[3]
                tags = task[4].split(", ") if task[4] else []
                
                # 创建任务卡片
                card = self.create_task_card(task_id, name, tags, due_date, status)
                
                # 添加到对应状态列
                if status in self.status_columns:
                    self.status_columns[status]["layout"].insertWidget(
                        self.status_columns[status]["layout"].count()-1,  # 保留最后的stretch
                        card
                    )

        except Error as e:
            QMessageBox.critical(self, "数据库错误", f"加载任务失败: {e}")

    def create_task_card(self, task_id: int, name: str, tags: list, 
                        due_date: date, status: str) -> QFrame:
        """创建单个任务卡片组件"""
        card = QFrame()
        card.setObjectName("taskCard")
        card.setStyleSheet(f"""
            #taskCard {{
                background: white;
                border-radius: 8px;
                padding: 15px;
                border-left: 4px solid {self.get_status_color(status)};
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # 任务名称
        name_label = QLabel(name)
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(name_label)
        
        # 标签显示
        if tags:
            tag_container = QWidget()
            tag_layout = QHBoxLayout()
            tag_layout.setContentsMargins(0, 0, 0, 0)
            tag_layout.setSpacing(5)
            
            for tag in tags:
                tag_label = QLabel(tag)
                tag_label.setStyleSheet("""
                    background: #E2E8F0;
                    color: #4A5568;
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-size: 12px;
                """)
                tag_layout.addWidget(tag_label)
            
            tag_container.setLayout(tag_layout)
            layout.addWidget(tag_container)
        
        # 截止时间
        due_label = QLabel(f"截止时间：{due_date}")
        due_label.setStyleSheet("color: #718096; font-size: 12px;")
        layout.addWidget(due_label)
        
        # 状态选择下拉框
        status_combo = QComboBox()
        status_combo.addItems(["未开始", "进行中", "已完成", "已中断"])
        status_combo.setCurrentText(status)
        status_combo.currentTextChanged.connect(
            lambda new_status, t_id=task_id: self.update_task_status(t_id, new_status)
        )
        layout.addWidget(status_combo)
        
        card.setLayout(layout)
        return card

    def get_status_color(self, status: str) -> str:
        """获取状态对应的颜色"""
        return {
            "未开始": "#CBD5E0",
            "进行中": "#63B3ED",
            "已完成": "#68D391",
            "已中断": "#FC8181"
        }.get(status, "#CBD5E0")

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