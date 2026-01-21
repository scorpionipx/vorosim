import time
import threading
from PyQt6.QtCore import QObject, pyqtSignal

from vorosim.utils.win_mmap.provider.core import WinMmapProvider


class TelemetryWorker(QObject):
    log = pyqtSignal(str)
    status = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, read_hz: float = 100.0):
        super().__init__()
        self.read_dt = 1.0 / max(read_hz, 1.0)
        self._running = False
        self._shm = None

        self._lock = threading.Lock()
        self._latest_t = 0.0
        self._latest_sample = None

    def get_latest(self):
        """Called from UI thread."""
        with self._lock:
            return self._latest_t, self._latest_sample

    def start_stream(self):
        if self._running:
            return
        self._running = True

        start = time.perf_counter()
        try:
            self.status.emit("opening shared memory…")
            self._shm = AssettoCorsaSharedMemory()
            self._shm.open()

            self.status.emit("streaming")
            self.log.emit("Streaming started (100 Hz read)")

            while self._running:
                s = self._shm.read()
                t = time.perf_counter() - start

                with self._lock:
                    self._latest_t = t
                    self._latest_sample = s

                time.sleep(self.read_dt)

        except Exception as e:
            self.log.emit(f"Worker error: {e}")
            self.status.emit("error")

        finally:
            try:
                if self._shm:
                    self._shm.close()
            except Exception:
                pass

            self._shm = None
            self._running = False
            self.status.emit("stopped")
            self.log.emit("Streaming stopped")
            self.finished.emit()

    def stop_stream(self):
        self._running = False
