import sys
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPixmap, QPainter, QColor, QIcon

def create_visible_icon():
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor("#00D4FF"))

    painter = QPainter(pixmap)
    painter.setPen(QColor("black"))
    painter.drawText(20, 40, "AI")
    painter.end()

    return QIcon(pixmap)

app = QApplication(sys.argv)

tray = QSystemTrayIcon()
tray.setIcon(create_visible_icon())  # 🔥 IMPORTANT
tray.setToolTip("DeskmateAI Running")

def show_tray():
    tray.show()
    print("Visible:", tray.isVisible())

QTimer.singleShot(0, show_tray)

sys.exit(app.exec())

tray.showMessage("Test", "Tray is working!")