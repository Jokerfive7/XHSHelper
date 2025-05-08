import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel

class DemoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.label = QLabel("Hover over me!")
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        # 初始样式
        self.setStyleSheet("""
            QWidget {
                background: #ecf0f1;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
            }
        """)

    def enterEvent(self, event):
        self.setStyleSheet("""
            QWidget {
                background: #3498db;
                border: 2px solid #2980b9;
                border-radius: 5px;
                color: white;
            }
        """)
        self.label.setText("Mouse Entered!")

    def leaveEvent(self, event):
        self.setStyleSheet("""
            QWidget {
                background: #ecf0f1;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                color: black;
            }
        """)
        self.label.setText("Mouse Left!")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DemoWidget()
    window.resize(300, 200)
    window.show()
    sys.exit(app.exec_())