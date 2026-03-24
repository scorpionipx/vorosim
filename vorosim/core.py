import base64
import json
import logging
import os
import sys

from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QTimer, QEvent, QThread
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QMenuBar,
    QComboBox,
    QFileDialog,
)

from vorosim.utils.widgets.console.core import ConsoleWidget
from vorosim.utils.widgets.plot.qtchart.core import PlotWidget
from vorosim.utils.win_mmap.provider.core import WinMmapProvider
from vorosim.utils.widgets.signal_picker.core import SignalPickerDialog
from vorosim.utils.telemetry.worker import TelemetryWorker

from vorosim.version import __version__


DEFAULT_CONFIG_PATH = Path.cwd() / "vorosim_config.json"

os.environ["QT_OPENGL"] = "angle"


class VoroSimMainWindow(QMainWindow):
    TARGET_AC = "Assetto Corsa Shared Memory"
    TARGET_EMULATOR = "Windows MMAP Emulator"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VoroSim")
        self.resize(1200, 800)

        self.provider = None
        self.worker = None
        self.worker_thread = None

        self.is_running = False
        self._plot_paused = False

        self._build_menu()
        self._build_ui()
        self._build_timer()

        self.btn_play.clicked.connect(self.start_stream)
        self.btn_stop.clicked.connect(self.stop_stream)
        self.btn_save_config.clicked.connect(self.save_configuration)
        self.btn_load_config.clicked.connect(self.load_configuration)

        self.btn_play.setEnabled(True)
        self.btn_stop.setEnabled(False)

        self._resume_timer = QTimer(self)
        self._resume_timer.setSingleShot(True)
        self._resume_timer.timeout.connect(self._resume_plotting)

        self.installEventFilter(self)

        self.target_combo.setCurrentIndex(0)
        self._on_target_changed(0)

        self._autoload_default_config()

    def _autoload_default_config(self):
        if DEFAULT_CONFIG_PATH.exists() and DEFAULT_CONFIG_PATH.is_file():
            self._log(f"[System] Found config: {DEFAULT_CONFIG_PATH}")
            self._load_configuration_from_path(DEFAULT_CONFIG_PATH)

    def _load_configuration_from_path(self, path: Path):
        try:
            cfg = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            self._log(f"[System] Failed to read config '{path}': {e}")
            return

        was_running = self.is_running
        if was_running:
            self.stop_stream()

        geom_b64 = cfg.get("window_geometry_b64")
        if isinstance(geom_b64, str) and geom_b64:
            try:
                self.restoreGeometry(base64.b64decode(geom_b64.encode("ascii")))
            except Exception:
                pass
        else:
            win = cfg.get("window", {})
            w = win.get("width")
            h = win.get("height")
            x = win.get("x")
            y = win.get("y")

            if isinstance(w, int) and isinstance(h, int):
                self.resize(w, h)
            if isinstance(x, int) and isinstance(y, int):
                self.move(x, y)

        target = cfg.get("selected_target")
        if isinstance(target, str) and target:
            idx = self.target_combo.findText(target)
            if idx >= 0:
                self.target_combo.setCurrentIndex(idx)
            else:
                self._log(f"[System] Target '{target}' not found in dropdown. Keeping current.")

        plots_cfg = cfg.get("plots", {})
        self.plot_top.import_config(plots_cfg.get("top", {}))
        self.plot_bottom.import_config(plots_cfg.get("bottom", {}))

        self._log(f"[System] Loaded configuration: {path}")

        if was_running:
            self.start_stream()

    def _build_menu(self):
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        system_menu = menubar.addMenu("System")
        exit_action = system_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(10)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(6)

        self.btn_play = QPushButton("▶")
        self.btn_stop = QPushButton("■")
        self.btn_save_config = QPushButton("Save Configuration")
        self.btn_load_config = QPushButton("Load Configuration")
        self.btn_dummy_3 = QPushButton("B3")
        self.btn_dummy_4 = QPushButton("B4")

        self.btn_dummy_4.setEnabled(False)

        for b in (
            self.btn_play,
            self.btn_stop,
            self.btn_save_config,
            self.btn_load_config,
            self.btn_dummy_3,
            self.btn_dummy_4,
        ):
            b.setFixedHeight(28)

        btn_row.addWidget(self.btn_play)
        btn_row.addWidget(self.btn_stop)
        btn_row.addSpacing(10)
        btn_row.addWidget(self.btn_save_config)
        btn_row.addWidget(self.btn_load_config)
        btn_row.addWidget(self.btn_dummy_3)
        btn_row.addWidget(self.btn_dummy_4)
        btn_row.addStretch(1)

        self.target_combo = QComboBox()
        self.target_combo.setFixedHeight(28)
        self.target_combo.addItem(self.TARGET_AC)
        self.target_combo.addItem(self.TARGET_EMULATOR)
        self.target_combo.currentIndexChanged.connect(self._on_target_changed)

        btn_row.addWidget(self.target_combo)
        left_layout.addLayout(btn_row)

        self.plot_top = PlotWidget("Graph 1")
        self.plot_bottom = PlotWidget("Graph 2")

        if hasattr(self.plot_bottom, "plot") and hasattr(self.plot_top, "plot"):
            self.plot_bottom.plot.setXLink(self.plot_top.plot)

        self.plot_top.request_add_signal.connect(self._open_signal_picker_for_plot)
        self.plot_bottom.request_add_signal.connect(self._open_signal_picker_for_plot)

        left_layout.addWidget(self.plot_top, 1)
        left_layout.addWidget(self.plot_bottom, 1)

        right = QWidget()
        right.setFixedWidth(300)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        self.console_a = ConsoleWidget("Console 1")
        self.console_b = ConsoleWidget("Console 2")
        self.console_c = ConsoleWidget("Console 3")

        right_layout.addWidget(self.console_a, 1)
        right_layout.addWidget(self.console_b, 1)
        right_layout.addWidget(self.console_c, 1)

        root.addWidget(left, 1)
        root.addWidget(right, 0)

    def _build_timer(self):
        self.timer = QTimer(self)
        self.timer.setInterval(16)  # ~60 Hz UI update
        self.timer.timeout.connect(self._on_tick)

    def start_stream(self):
        if self.is_running:
            return

        target = self.target_combo.currentText()

        if target == self.TARGET_AC:
            self._start_ac_worker()
        elif target == self.TARGET_EMULATOR:
            self._start_emulator()
        else:
            self._log(f"[System] Unknown target: {target}")
            return

        if not self.timer.isActive():
            self.timer.start()

        self.is_running = True
        self.btn_play.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self._log("[System] Streaming started.")

    def stop_stream(self):
        if self.timer.isActive():
            self.timer.stop()

        if self.worker is not None:
            try:
                self.worker.stop_stream()
            except Exception as e:
                self._log(f"[System] Failed to stop worker: {e}")

        if self.worker_thread is not None:
            try:
                self.worker_thread.quit()
                self.worker_thread.wait(2000)
            except Exception as e:
                self._log(f"[System] Failed to stop worker thread: {e}")

        self.worker = None
        self.worker_thread = None

        if self.provider is not None and self.provider.is_connected():
            try:
                self.provider.disconnect()
                self._log("[System] Provider disconnected.")
            except Exception as e:
                self._log(f"[System] Failed to disconnect provider: {e}")

        self.provider = None

        self.is_running = False
        self.btn_play.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self._log("[System] Streaming stopped.")

    def _start_ac_worker(self):
        self.worker_thread = QThread()
        self.worker = TelemetryWorker(read_hz=100.0)

        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.start_stream)
        self.worker.log.connect(self._log)
        self.worker.status.connect(self._on_worker_status)
        self.worker.finished.connect(self._on_worker_finished)

        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.worker_thread.start()
        self._log("[System] Assetto Corsa worker started.")

    def _start_emulator(self):
        try:
            self.provider = WinMmapProvider(tagname="VoroSim_Telemetry", capacity=1024)
            self.provider.connect()
            self._log("[System] Connected to Windows MMAP Emulator (VoroSim_Telemetry).")
        except Exception as e:
            self.provider = None
            self._log(f"[System] Failed to connect emulator provider: {e}")
            raise

    def _on_worker_status(self, status: str):
        self._log(f"[Worker] Status: {status}")

    def _on_worker_finished(self):
        self._log("[Worker] Finished.")
        self.worker = None
        self.worker_thread = None

        if self.is_running:
            self.is_running = False
            self.btn_play.setEnabled(True)
            self.btn_stop.setEnabled(False)

        if self.timer.isActive():
            self.timer.stop()

    def _pause_plotting(self):
        if self.timer.isActive():
            self.timer.stop()
        self._plot_paused = True

    def _resume_plotting(self):
        if self._plot_paused and self.is_running:
            self.timer.start()
        self._plot_paused = False

    def eventFilter(self, obj, event):
        if obj is self and event.type() in (QEvent.Type.Move, QEvent.Type.Resize):
            self._pause_plotting()
            self._resume_timer.start(150)
        return super().eventFilter(obj, event)

    def _on_tick(self):
        if not self.is_running:
            return

        target = self.target_combo.currentText()

        if target == self.TARGET_AC:
            self._tick_ac()
        elif target == self.TARGET_EMULATOR:
            self._tick_emulator()

    def _tick_ac(self):
        if self.worker is None:
            return

        try:
            t, sample = self.worker.get_latest()
        except Exception as e:
            self._log(f"[System] worker get_latest failed: {e}")
            return

        if sample is None:
            return

        x = float(t)
        self.plot_top.tick(sample, x)
        self.plot_bottom.tick(sample, x)

    def _tick_emulator(self):
        if self.provider is None or not self.provider.is_connected():
            return

        try:
            counter, ts = self.provider.read_header()
            frame = self.provider.read_frame()
        except Exception as e:
            self._log(f"[System] frame read failed: {e}")
            return

        x = float(counter)
        self.plot_top.tick(frame, x)
        self.plot_bottom.tick(frame, x)

    def _log(self, msg: str, level: int = logging.INFO):
        logging.log(level, msg)

        ts = datetime.now().strftime("%H:%M:%S")
        level_name = logging.getLevelName(level)
        ui_msg = f"[{ts}] [{level_name}] {msg}"

        self.console_a.append_line(ui_msg)

    def _on_target_changed(self, idx: int):
        name = self.target_combo.currentText()

        if self.is_running:
            self.stop_stream()

        if name == self.TARGET_AC:
            self._log("[System] Assetto Corsa target selected.")
            self.provider = None

        elif name == self.TARGET_EMULATOR:
            self._log("[System] Windows MMAP Emulator target selected.")
            self.provider = None

        else:
            self._log(f"[System] Unknown provider: {name}")
            self.provider = None

    def _open_signal_picker_for_plot(self, plot_widget: PlotWidget):
        target = self.target_combo.currentText()

        if target == self.TARGET_AC:
            self._open_signal_picker_ac(plot_widget)
        elif target == self.TARGET_EMULATOR:
            self._open_signal_picker_emulator(plot_widget)

    def _open_signal_picker_ac(self, plot_widget: PlotWidget):
        if self.worker is None:
            self._log("[System] No worker running.")
            return

        try:
            _, sample = self.worker.get_latest()
        except Exception as e:
            self._log(f"[System] Failed to get latest sample: {e}")
            return

        if sample is None:
            self._log("[System] No telemetry sample available yet. Start AC and wait a moment.")
            return

        signals = sorted(sample.keys())

        dlg = SignalPickerDialog(signals, parent=self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return

        selected = dlg.selected_signals()
        if not selected:
            return

        for s in selected:
            try:
                plot_widget.add_signal(s)
            except Exception as e:
                self._log(f"[System] Could not add signal '{s}': {e}")

    def _open_signal_picker_emulator(self, plot_widget: PlotWidget):
        if self.provider is None or not self.provider.is_connected():
            self._log("[System] No emulator provider connected.")
            return

        try:
            signals = self.provider.list_signals()
        except Exception as e:
            self._log(f"[System] Failed to list signals: {e}")
            return

        dlg = SignalPickerDialog(signals, parent=self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return

        selected = dlg.selected_signals()
        if not selected:
            return

        for s in selected:
            try:
                plot_widget.add_signal(s)
            except Exception as e:
                self._log(f"[System] Could not add signal '{s}': {e}")

    def save_configuration(self):
        cfg = {
            "version": __version__,
            "window_geometry_b64": base64.b64encode(self.saveGeometry()).decode("ascii"),
            "selected_target": self.target_combo.currentText(),
            "plots": {
                "top": self.plot_top.export_config(),
                "bottom": self.plot_bottom.export_config(),
            },
        }

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Configuration",
            "vorosim_config.json",
            "JSON Files (*.json);;All Files (*)",
        )
        if not filename:
            return

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
            self._log(f"[System] Saved configuration to: {filename}")
        except Exception as e:
            self._log(f"[System] Failed to save configuration: {e}")

    def load_configuration(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Configuration",
            "",
            "JSON Files (*.json);;All Files (*)",
        )
        if not filename:
            return

        self._load_configuration_from_path(Path(filename))

    def closeEvent(self, event):
        try:
            self.stop_stream()
        except Exception:
            pass
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    win = VoroSimMainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()