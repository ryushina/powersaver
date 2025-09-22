
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer
from login_window import LoginWindow
from main_window import MainWindow
from shared_state import SharedState

import asyncio

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer

class DebugWindow(QWidget):
    def __init__(self, shared_state):
        super().__init__()
        self.shared_state = shared_state
        self.setWindowTitle("Shared State Debugger")
        self.resize(300, 200)

        layout = QVBoxLayout()
        self.label = QLabel("Waiting for data...")
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Timer to refresh the label
        self.timer = QTimer(self)
        self.timer.setInterval(1000)  # 1 second
        self.timer.timeout.connect(self.update_display)
        self.timer.start()

    def update_display(self):
        snapshot = self.shared_state.get_snapshot()
        self.label.setText(str(snapshot))

VALID = [("admin", "admin123"), ("user", "user123")]

async def main():
    app = QApplication([])

    login = LoginWindow()
    login.show()

    def on_submitted(username, password):
        if not username or not password:
            QMessageBox.warning(login, "Login", "Username and password are required.")
            return
        

        if (username, password) in VALID:
            print("[DEBUG] Valid credentials, creating MainWindow...")

            # Create shared state
            shared = SharedState()
            main_win = MainWindow(state=shared)
            main_win.show()
            login.close()

            debug_win = DebugWindow(shared)
            debug_win.show()

            main_win._debug_win = debug_win
        else:
            QMessageBox.critical(login, "Login", "Invalid username or password.")

    login.submitted.connect(on_submitted)
    app.exec()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"[DEBUG] Exception in main: {e}")
        import traceback
        traceback.print_exc()
