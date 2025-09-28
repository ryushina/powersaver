import os

from shared_state import SharedState
from tapo_controller import TapoPlugController
# ---- Make FFmpeg the preferred backend and set sane RTSP options (must be BEFORE importing cv2) ----
os.environ["OPENCV_VIDEOIO_PRIORITY_FFMPEG"] = "1"   # prefer FFMPEG
os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"     # avoid MSMF on Windows for RTSP
# Force TCP + short timeouts (values are microseconds)
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;3000000|max_delay;500000"

from PySide6.QtWidgets import QMainWindow, QGraphicsScene, QLabel, QSizePolicy
from PySide6.QtCore import QThread, Signal, QObject, Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from diskcache import Cache
from UI.MainWindow_ui import Ui_MainWindow

import cv2
import numpy as np
from urllib.parse import quote
from ultralytics import YOLO


PERSON_CLASS_ID = 0  # COCO id for 'person'


class VideoWorker(QObject):
    frame_ready = Signal(QImage, int)   # (QImage for display, person_count or -1 if skipped)
    error = Signal(str)
    finished = Signal()

    def __init__(
        self,
        rtsp_url: str,
        model_path: str = "yolov8n.pt",
        infer_every_n: int = 3,         # run detection every Nth frame
        draw_boxes: bool = True,
        infer_width: int = 480,         # downsize copy for inference
        reopen_every_failures: int = 10,
        state:SharedState = None,
        tpc: TapoPlugController = None,
    ):
        super().__init__()
        self.rtsp_url = rtsp_url
        self.infer_every_n = max(1, infer_every_n)
        self.draw_boxes = draw_boxes
        self.infer_width = infer_width
        self.reopen_every_failures = max(3, reopen_every_failures)
        self.state = state
        self._running = True
        self._frame_idx = 0
        self._fail_reads = 0
        self.device = "cpu"
        self.state = state
        self.tpc = tpc
        # Load YOLO model
        try:
            print(f"[DEBUG] Loading YOLO model from: {model_path}")
            self.model = YOLO(model_path)
            print("[DEBUG] YOLO model loaded successfully")
        except Exception as e:
            print(f"[DEBUG] Failed to load YOLO model: {e}")
            self.error.emit(f"Failed to load YOLO model: {e}")
            self._running = False
            return

        # Open RTSP with FFMPEG backend
        self.cap = None
        self._open_capture()

    def _open_capture(self):
        print(f"[DEBUG] Attempting to open RTSP stream: {self.rtsp_url}")
        if self.cap:
            try:
                self.cap.release()
                print("[DEBUG] Released previous capture")
            except Exception as e:
                print(f"[DEBUG] Error releasing previous capture: {e}")
        self.cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        # Optional: also set Open/Read timeouts if your OpenCV supports them
        try:
            self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 3000)  # 3s
            self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 3000)  # 3s
            print("[DEBUG] Set capture timeouts to 3000ms")
        except Exception as e:
            print(f"[DEBUG] Error setting timeouts: {e}")
        backend = ""
        try:
            backend = self.cap.getBackendName()
            print(f"[DEBUG] Capture backend: {backend}")
        except Exception as e:
            backend = ""
            print(f"[DEBUG] Error getting backend: {e}")
        if not self.cap.isOpened():
            print(f"[DEBUG] Failed to open RTSP stream (backend={backend or 'unknown'})")
            self.error.emit(f"Failed to open RTSP stream (backend={backend or 'unknown'}).")
            self._running = False
        else:
            print("[DEBUG] Successfully opened RTSP stream")

    def stop(self):
        print("[DEBUG] VideoWorker.stop() called")
        self._running = False

    @staticmethod
    def _to_qimage(frame_rgb: np.ndarray) -> QImage:
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        return QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)

    def run(self):
        try:
            print("[DEBUG] VideoWorker thread started")
            import time
            while self._running:
                # Check if we should stop periodically
                if not self._running:
                    print("[DEBUG] _running flag is False, breaking loop")
                    break

                if not self.cap:
                    print("[DEBUG] No capture object, attempting to open...")
                    self._open_capture()
                    if not self._running:
                        break

                ok, frame_bgr = self.cap.read()
                print(f"[DEBUG] Read frame - ok: {ok}, frame shape: {frame_bgr.shape if frame_bgr is not None else 'None'}")

                if not ok or frame_bgr is None:
                    self._fail_reads += 1
                    print(f"[DEBUG] Read failed, attempt {self._fail_reads}/{self.reopen_every_failures}")
                    if self._fail_reads % self.reopen_every_failures == 0:
                        print("[DEBUG] Reopening RTSP stream...")
                        self.error.emit("Read failed, attempting to reopen RTSP…")
                        self._open_capture()
                    continue
                self._fail_reads = 0
                print(f"[DEBUG] Successfully read frame {self._frame_idx}")

                # Convert to RGB for Qt
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                H0, W0 = frame_rgb.shape[:2]

                person_count = -1
                if (self._frame_idx % self.infer_every_n) == 0:
                    # Downscale copy for faster inference
                    if self.infer_width and W0 > self.infer_width:
                        scale = self.infer_width / float(W0)
                        infer_img = cv2.resize(
                            frame_rgb,
                            (self.infer_width, int(H0 * scale)),
                            interpolation=cv2.INTER_AREA,
                        )
                    else:
                        infer_img = frame_rgb

                    h1, w1 = infer_img.shape[:2]
                    sx, sy = W0 / float(w1), H0 / float(h1)

                    # YOLO predict
                    results = self.model.predict(
                        source=infer_img,    # numpy RGB
                        imgsz=max(w1, h1),   # let YOLO letterbox as needed
                        conf=0.35,
                        device=self.device,
                        verbose=False,
                    )

                    count = 0
                    if results:
                        r = results[0]
                        if r.boxes is not None:
                            for b in r.boxes:
                                cls_id = int(b.cls[0].item()) if b.cls is not None else -1
                                if cls_id == PERSON_CLASS_ID:
                                    count += 1
                                    if self.draw_boxes and b.xyxy is not None:
                                        x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
                                        # map box to original frame size
                                        X1, Y1 = int(x1 * sx), int(y1 * sy)
                                        X2, Y2 = int(x2 * sx), int(y2 * sy)
                                        cv2.rectangle(frame_rgb, (X1, Y1), (X2, Y2), (0, 255, 0), 2)
                    person_count = count

                qimg = self._to_qimage(frame_rgb)
                self.frame_ready.emit(qimg, person_count)
                self._frame_idx += 1
                print(f"[DEBUG] Emitted frame {self._frame_idx}, _running={self._running}")

            self.finished.emit()
        finally:
            try:
                if self.cap:
                    self.cap.release()
            except Exception:
                pass


class MainWindow(QMainWindow):

    def __init__(self, parent=None,state: SharedState = None,tpc:TapoPlugController = None):
        print("[DEBUG] MainWindow.__init__ called")
        super().__init__(parent)
        print("[DEBUG] Setting up UI...")
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.state = state
        self.tpc = tpc
        # Video display label
        print("[DEBUG] Setting up video display label...")
        self.video_label = QLabel(self)
        self.video_label.setGeometry(50, 20, 661, 331)  # Same size as original graphicsView
        self.video_label.setStyleSheet("QLabel { background-color: #000000; border: 1px solid #cccccc; }")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(320, 240)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Show initial message
        self.video_label.setText("Connecting to camera...\nPlease wait...")
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #000000;
                border: 1px solid #cccccc;
                color: #ffffff;
                font-size: 14px;
                qproperty-alignment: AlignCenter;
            }
        """)
        print("[DEBUG] Video display label setup complete")

        # Start camera + AI
        print("[DEBUG] Initializing camera and AI...")
        self.init_camera_and_ai()

        # Optional: tiny heartbeat to show app is alive
        self._tick = 0
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._beat)
        self.status_timer.start(1000)
        self.cache = Cache("./app_cache")
        print("[DEBUG] MainWindow initialization complete")

        # Connect resize event to handle video label resizing
        self.resizeEvent = self._on_resize

    def _beat(self):
        self._tick += 1
        # Keep it quiet; uncomment if you want a subtle heartbeat in the console widget
        # self.ui.consoleDisplay.appendPlainText(f"[tick] {self._tick}")

    def init_camera_and_ai(self):
        print("[DEBUG] Initializing camera and AI...")
        # --- Build RTSP URL (password contains '@' so URL-encode) ---
        user = "admin"
        password_raw = "iTpower@123"
        password_enc = quote(password_raw, safe="")  # -> iTpower%40123
        host = "192.168.0.184"

        # Use sub-stream for lower resolution (easier on CPU). Ensure sub-stream codec is H.264.
        rtsp_url = f"rtsp://{user}:{password_enc}@{host}:554/cam/realmonitor?channel=1&subtype=1"
        print(f"[DEBUG] RTSP URL: {rtsp_url}")

        # Threaded worker
        print("[DEBUG] Creating QThread...")
        self.thread = QThread(self)
        print("[DEBUG] Creating VideoWorker...")
        self.worker = VideoWorker(
            rtsp_url=rtsp_url,
            model_path="yolov8n.pt",
            infer_every_n=3,     # try 2 for more frequent detection, 4 for lighter load
            draw_boxes=True,
            infer_width=480,
            state=self.state,
            tpc=self.tpc
        )
        print("[DEBUG] Moving worker to thread...")
        self.worker.moveToThread(self.thread)

        # Wire signals
        print("[DEBUG] Connecting signals...")
        self.thread.started.connect(self.worker.run)
        self.worker.frame_ready.connect(self.on_frame_ready, Qt.QueuedConnection)
        self.worker.error.connect(self.on_worker_error, Qt.QueuedConnection)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        print("[DEBUG] Starting thread...")
        self.thread.start()

    def on_frame_ready(self, qimg: QImage, person_count: int):
        print(f"[DEBUG] Frame ready - person_count: {person_count}, image size: {qimg.width()}x{qimg.height()}")
        # Update video display
        pix = QPixmap.fromImage(qimg)
        self.video_label.setPixmap(pix)

        # Clear any text when video starts
        if self.video_label.text():
            self.video_label.clear()

        # Update console with latest count
        if person_count >= 0:
            self.ui.consoleDisplay.setPlainText(f"Persons detected: {person_count}")
            self.cache.set("person_count", person_count)
            self.state.set_count(person_count)

    def on_worker_error(self, msg: str):
        print(f"[DEBUG] Worker error: {msg}")
        self.ui.consoleDisplay.appendPlainText(f"[ERROR] {msg}")

    def _on_resize(self, event):
        """Handle window resize to adjust video label size"""
        if hasattr(self, 'video_label'):
            # Calculate new size for video label (maintain aspect ratio)
            new_width = min(self.width() - 100, 661)  # Max width with some margin
            new_height = min(self.height() - 200, 331)  # Max height with some margin
            self.video_label.setGeometry(50, 20, new_width, new_height)
        super().resizeEvent(event)

    def closeEvent(self, event):
        print("[DEBUG] MainWindow closeEvent called")
        try:
            if hasattr(self, "worker") and self.worker:
                print("[DEBUG] Stopping worker...")
                self.worker.stop()
                print(f"[DEBUG] Worker _running flag set to False: {not self.worker._running}")
            if hasattr(self, "thread") and self.thread:
                print(f"[DEBUG] Thread running: {self.thread.isRunning()}")
                if self.thread.isRunning():
                    print("[DEBUG] Quitting thread...")
                    self.thread.quit()
                    #test nga
                    print("[DEBUG] Waiting for thread to finish (5 seconds)...")
                    if not self.thread.wait(5000):  # Increased timeout to 5 seconds
                        print("[DEBUG] Thread did not finish within 5 seconds, terminating...")
                        self.thread.terminate()  # Force terminate if it doesn't respond
                        self.thread.wait()  # Wait for termination to complete
                        print("[DEBUG] Thread terminated forcefully")
                    else:
                        print("[DEBUG] Thread finished successfully")
        except Exception as e:
            print(f"[DEBUG] Error during closeEvent: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("[DEBUG] Calling super().closeEvent(event)")
            super().closeEvent(event)
