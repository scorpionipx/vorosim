import time
import threading

from PyQt6.QtCore import QObject, pyqtSignal

from vorosim.utils.win_mmap.assetto import AssettoCorsaSharedMemory


def flatten_ac_sample(sample: dict) -> dict:
    out = {}

    for group_name, group in sample.items():
        if not isinstance(group, dict):
            continue

        for key, value in group.items():
            if isinstance(value, list):
                for i, v in enumerate(value):
                    out[f"{group_name}.{key}[{i}]"] = v
            else:
                out[f"{group_name}.{key}"] = value

    return out


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
        with self._lock:
            return self._latest_t, self._latest_sample

    def start_stream(self):
        if self._running:
            return

        self._running = True
        start = time.perf_counter()

        try:
            self.status.emit("opening shared memory...")
            self._shm = AssettoCorsaSharedMemory()
            self._shm.open()

            self.status.emit("streaming")
            self.log.emit("Streaming started (Assetto Corsa shared memory)")

            while self._running:
                raw = self._shm.read()
                sample = flatten_ac_sample(raw)
                t = time.perf_counter() - start

                with self._lock:
                    self._latest_t = t
                    self._latest_sample = sample

                end_time = time.perf_counter() + self.read_dt
                while self._running and time.perf_counter() < end_time:
                    time.sleep(0.001)

        except Exception as e:
            self.log.emit(f"Worker error: {e}")
            self.status.emit("error")

        finally:
            try:
                if self._shm is not None:
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