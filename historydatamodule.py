import sys
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, 
                            QPushButton, QDialog, QFormLayout, QGroupBox, QAbstractItemView)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont

class TaskHistoryPage(QWidget):
    def __init__(self):
        super().__init__()
        self.db_conn = sqlite3.connect('task_manager1.db')  # 修改为你的数据库路径
        self.current_page = 1
        self.init_ui()
        self.load_months()
        self.load_tags()
        self.load_tasks()

    def init_ui(self):
        self.setWindowTitle('任务历史记录')
        self.setGeometry(100, 100, 1000, 700)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)

        # 筛选区域
        filter_layout = QHBoxLayout()
        
        # 月份筛选
        month_label = QLabel("月份筛选:")
        self.month_combo = QComboBox()
        self.month_combo.setMinimumWidth(150)
        filter_layout.addWidget(month_label)
        filter_layout.addWidget(self.month_combo)
        
        # 标签筛选
        tag_label = QLabel("标签筛选:")
        self.tag_combo = QComboBox()
        self.tag_combo.setMinimumWidth(150)
        filter_layout.addWidget(tag_label)
        filter_layout.addWidget(self.tag_combo)
        
        # 添加占位符使按钮居右
        filter_layout.addStretch()
        
        # 刷新按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setFixedWidth(100)
        filter_layout.addWidget(self.refresh_btn)
        
        main_layout.addLayout(filter_layout)

        # 任务表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["任务名称", "完成日期", "预期收入", "实际收入", "支出", "标签"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 5px;
                border: 1px solid #e0e0e0;
                font-weight: bold;
            }
        """)
        
        main_layout.addWidget(self.table)

        # 分页控件
        page_layout = QHBoxLayout()
        page_layout.addStretch()
        
        self.prev_btn = QPushButton("上一页")
        self.prev_btn.setFixedWidth(80)
        page_layout.addWidget(self.prev_btn)
        
        self.page_label = QLabel("第 1 页")
        self.page_label.setFixedWidth(80)
        self.page_label.setAlignment(Qt.AlignCenter)
        page_layout.addWidget(self.page_label)
        
        self.next_btn = QPushButton("下一页")
        self.next_btn.setFixedWidth(80)
        page_layout.addWidget(self.next_btn)
        
        page_layout.addStretch()
        main_layout.addLayout(page_layout)
        
        self.setLayout(main_layout)

        # 事件绑定
        self.month_combo.currentIndexChanged.connect(self.reset_page)
        self.tag_combo.currentIndexChanged.connect(self.reset_page)
        self.refresh_btn.clicked.connect(self.load_tasks)
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn.clicked.connect(self.next_page)
        self.table.cellDoubleClicked.connect(self.show_task_detail)

    def load_months(self):
        """加载可用的月份"""
        cursor = self.db_conn.cursor()
        cursor.execute("""
            SELECT DISTINCT strftime('%Y-%m', due_date) AS month 
            FROM tasks 
            WHERE status = '已完成'
            ORDER BY due_date DESC
        """)
        
        self.month_combo.clear()
        self.month_combo.addItem("全部月份", None)
        
        for month, in cursor.fetchall():
            year, month_num = month.split('-')
            month_name = f"{year}年{int(month_num)}月"
            self.month_combo.addItem(month_name, month)
    
    def load_tags(self):
        """加载标签数据"""
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT tag_id, tag_name FROM tags ORDER BY tag_name")
        
        self.tag_combo.clear()
        self.tag_combo.addItem("全部标签", None)
        
        for tag_id, tag_name in cursor.fetchall():
            self.tag_combo.addItem(tag_name, tag_id)
    
    def get_selected_month(self):
        """获取选中的月份值"""
        return self.month_combo.currentData()
    
    def get_selected_tag(self):
        """获取选中的标签ID"""
        return self.tag_combo.currentData()
    
    def reset_page(self):
        """重置分页到第一页"""
        self.current_page = 1
        self.load_tasks()
    
    def prev_page(self):
        """跳转到上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self.load_tasks()
    
    def next_page(self):
        """跳转到下一页"""
        # 先获取任务总数以确定最大页数
        total_tasks = self.get_total_tasks()
        total_pages = (total_tasks + 9) // 10  # 向上取整
        
        if self.current_page < total_pages:
            self.current_page += 1
            self.load_tasks()
    
    def get_total_tasks(self):
        """获取符合条件的任务总数"""
        month = self.get_selected_month()
        tag_id = self.get_selected_tag()
        
        query = """
            SELECT COUNT(DISTINCT tasks.task_id)
            FROM tasks
            LEFT JOIN task_tags ON tasks.task_id = task_tags.task_id
            WHERE tasks.status = '已完成'
        """
        params = []
        
        if month:
            query += " AND strftime('%Y-%m', due_date) = ?"
            params.append(month)
        
        if tag_id:
            query += " AND task_tags.tag_id = ?"
            params.append(tag_id)
        
        cursor = self.db_conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()[0]
    
    def load_tasks(self):
        """加载并显示任务数据"""
        month = self.get_selected_month()
        tag_id = self.get_selected_tag()
        offset = (self.current_page - 1) * 10
        
        # 查询任务数据
        query = """
            SELECT 
                tasks.task_id, 
                tasks.name, 
                tasks.due_date, 
                tasks.expected_income, 
                tasks.actual_income, 
                tasks.expense,
                GROUP_CONCAT(tags.tag_name, ', ') AS tags
            FROM tasks
            LEFT JOIN task_tags ON tasks.task_id = task_tags.task_id
            LEFT JOIN tags ON task_tags.tag_id = tags.tag_id
            WHERE tasks.status = '已完成'
        """
        params = []
        
        if month:
            query += " AND strftime('%Y-%m', due_date) = ?"
            params.append(month)
        
        if tag_id:
            query += " AND task_tags.tag_id = ?"
            params.append(tag_id)
        
        query += """
            GROUP BY tasks.task_id
            ORDER BY tasks.due_date DESC
            LIMIT 10 OFFSET ?
        """
        params.append(offset)
        
        cursor = self.db_conn.cursor()
        cursor.execute(query, params)
        tasks = cursor.fetchall()
        
        # 更新表格
        self.table.setRowCount(len(tasks))
        
        for row, task in enumerate(tasks):
            task_id, name, due_date, expected_income, actual_income, expense, tags = task
            
            # 转换日期格式
            formatted_date = QDate.fromString(due_date, "yyyy-MM-dd").toString("yyyy-MM-dd")
            
            # 填充表格
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(formatted_date))
            self.table.setItem(row, 2, QTableWidgetItem(f"¥{expected_income:,.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"¥{actual_income:,.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"¥{expense:,.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(tags if tags else "无标签"))
            
            # 存储task_id在隐藏列中
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.item(row, 0).setData(Qt.UserRole, task_id)
        
        # 更新分页信息
        total_tasks = self.get_total_tasks()
        total_pages = (total_tasks + 9) // 10  # 向上取整
        
        self.page_label.setText(f"第 {self.current_page} 页 / 共 {total_pages} 页")
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < total_pages)
    
    def show_task_detail(self, row, column):
        """显示任务详情弹窗"""
        task_id_item = self.table.item(row, 0)
        task_id = task_id_item.data(Qt.UserRole)
        
        if task_id:
            dialog = TaskDetailDialog(task_id, self.db_conn)
            dialog.exec_()


class TaskDetailDialog(QDialog):
    def __init__(self, task_id, db_conn):
        super().__init__()
        self.task_id = task_id
        self.db_conn = db_conn
        self.setWindowTitle("任务详情")
        self.setMinimumWidth(500)
        self.load_task_data()
        self.init_ui()

    def load_task_data(self):
        """从数据库加载任务详情数据"""
        cursor = self.db_conn.cursor()
        
        # 查询任务基本信息
        cursor.execute("""
            SELECT 
                name, description, status, due_date, 
                expected_income, actual_income, expense, created_at
            FROM tasks
            WHERE task_id = ?
        """, (self.task_id,))
        
        task_data = cursor.fetchone()
        if task_data:
            (self.name, self.description, self.status, self.due_date, 
             self.expected_income, self.actual_income, self.expense, self.created_at) = task_data
        
        # 查询任务标签
        cursor.execute("""
            SELECT tags.tag_name
            FROM task_tags
            JOIN tags ON task_tags.tag_id = tags.tag_id
            WHERE task_tags.task_id = ?
        """, (self.task_id,))
        
        self.tags = [tag[0] for tag in cursor.fetchall()]
        if not self.tags:
            self.tags = ["无标签"]

    def init_ui(self):
        layout = QVBoxLayout()
        
        # 基本信息组
        info_group = QGroupBox("基本信息")
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        
        form_layout.addRow("任务名称:", QLabel(self.name))
        form_layout.addRow("状态:", QLabel(self.status))
        
        due_date = QDate.fromString(self.due_date, "yyyy-MM-dd").toString("yyyy年MM月dd日")
        form_layout.addRow("完成日期:", QLabel(due_date))
        
        created_at = QDate.fromString(self.created_at.split()[0], "yyyy-MM-dd").toString("yyyy年MM月dd日")
        form_layout.addRow("创建时间:", QLabel(created_at))
        
        info_group.setLayout(form_layout)
        layout.addWidget(info_group)
        
        # 财务信息组
        finance_group = QGroupBox("财务信息")
        finance_layout = QFormLayout()
        finance_layout.setLabelAlignment(Qt.AlignRight)
        
        finance_layout.addRow("预期收入:", QLabel(f"¥{self.expected_income:,.2f}"))
        finance_layout.addRow("实际收入:", QLabel(f"¥{self.actual_income:,.2f}"))
        finance_layout.addRow("支出:", QLabel(f"¥{self.expense:,.2f}"))
        
        # 计算收益
        profit = self.actual_income - self.expense
        profit_label = QLabel(f"¥{profit:,.2f}")
        profit_label.setStyleSheet(f"color: {'#2ecc71' if profit >= 0 else '#e74c3c'}; font-weight: bold;")
        finance_layout.addRow("净收益:", profit_label)
        
        finance_group.setLayout(finance_layout)
        layout.addWidget(finance_group)
        
        # 描述和标签
        desc_group = QGroupBox("任务描述")
        desc_layout = QVBoxLayout()
        desc_text = QLabel(self.description if self.description else "无描述")
        desc_text.setWordWrap(True)
        desc_layout.addWidget(desc_text)
        desc_group.setLayout(desc_layout)
        layout.addWidget(desc_group)
        
        # 标签
        tags_group = QGroupBox("标签")
        tags_layout = QHBoxLayout()
        
        for tag in self.tags:
            tag_label = QLabel(tag)
            tag_label.setStyleSheet("""
                background-color: #e0f7fa;
                border-radius: 10px;
                padding: 5px 10px;
                margin: 3px;
            """)
            tags_layout.addWidget(tag_label)
        
        tags_layout.addStretch()
        tags_group.setLayout(tags_layout)
        layout.addWidget(tags_group)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setFixedWidth(100)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)


""" if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 设置全局字体
    font = QFont("微软雅黑", 10)
    app.setFont(font)
    
    # 创建并显示任务历史页面
    history_page = TaskHistoryPage()
    history_page.show()
    
    sys.exit(app.exec_()) """