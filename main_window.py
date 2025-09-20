from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Signal
from UI.MainWindow_ui import Ui_MainWindow
import cv2
from PySide6.QtCore import QTimer
from PySide6.QtGui import QImage, QPixmap

class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.init_camera_stream()

 

    def init_camera_stream(self):
        # RTSP URL for Amcrest camera
        rtsp_url = "rtsp://admin:iTpower@123@192.168.0.184:554/cam/realmonitor?channel=1&subtype=0"
        self.cap = cv2.VideoCapture(rtsp_url)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # ~30 FPS

    def update_frame(self):
        if hasattr(self, 'cap') and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_image)
                # Assuming your graphics view is named 'graphicsView' in Ui_MainWindow
                self.ui.graphicsView.setSceneRect(0, 0, w, h)
                if not hasattr(self, 'scene'):
                    from PySide6.QtWidgets import QGraphicsScene
                    self.scene = QGraphicsScene()
                    self.ui.graphicsView.setScene(self.scene)
                self.scene.clear()
                self.scene.addPixmap(pixmap)

    def closeEvent(self, event):
        if hasattr(self, 'cap'):
            self.cap.release()
        event.accept()
