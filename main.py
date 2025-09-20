# main.py
from PySide6.QtWidgets import QApplication, QMessageBox
from login_window import LoginWindow
from main_window import MainWindow

VALID = [("admin", "admin123"), ("user", "user123")]

def main():
    print("[DEBUG] Starting QApplication...")
    app = QApplication([])

    print("[DEBUG] Creating LoginWindow...")
    login = LoginWindow()
    login.show()
    print("[DEBUG] LoginWindow shown")

    def on_submitted(username,password):
        print(f"[DEBUG] Login submitted - username: {username}, password: {password}")
        if not username or not password:
            print("[DEBUG] Empty username or password")
            QMessageBox.warning(login, "Login", "Username and password are required.")
            return
        if (username, password) in VALID:
            print("[DEBUG] Valid credentials, creating MainWindow...")
            main_win = MainWindow()
            main_win.show()
            print("[DEBUG] MainWindow shown, closing login...")
            login.close()
        else:
            print("[DEBUG] Invalid credentials")
            QMessageBox.critical(login, "Login", "Invalid username or password.")

    login.submitted.connect(on_submitted)
    print("[DEBUG] Starting app.exec()...")
    app.exec()

if __name__ == "__main__":
    try:
        print("[DEBUG] Starting main()...")
        main()
    except Exception as e:
        print(f"[DEBUG] Exception in main: {e}")
        import traceback
        traceback.print_exc()
