import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QPainterPath

class CircleButton(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(100, 100)
        
    def hitButton(self, pos):
        # 创建圆形点击区域
        path = QPainterPath()
        path.addEllipse(self, self.rect())
        return path.contains(pos)

    def enterEvent(self, event):
        if self.hitButton(event.pos()):
            self.setStyleSheet("background: red;")

    def leaveEvent(self, event):
        self.setStyleSheet("background: gray;")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CircleButton()
    window.show()
    sys.exit(app.exec_())