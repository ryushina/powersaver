
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer
from login_window import LoginWindow
from main_window import MainWindow
from shared_state import SharedState
import asyncio
import time
import json
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit
from PySide6.QtCore import QTimer

from tapo_controller import TapoPlugController


# ---------- Debug Window ----------
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
        self.text.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.text.setPlaceholderText("Waiting for data...")
        layout.addWidget(self.text)

        self.timer = QTimer(self)
        self.timer.setInterval(interval_ms)
        self.timer.timeout.connect(self.update_display)
        self.timer.start()

    def update_display(self):
        snap = self.shared_state.get_snapshot()
        # Pretty JSON + timestamp
        line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] " + json.dumps(snap, ensure_ascii=False)
        self.text.appendPlainText(line)

        # Optional: trim the buffer so it doesn't grow forever
        if self.text.blockCount() > self.max_lines:
            cursor = self.text.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.select(cursor.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()  # remove newline

VALID = [("admin", "admin123"), ("user", "user123")]

async def main():
    app = QApplication([])

    login = LoginWindow()
    login.show()

    async def on_submitted(username, password):
        if not username or not password:
            QMessageBox.warning(login, "Login", "Username and password are required.")
            return
        

        if (username, password) in VALID:
            print("[DEBUG] Valid credentials, creating MainWindow...")
            people = []
            # Create shared state
            tpc = TapoPlugController(
                "rustanlacanilao@gmail.com",
                "iTpower@123",
                "192.168.0.128"
            )
            await tpc.connect()
            shared = SharedState()
            shared.is_tapo_on = await tpc.get_state()
            main_win = MainWindow(state=shared,tpc=tpc)
            main_win.show()
            async def check_people():
                while True:
                    await asyncio.sleep(.5)
                    people.append(shared.current_count)
                    if len(people)==25:
                        if all(x == 0 for x in people):
                            await tpc.turn_off()
                        del people[0]
            asyncio.create_task(check_people())
            # Show the DebugWindow *now* and keep a reference so it won't get GC'd.
            dbg = DebugWindow(shared_state=shared, interval_ms=1000, max_lines=500)
            dbg.show()
            main_win._debug_win = dbg  # keep reference with the main window

            # (Optional) a quick keyboard shortcut on the main window to re-show the debugger
            # Press F12 to bring it back to front if you hide/minimize it.
            main_win.shortcut_toggle_dbg = main_win.addAction("Toggle Debug")
            main_win.shortcut_toggle_dbg.setShortcut(Qt.Key_F12)

            def toggle_dbg():
                if dbg.isVisible():
                    dbg.hide()
                else:
                    dbg.show()
                    dbg.raise_()
                    dbg.activateWindow()

            main_win.shortcut_toggle_dbg.triggered.connect(toggle_dbg)

            login.close()


        else:
            QMessageBox.critical(login, "Login", "Invalid username or password.")

    login.submitted.connect(on_submitted)
    app.exec()
#check for git change
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"[DEBUG] Exception in main: {e}")
        import traceback
        traceback.print_exc()
