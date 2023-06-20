import sys
from PyQt6.QtWidgets import QApplication

from views import MainWindow

app = QApplication(sys.argv)

main_window = MainWindow()
main_window.show()

app.exit(app.exec())