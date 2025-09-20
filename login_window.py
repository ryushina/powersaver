
from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Signal
from UI.Login_ui import Ui_Login

class LoginWindow(QMainWindow):
    """Thin wrapper: only gathers inputs and emits a signal."""
    submitted = Signal(str,str)  # emits Credentials

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Login()
        self.ui.setupUi(self)

        # Adjust these names to your .ui object names:
        u = self.ui.le_Username
        p = self.ui.le_Password
        btn = self.ui.btn_Login

        btn.clicked.connect(self._submit)
        u.returnPressed.connect(self._submit)   # Enter to submit
        p.returnPressed.connect(self._submit)

    def _submit(self):
        u = self.ui.le_Username.text().strip()
        p = self.ui.le_Password.text()
        self.submitted.emit(u, p)
