import sys
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication
from mainwindow import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置全局字体
    font = QFont()
    font.setFamily("微软雅黑")
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())