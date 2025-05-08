import sys
from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QPainter, QColor, QPen, QCursor, QIcon
from PyQt5.QtWidgets import (QApplication, QWidget, QMenu, QAction, 
                            QSystemTrayIcon, QDialog, QVBoxLayout, QLabel,
                            QHBoxLayout)

class SubMenu(QWidget):
    """ 悬浮子菜单组件，包含4个子图标 """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_icon = parent  # 父级主图标对象
        self.initUI()
        self.initAnimations()

    def initUI(self):
        """ 初始化子菜单界面 """
        # 设置窗口属性：无边框、透明背景
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 水平布局存放4个子图标
        layout = QHBoxLayout()
        layout.setSpacing(15)  # 图标间距
        layout.setContentsMargins(20, 10, 20, 20)  # 边距（左，上，右，下）
        
        self.icons = []
        for i in range(1, 5):
            # 创建带样式的子图标（使用QLabel模拟按钮）
            icon = QLabel(f"{i}", self)
            # 使用样式表设置外观（渐变背景+圆角）
            icon.setStyleSheet("""
                QLabel {
                    background: qradialgradient(cx:0.5, cy:0.5, radius: 0.5,
                        fx:0.5, fy:0.5, stop:0 white, stop:1 #88FF9999);
                    border-radius: 20px;  /* 圆形半径 */
                    min-width: 40px;      /* 最小尺寸 */
                    min-height: 40px;
                    font: bold 14px;      /* 字体样式 */
                    color: #333;
                }
                QLabel:hover {  /* 鼠标悬停效果 */
                    background: qradialgradient(cx:0.5, cy:0.5, radius: 0.5,
                        fx:0.5, fy:0.5, stop:0 white, stop:1 #99FFAAAA);
                }
            """)
            icon.setAlignment(Qt.AlignCenter)  # 文字居中
            
            # 绑定点击事件：使用lambda传递参数i
            icon.mousePressEvent = lambda event, num=i: self.openWindow(num)
            
            layout.addWidget(icon)
            self.icons.append(icon)
        
        self.setLayout(layout)
        self.adjustSize()  # 自动调整窗口大小
        self.hide()       # 初始隐藏

    def initAnimations(self):
        """ 初始化显示动画 """
        # 几何形状动画：改变窗口的位置和大小
        self.show_anim = QPropertyAnimation(self, b"geometry")
        self.show_anim.setDuration(300)  # 动画时长300ms
        self.show_anim.setEasingCurve(QEasingCurve.OutBack)  # 弹性效果

    def showEvent(self, event):
        """ 显示事件触发动画 """
        # 根据父图标位置计算显示坐标
        parent_pos = self.parent_icon.icon_pos
        # 起始位置：父图标下方，高度为1（几乎不可见）
        start_rect = QRect(parent_pos.x() - 10, parent_pos.y(), 
                          self.width(), 1)
        # 结束位置：居中显示在父图标下方50像素处
        end_rect = QRect(parent_pos.x() - self.width()//2, 
                        parent_pos.y() + 50,
                        self.width(), self.height())
        
        # 设置动画参数并启动
        self.show_anim.setStartValue(start_rect)
        self.show_anim.setEndValue(end_rect)
        self.show_anim.start()
        super().showEvent(event)

    def openWindow(self, num):
        """ 打开对应编号的窗口 """
        window = QDialog(self)  # 创建对话框窗口
        window.setWindowTitle(f"Window {num}")
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"This is window {num}"))
        window.setLayout(layout)
        window.exec_()  # 模态显示

class InteractiveIcon(QWidget):
    """ 主图标类，实现可拖拽和悬停菜单 """
    def __init__(self):
        super().__init__()
        self.initUI()        # 初始化界面
        #self.initAnimation()# 初始化动画
        self.initTray()     # 初始化系统托盘
        
        self.sub_menu = SubMenu(self)  # 创建子菜单实例
        self.hover_timer = None        # 悬停计时器（未使用）

    def initTray(self):
        """ 初始化系统托盘图标 """
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(QIcon("icon.png"))  # 需要准备图标文件
        
        # 创建右键菜单
        menu = QMenu()
        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(self.cleanExit)
        menu.addAction(quit_action)
        
        self.tray.setContextMenu(menu)
        self.tray.show()

    def cleanExit(self):
        """ 安全退出程序 """
        self.tray.hide()      # 隐藏托盘图标
        QApplication.quit()   # 退出应用

    def initUI(self):
        """ 初始化主界面 """
        # 窗口属性设置
        self.setWindowFlags(Qt.FramelessWindowHint |  # 无边框
                           Qt.WindowStaysOnBottomHint |  # 显示在底层
                           Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景
        self.setGeometry(QApplication.desktop().screenGeometry())  # 全屏

        # 图标属性
        self.icon_pos = QPoint(200, 200)   # 初始位置
        self.icon_radius = 30              # 半径
        self.icon_color = QColor(255, 160, 90)  # 初始颜色

        # 拖拽状态变量
        self.dragging = False  # 是否正在拖拽
        self.offset = QPoint() # 鼠标点击位置与图标中心的偏移

    def enterEvent(self, event):
        """ 鼠标进入主图标区域事件 """
        if (event.pos() - self.icon_pos).manhattanLength() < self.icon_radius:
            self.sub_menu.show()  # 显示子菜单

    #def leaveEvent(self, event):
        """ 鼠标离开主图标区域事件 """
        # 检查鼠标是否在子菜单区域内
     #   if not self.sub_menu.geometry().contains(event.globalPos()):
      #      self.sub_menu.hide()

    def mousePressEvent(self, event):
        """ 鼠标按下事件处理 """
        # 计算点击位置与图标的曼哈顿距离（粗略判断是否点击在图标上）
        if (event.pos() - self.icon_pos).manhattanLength() < self.icon_radius:
            self.dragging = True
            self.offset = event.pos() - self.icon_pos  # 计算偏移量
            self.icon_color = QColor(70, 130, 200)    # 拖拽时变色
            self.sub_menu.hide()  # 隐藏子菜单
            self.update()

            # 右键点击显示菜单
        if event.button() == Qt.RightButton:
            menu = QMenu(self)
            exit_action = QAction("Exit", self)
            exit_action.triggered.connect(self.cleanExit)
            menu.addAction(exit_action)
            menu.exec_(QCursor.pos())  # 在鼠标位置显示菜单

    def mouseMoveEvent(self, event):
        """ 鼠标移动事件处理 """
        if self.dragging:
            # 计算新位置（鼠标当前位置 - 偏移量）
            new_pos = event.pos() - self.offset
            self.icon_pos = new_pos
            self.update()  # 触发重绘
            
            # 同步更新子菜单位置（居中显示在图标下方）
            self.sub_menu.move(self.icon_pos.x() - self.sub_menu.width()//2,
                             self.icon_pos.y() + 50)

    def paintEvent(self, event):
        """ 绘制主图标和指示箭头 """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # 抗锯齿
        
        # 绘制主图标（圆形）
        painter.setPen(QPen(Qt.white, 2))  # 白色边框
        painter.setBrush(self.icon_color)  # 填充颜色
        painter.drawEllipse(self.icon_pos, self.icon_radius, self.icon_radius)
        
        # 当子菜单可见时，绘制指示箭头
        if self.sub_menu.isVisible():
            arrow = [
                QPoint(self.icon_pos.x(), self.icon_pos.y() + self.icon_radius),      # 顶点
                QPoint(self.icon_pos.x() - 8, self.icon_pos.y() + self.icon_radius + 15), # 左下
                QPoint(self.icon_pos.x() + 8, self.icon_pos.y() + self.icon_radius + 15)  # 右下
            ]
            painter.drawPolygon(arrow)  # 绘制三角形

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 防止关闭窗口时退出程序
    
    window = InteractiveIcon()
    window.show()
    
    sys.exit(app.exec_())