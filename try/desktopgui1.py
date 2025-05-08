import sys
from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QPen, QCursor
from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QAction

class InteractiveIcon(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.initAnimation()

    def initUI(self):
        # 窗口设置为无边框、透明背景、始终在最前端
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnBottomHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(QApplication.desktop().screenGeometry())  # 全屏

        # 图标属性
        self.icon_pos = QPoint(200, 200)
        self.icon_radius = 30
        self.icon_color = QColor(255, 160, 90)

        # 拖拽相关变量
        self.dragging = False
        self.offset = QPoint()

    def initAnimation(self):
        # 创建位移动画
        self.anim = QPropertyAnimation(self, b"icon_pos")
        self.anim.setDuration(1000)
        self.anim.setEasingCurve(QEasingCurve.OutBounce)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制图标
        painter.setPen(QPen(Qt.white, 2))
        painter.setBrush(self.icon_color)
        painter.drawEllipse(self.icon_pos, self.icon_radius, self.icon_radius)

    def mousePressEvent(self, event):
        # 判断是否点击在图标区域内
        if (event.pos() - self.icon_pos).manhattanLength() < self.icon_radius:
            self.dragging = True
            self.offset = event.pos() - self.icon_pos
            self.icon_color = QColor(70, 130, 200)  # 拖拽时变色
            self.update()
        else:
            # 右键菜单示例
            if event.button() == Qt.RightButton:
                menu = QMenu(self)
                exit_action = QAction("Exit", self)
                exit_action.triggered.connect(self.close)
                menu.addAction(exit_action)
                menu.exec_(QCursor.pos())

    def mouseMoveEvent(self, event):
        if self.dragging:
            new_pos = event.pos() - self.offset
            self.icon_pos = new_pos
            self.update()

    def mouseReleaseEvent(self, event):
        if self.dragging:
            self.dragging = False
            self.icon_color = QColor(255, 160, 90)
            self.update()
            # 启动动画弹回原位（可选）
            self.anim.setStartValue(self.icon_pos)
            self.anim.setEndValue(QPoint(200, 200))
            self.anim.start()

    def enterEvent(self, event):
        """ 鼠标进入事件 """
        self.current_color = QColor(70, 130, 200)
        self.update()  # 触发重绘

    def leaveEvent(self, event):
        """ 鼠标离开事件 """
        self.current_color = QColor(255, 160, 90)
        self.update()

    # 通过属性动画更新位置
    def set_icon_pos(self, pos):
        self.icon_pos = pos
        self.update()

    def icon_pos(self):
        return self.icon_pos

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InteractiveIcon()
    window.show()
    sys.exit(app.exec_())