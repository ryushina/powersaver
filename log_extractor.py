# log_extractor.py
from PySide6.QtCore import QDate, QTimer, Signal,Qt
from PySide6.QtWidgets import QWidget
from UI.LogExtractor_ui import Ui_Form

class LogExtractor(QWidget):
    # Emit selected date in "YYYY-MM-DD" when user clicks Extract
    date_chosen = Signal(str)

    def __init__(self, parent=None, initial_qdate=None):
        super().__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setWindowTitle("Extractor")

        # Make date widget nice and default to TODAY (PC clock)
        self.ui.dateSelect.setCalendarPopup(True)
        self.ui.dateSelect.setDisplayFormat("yyyy-MM-dd")
        self.ui.dateSelect.setMinimumDate(QDate(1900, 1, 1))
        self.ui.dateSelect.setMaximumDate(QDate(2100, 12, 31))

        if initial_qdate is not None:
            self.ui.dateSelect.setDate(initial_qdate)
        else:
            # Force after the widget is shown (avoids Designer defaults snapping back)
            QTimer.singleShot(0, lambda: self.ui.dateSelect.setDate(QDate.currentDate()))

        # When the user clicks "Extract"
        self.ui.pushButton.clicked.connect(self._on_extract_clicked)

    def _on_extract_clicked(self):
        picked = self.ui.dateSelect.date().toString("yyyy-MM-dd")
        self.date_chosen.emit(picked)   # tell MainWindow
        self.close()                    # close the subwindow
