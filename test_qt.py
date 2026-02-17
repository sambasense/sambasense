import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel

def test():
    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowTitle("Test Window")
    win.setMinimumSize(400, 300)
    label = QLabel("If you see this, Qt is working.", win)
    win.setCentralWidget(label)
    win.show()
    print("DEBUG: Window shown")
    sys.exit(app.exec())

if __name__ == "__main__":
    test()
