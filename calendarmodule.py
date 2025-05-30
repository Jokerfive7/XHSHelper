from PyQt5.QtWidgets import QCalendarWidget, QGraphicsDropShadowEffect
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QPainter, QColor, QFont
from sqlite3 import Error
from database import TaskManagerDB

class TaskCalendar(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = TaskManagerDB()
        self.setGridVisible(True)
        self.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.setNavigationBarVisible(True)
        
        # 初始化当前月份任务数据
        self.task_counts = {}
        self.load_month_tasks(self.yearShown(), self.monthShown())
        
        # 连接信号
        self.clicked.connect(self.handle_date_click)
        self.currentPageChanged.connect(self.on_page_changed)
        
        # 视觉效果
        self.setup_shadow_effect()

    def setup_shadow_effect(self):
        """添加阴影效果"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(3, 3)
        self.setGraphicsEffect(shadow)

    def paintCell(self, painter, rect, date):
        """自定义单元格绘制"""
        super().paintCell(painter, rect, date)
        
        # 突出显示今天
        if date == QDate.currentDate():
            painter.save()
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(254, 240, 138, 100))
            painter.drawRoundedRect(rect, 5, 5)
            painter.restore()
        
        # 绘制任务标记
        count = self.task_counts.get(date.toString("yyyy-MM-dd"), 0)
        if count > 0:
            painter.save()
            painter.setFont(QFont("Arial", 8, QFont.Bold))
            painter.setPen(QColor("#2D3748"))
            
            # 绘制背景圆
            circle_size = 20
            circle_rect = rect.adjusted(
                rect.width() - circle_size -5, 
                rect.height() - circle_size -5, 
                -5, -5
            )
            painter.setBrush(QColor("#E2E8F0"))
            painter.drawEllipse(circle_rect)
            
            # 绘制任务数量
            text_rect = circle_rect.adjusted(0, 0, 0, 0)
            painter.drawText(text_rect, Qt.AlignCenter, str(count))
            painter.restore()

    def load_month_tasks(self, year: int, month: int):
        """加载当月任务统计"""
        start_date = QDate(year, month, 1)
        end_date = start_date.addMonths(1).addDays(-1)
        
        try:
            cursor = self.db.conn.execute("""
                SELECT DATE(due_date) AS task_date, COUNT(*) 
                FROM tasks 
                WHERE DATE(due_date) BETWEEN ? AND ?
                GROUP BY DATE(due_date)
            """, (start_date.toString("yyyy-MM-dd"),
                  end_date.toString("yyyy-MM-dd")))
            
            self.task_counts = {
                row[0]: row[1] 
                for row in cursor.fetchall()
            }
        except Error as e:
            print(f"加载日历数据失败: {e}")

    def on_page_changed(self, year: int, month: int):
        """月份切换时重新加载数据"""
        self.load_month_tasks(year, month)
        self.updateCells()

    def handle_date_click(self, date: QDate):
        """处理日期点击事件"""
        # 跳转到添加任务页面
        main_window = self.parent().parent().parent()  # 获取MainWindow实例
        main_window.show_add_task()
        
        # 设置默认截止日期
        #main_window.due_date_edit.setDate(date)
        
        # 自动聚焦任务名称输入框
        #main_window.task_name_input.setFocus()