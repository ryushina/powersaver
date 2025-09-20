# main.py
from PySide6.QtWidgets import QApplication, QMessageBox
from login_window import LoginWindow
from main_window import MainWindow

VALID = [("admin", "admin123"), ("user", "user123")]

def main():
    app = QApplication([])
    main_win = MainWindow()
    login = LoginWindow()
    login.show()

    def on_submitted(username,password):
        if not username or not password:
            QMessageBox.warning(login, "Login", "Username and password are required.")
            return
        if (username, password) in VALID:
            main_win.show()
            login.close()
        else:
            QMessageBox.critical(login, "Login", "Invalid username or password.")

    login.submitted.connect(on_submitted)
    app.exec()

if __name__ == "__main__":
    main()
