import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class GlassCard(QFrame):
    def __init__(self, title, subtitle):
        super().__init__()
        self.setFixedHeight(110)
        self.setStyleSheet("""
        QFrame {
            background: rgba(20, 20, 40, 190);
            border-radius: 18px;
            border: 1px solid rgba(100, 100, 255, 80);
        }
        QFrame:hover {
            border: 2px solid #7aa2ff;
            background: rgba(40, 40, 90, 220);
        }
        """)
        layout = QVBoxLayout(self)
        t = QLabel(title)
        t.setStyleSheet("font-size:16px;font-weight:bold;")
        s = QLabel(subtitle)
        s.setStyleSheet("color:#aaa;")
        layout.addWidget(t)
        layout.addWidget(s)

class SidebarButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setFixedHeight(55)
        self.setStyleSheet("""
        QPushButton {
            background: transparent;
            color: #aaa;
            border: none;
            font-size: 14px;
            text-align: left;
            padding-left: 20px;
        }
        QPushButton:hover {
            color: white;
            background: rgba(100,100,255,40);
        }
        """)

class JarvisLux(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("J.A.R.V.I.S. Lux")
        self.resize(1200, 800)

        self.setStyleSheet("""
        QMainWindow {
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
            stop:0 #0a0f1e, stop:1 #140d2b);
        }
        QLabel {
            color: white;
        }
        """)

        root = QWidget()
        self.setCentralWidget(root)
        main = QHBoxLayout(root)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(90)
        sidebar.setStyleSheet("""
        QFrame {
            background: rgba(10,10,30,230);
            border-right:1px solid rgba(120,120,255,50);
        }
        """)
        s_layout = QVBoxLayout(sidebar)
        s_layout.setSpacing(20)

        for i in ["🏠","🎤","⚙","🎵","🧠"]:
            b = QPushButton(i)
            b.setFixedSize(50,50)
            b.setStyleSheet("""
            QPushButton {
                background: rgba(100,100,255,40);
                border-radius: 15px;
                color:white;
                font-size:20px;
            }
            QPushButton:hover {
                background: rgba(100,100,255,90);
            }
            """)
            s_layout.addWidget(b)
            s_layout.setAlignment(b, Qt.AlignCenter)

        s_layout.addStretch()

        # Content
        content = QWidget()
        c = QVBoxLayout(content)

        title = QLabel("НОВАЯ КОМАНДА")
        title.setStyleSheet("font-size:32px;font-weight:bold;")
        c.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(25)

        cards = [
            ("Sound.PlayWav","JarvisVoice.wav"),
            ("Mouse.ToCoords","100, 200"),
            ("Lux.Pause","2 sec"),
            ("Mouse.Click","Left")
        ]

        r = 0
        for i,(t,s) in enumerate(cards):
            card = GlassCard(t,s)
            grid.addWidget(card,r,i%2)
            if i%2: r+=1

        c.addLayout(grid)
        c.addStretch()

        main.addWidget(sidebar)
        main.addWidget(content)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JarvisLux()
    window.show()
    sys.exit(app.exec_())
