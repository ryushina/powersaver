# log_extractor.py
from PySide6.QtCore import QDate, QTimer, Signal, Qt
from PySide6.QtWidgets import QWidget, QMessageBox
from UI.LogExtractor_ui import Ui_Form
import os
import sqlite3
from datetime import datetime, timedelta
import pandas as pd


class LogExtractor(QWidget):
    # Optional: still emit the picked date (useful for logging/parent listeners)
    date_chosen = Signal(str)

    def __init__(self, parent=None, initial_qdate=None, db_path="tapo_log.db"):
        super().__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setWindowTitle("Extractor")

        self.db_path = db_path

        # Date widget setup
        self.ui.dateSelect.setCalendarPopup(True)
        self.ui.dateSelect.setDisplayFormat("yyyy-MM-dd")
        self.ui.dateSelect.setMinimumDate(QDate(1900, 1, 1))
        self.ui.dateSelect.setMaximumDate(QDate(2100, 12, 31))

        if initial_qdate is not None:
            self.ui.dateSelect.setDate(initial_qdate)
        else:
            QTimer.singleShot(0, lambda: self.ui.dateSelect.setDate(QDate.currentDate()))

        # Wire up the Extract button
        self.ui.pushButton.clicked.connect(self._on_extract_clicked)

    def _on_extract_clicked(self):
        picked = self.ui.dateSelect.date().toString("yyyy-MM-dd")
        self.date_chosen.emit(picked)  # optional signal

        # Ensure the DB exists
        if not os.path.exists(self.db_path):
            QMessageBox.critical(
                self,
                "Database not found",
                f"Can't find the database file:\n{os.path.abspath(self.db_path)}",
            )
            return

        # Build the [start, next_day) window to match the chosen calendar date
        start_dt = datetime.strptime(picked, "%Y-%m-%d")
        next_dt = start_dt + timedelta(days=1)
        start_s = start_dt.strftime("%Y-%m-%d 00:00:00")
        next_s = next_dt.strftime("%Y-%m-%d 00:00:00")

        # Query and export
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Use parameterized query; coerce types for cleaner CSV
                sql = """
                    SELECT
                        id,
                        date_time,
                        CAST(current_count AS INTEGER) AS current_count,
                        CASE
                            WHEN is_tapo_on IN (1, '1', 'true', 'True') THEN 1
                            ELSE 0
                        END AS is_tapo_on
                    FROM logs
                    WHERE date_time >= ? AND date_time < ?
                    ORDER BY date_time ASC
                """
                df = pd.read_sql_query(sql, conn, params=[start_s, next_s])

                # Make boolean pretty (optional)
                if not df.empty:
                    df["is_tapo_on"] = df["is_tapo_on"].astype(bool)

            out_path = f"C:\\logs_{picked}.csv"

            # Even if empty, still create a CSV with headers so it’s clear nothing matched
            df.to_csv(out_path, index=False, encoding="utf-8")

            if df.empty:
                QMessageBox.information(
                    self,
                    "Done (no rows)",
                    f"No logs found for {picked}.\nAn empty CSV with headers was written to:\n{out_path}",
                )
            else:
                QMessageBox.information(
                    self,
                    "Extract complete",
                    f"Exported {len(df):,} rows for {picked} to:\n{out_path}",
                )

            self.close()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Extraction failed",
                f"An error occurred while extracting logs:\n{e}",
            )
