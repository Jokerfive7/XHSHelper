import sys
import sqlite3
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QComboBox)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class StatsDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.db_conn = sqlite3.connect('task_manager.db')  # 修改为你的数据库路径
        self.init_ui()
        self.load_tags()
        self.update_display()

    def init_ui(self):
        self.setWindowTitle('任务统计仪表盘')
        self.setGeometry(100, 100, 1200, 800)

        main_layout = QVBoxLayout()

        # 标签筛选
        self.tag_combo = QComboBox()
        main_layout.addWidget(self.tag_combo)

        # 累计收益显示
        self.total_income_label = QLabel()
        self.total_income_label.setAlignment(Qt.AlignCenter)
        self.total_income_label.setStyleSheet("""
            font-size: 32px; 
            color: #2ecc71;
            font-weight: bold;
            margin: 20px;
        """)
        main_layout.addWidget(self.total_income_label)

        # 图表区域
        self.charts_layout = QHBoxLayout()
        
        # 折线图容器
        self.line_chart_widget = QWidget()
        self.charts_layout.addWidget(self.line_chart_widget, stretch=2)
        
        # 饼图容器
        self.pie_chart_widget = QWidget()
        self.charts_layout.addWidget(self.pie_chart_widget, stretch=1)
        
        main_layout.addLayout(self.charts_layout)
        self.setLayout(main_layout)

        # 事件绑定
        self.tag_combo.currentIndexChanged.connect(self.update_display)

    def load_tags(self):
        """加载标签数据到下拉框"""
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT tag_id, tag_name FROM tags ORDER BY tag_name")
        self.tag_combo.clear()
        self.tag_combo.addItem("全部", None)
        for tag_id, tag_name in cursor.fetchall():
            self.tag_combo.addItem(tag_name, tag_id)

    def get_selected_tag(self):
        """获取当前选中的标签ID"""
        return self.tag_combo.currentData()

    def update_display(self):
        """更新所有显示内容"""
        tag_id = self.get_selected_tag()
        
        # 更新累计收益
        total = self.get_total_income(tag_id)
        self.total_income_label.setText(f"累计收益：¥{total:,.2f}")
        
        # 更新图表
        self.update_line_chart(tag_id)
        self.update_pie_chart(tag_id)

    def get_total_income(self, tag_id):
        """获取累计收益"""
        query = """
            SELECT COALESCE(SUM(expected_income), 0) 
            FROM tasks 
            WHERE status = '已完成'
        """
        params = []
        if tag_id:
            query += " AND task_id IN (SELECT task_id FROM task_tags WHERE tag_id = ?)"
            params.append(tag_id)
        
        cursor = self.db_conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()[0]

    def get_chart_data(self, tag_id):
        """获取图表所需数据"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=29)
        
        # 生成完整日期范围
        dates = [start_date + timedelta(days=i) for i in range(30)]
        
        # 查询每日收益
        daily_query = """
            SELECT DATE(due_date), SUM(expected_income)
            FROM tasks
            WHERE status = '已完成' 
              AND due_date BETWEEN ? AND ?
        """
        params = [start_date.isoformat(), end_date.isoformat()]
        
        if tag_id:
            daily_query += " AND task_id IN (SELECT task_id FROM task_tags WHERE tag_id = ?)"
            params.append(tag_id)
        
        daily_query += " GROUP BY DATE(due_date)"
        
        cursor = self.db_conn.execute(daily_query, params)
        daily_data = {datetime.strptime(d[0], "%Y-%m-%d").date(): d[1] for d in cursor}
        
        # 填充数据
        income = [daily_data.get(date, 0) for date in dates]
        
        # 查询总收支
        total_query = """
            SELECT 
                COALESCE(SUM(expected_income), 0),
                COALESCE(SUM(expense), 0) 
            FROM tasks
            WHERE status = '已完成'
              AND due_date BETWEEN ? AND ?
        """
        total_params = [start_date.isoformat(), end_date.isoformat()]
        if tag_id:
            total_query += " AND task_id IN (SELECT task_id FROM task_tags WHERE tag_id = ?)"
            total_params.append(tag_id)
        
        cursor = self.db_conn.execute(total_query, total_params)
        total_income, total_expense = cursor.fetchone()
        
        return {
            'dates': dates,
            'income': income,
            'total_income': total_income,
            'total_expense': total_expense
        }

    def update_line_chart(self, tag_id):
        """更新折线图"""
        data = self.get_chart_data(tag_id)
        
        # 清除旧图表
        if hasattr(self, 'line_canvas'):
            self.line_canvas.deleteLater()
        
        # 创建新图表
        fig = Figure(figsize=(8, 4))
        ax = fig.add_subplot(111)
        ax.plot(data['dates'], data['income'], marker='o', color='#3498db')
        ax.set_title("Total Income within last 30 days", fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.7)
        fig.autofmt_xdate()
        
        self.line_canvas = FigureCanvas(fig)
        #layout = QVBoxLayout()
        #layout.addWidget(self.line_canvas)
        #self.line_chart_widget.setLayout(layout)
        self.charts_layout.addWidget(self.line_canvas)

    def update_pie_chart(self, tag_id):
        """更新饼图"""
        data = self.get_chart_data(tag_id)
        total_income = data['total_income']
        total_expense = data['total_expense']
        
        # 处理零值情况
        if total_income + total_expense == 0:
            sizes = [1]  # 显示占位
            labels = ['No data']
        else:
            sizes = [total_income, total_expense]
            labels = [f'Income ({total_income:,.2f})', 
                    f'Outcome ({total_expense:,.2f})']
        
        # 清除旧图表
        if hasattr(self, 'pie_canvas'):
            self.pie_canvas.deleteLater()
        
        # 创建新图表
        fig = Figure(figsize=(4, 4))
        ax = fig.add_subplot(111)
        ax.pie(sizes, labels=labels, autopct='%1.1f%%',
               colors=['#2ecc71', '#e74c3c'], startangle=90)
        ax.set_title("Income/Outcome", fontsize=12)
        
        self.pie_canvas = FigureCanvas(fig)
        #layout = QVBoxLayout()
        #layout.addWidget(self.pie_canvas)
        #self.pie_chart_widget.setLayout(layout)
        self.charts_layout.addWidget(self.pie_canvas)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = StatsDashboard()
    window.show()
    sys.exit(app.exec_())