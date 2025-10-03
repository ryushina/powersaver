
from PySide6.QtWidgets import QApplication, QMessageBox
from login_window import LoginWindow
from main_window import MainWindow
from shared_state import SharedState
import json
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit
from PySide6.QtCore import QTimer

from tapo_controller import TapoPlugController

class DebugWindow(QWidget):
    def __init__(self, shared_state, interval_ms=1000, max_lines=500):
        super().__init__()
        self.shared_state = shared_state
        self.max_lines = max_lines

        self.setWindowTitle("Shared State Debugger")
        self.resize(420, 300)

        layout = QVBoxLayout(self)
        self.text = QPlainTextEdit(self)
        self.text.setReadOnly(True)
        self.text.setPlaceholderText("Waiting for data...")
        layout.addWidget(self.text)

        self.timer = QTimer(self)
        self.timer.setInterval(interval_ms)
        self.timer.timeout.connect(self.update_display)
        self.timer.start()

    def update_display(self):
        snap = self.shared_state.get_snapshot()
        line = json.dumps(snap)
        self.text.appendPlainText(line)


VALID = [("admin", "admin123"), ("user", "user123")]

def main():
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
            tpc = TapoPlugController(
                "rustanlacanilao@gmail.com",
                "iTpower@123",
                "192.168.0.128"
            )
            
            # Connect to Tapo device synchronously
            try:
                print("[DEBUG] Connecting to Tapo device...")
                tpc.connect_sync()
                tapo_state = tpc.get_state_sync()
                print(f"[DEBUG] Tapo connection successful, state: {tapo_state}")
            except Exception as e:
                print(f"[DEBUG] Failed to connect to Tapo: {e}")
                tapo_state = False
            
            shared = SharedState()
            shared.is_tapo_on = tapo_state
              # keep reference with the main window
            login.close()
            main_win = MainWindow(state=shared, tpc=tpc)
            main_win.show()
            dbg = DebugWindow(shared_state=shared, interval_ms=1000, max_lines=500)
            dbg.show()
            main_win._debug_win = dbg
        else:
            QMessageBox.critical(login, "Login", "Invalid username or password.")

    login.submitted.connect(on_submitted)
    app.exec()

#if __name__ == "__main__":
try:
    main()
except Exception as exc:
    print(f"[DEBUG] Exception in main: {exc}")
    import traceback
    traceback.print_exc()
