import base64
import json
import logging
import os
import sys

from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QTimer, QEvent
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QMenuBar, QComboBox, QFileDialog,
)

from vorosim.utils.widgets.console.core import ConsoleWidget
# from vorosim.utils.widgets.plot.qtgraph.core import PlotWidget
from vorosim.utils.widgets.plot.qtchart.core import PlotWidget

from vorosim.utils.win_mmap.provider.core import WinMmapProvider
from vorosim.utils.widgets.signal_picker.core import SignalPickerDialog

from vorosim.version import __version__


DEFAULT_CONFIG_PATH = Path.cwd() / "vorosim_config.json"

os.environ["QT_OPENGL"] = "angle"


class VoroSimMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VoroSim")
        self.resize(1200, 800)

        self.provider = None  # active shared memory provider

        self._build_menu()
        self._build_ui()
        self._build_timer()

        self.is_running = False

        self.btn_play.clicked.connect(self.start_stream)
        self.btn_stop.clicked.connect(self.stop_stream)

        self.btn_save_config.clicked.connect(self.save_configuration)
        self.btn_load_config.clicked.connect(self.load_configuration)

        # initial button states
        self.btn_play.setEnabled(True)
        self.btn_stop.setEnabled(False)

        self._resume_timer = QTimer(self)
        self._resume_timer.setSingleShot(True)
        self._resume_timer.timeout.connect(self._resume_plotting)
        self._plot_paused = False

        # Catch move/resize events for this window
        self.installEventFilter(self)

        # auto-select first provider
        self.target_combo.setCurrentIndex(0)
        self._on_target_changed(0)

        self.sample_idx = 0
        self.sample_dt = 1.0 / 60.0

        self._autoload_default_config()

    def _autoload_default_config(self):
        """
        If ./vorosim_config.json exists, load it automatically at startup.
        """
        if DEFAULT_CONFIG_PATH.exists() and DEFAULT_CONFIG_PATH.is_file():
            self._log(f"[System] Found config: {DEFAULT_CONFIG_PATH}")
            self._load_configuration_from_path(DEFAULT_CONFIG_PATH)

    def _load_configuration_from_path(self, path: Path):
        """
        Loads config from a specific JSON file path (no dialogs).
        """
        try:
            cfg = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            self._log(f"[System] Failed to read config '{path}': {e}")
            return

        # Pause streaming while applying config
        was_running = getattr(self, "is_running", False)
        if was_running:
            self.stop_stream(disconnect=False)

        # ---- Restore window geometry (size+pos) if you saved it ----
        geom_b64 = cfg.get("window_geometry_b64")
        if isinstance(geom_b64, str) and geom_b64:
            try:
                self.restoreGeometry(base64.b64decode(geom_b64.encode("ascii")))
            except Exception:
                pass
        else:
            # Fallback: restore window size/pos if present
            win = cfg.get("window", {})
            w = win.get("width")
            h = win.get("height")
            x = win.get("x")
            y = win.get("y")
            if isinstance(w, int) and isinstance(h, int):
                self.resize(w, h)
            if isinstance(x, int) and isinstance(y, int):
                self.move(x, y)

        # ---- Switch target ----
        target = cfg.get("selected_target")
        if isinstance(target, str) and target:
            idx = self.target_combo.findText(target)
            if idx >= 0:
                # triggers your existing provider switching logic
                self.target_combo.setCurrentIndex(idx)
            else:
                self._log(f"[System] Target '{target}' not found in dropdown. Keeping current.")

        # ---- Restore plots ----
        plots_cfg = cfg.get("plots", {})
        self.plot_top.import_config(plots_cfg.get("top", {}))
        self.plot_bottom.import_config(plots_cfg.get("bottom", {}))

        self._log(f"[System] Loaded configuration: {path}")

        if was_running:
            self.start_stream()

    def start_stream(self):
        # Already running
        if self.is_running:
            return

        # Ensure provider is connected
        if self.provider is None:
            self._log("[System] No provider selected.")
            return

        if not self.provider.is_connected():
            try:
                self.provider.connect()
                self._log("[System] Provider connected.")
            except Exception as e:
                self._log(f"[System] Failed to connect provider: {e}")
                return

        # Start timer (plotting + reading)
        if not self.timer.isActive():
            self.timer.start()

        self.is_running = True
        self.btn_play.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self._log("[System] Streaming started.")

    def stop_stream(self, disconnect: bool = False):
        # Stop timer first so no more reads happen
        if self.timer.isActive():
            self.timer.stop()

        self.is_running = False
        self.btn_play.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self._log("[System] Streaming stopped.")

        # Optional: disconnect provider too
        if disconnect and self.provider is not None and self.provider.is_connected():
            try:
                self.provider.disconnect()
                self._log("[System] Provider disconnected.")
            except Exception as e:
                self._log(f"[System] Failed to disconnect provider: {e}")

    def _pause_plotting(self):
        if self.timer.isActive():
            self.timer.stop()
        self._plot_paused = True

    def _resume_plotting(self):
        if self._plot_paused and self.is_running:
            self.timer.start()
        self._plot_paused_by_move = False

    def eventFilter(self, obj, event):
        # Pause during move/resize; resume shortly after events stop firing
        if obj is self and event.type() in (QEvent.Type.Move, QEvent.Type.Resize):
            self._pause_plotting()
            # Resume 150ms after last move/resize event
            self._resume_timer.start(150)
        return super().eventFilter(obj, event)

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

        # ---------- Left side ----------
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # Top row: playback buttons + provider dropdown
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

        for b in (self.btn_play, self.btn_stop,
                  self.btn_save_config, self.btn_load_config, self.btn_dummy_3, self.btn_dummy_4):
            b.setFixedHeight(28)

        btn_row.addWidget(self.btn_play)
        btn_row.addWidget(self.btn_stop)
        btn_row.addSpacing(10)
        btn_row.addWidget(self.btn_save_config)
        btn_row.addWidget(self.btn_load_config)
        btn_row.addWidget(self.btn_dummy_3)
        btn_row.addWidget(self.btn_dummy_4)
        btn_row.addStretch(1)

        # Target dropdown (shared memory backend selector)
        self.target_combo = QComboBox()
        self.target_combo.setFixedHeight(28)
        self.target_combo.addItem("Windows MMAP Emulator")
        self.target_combo.currentIndexChanged.connect(self._on_target_changed)

        btn_row.addWidget(self.target_combo)

        left_layout.addLayout(btn_row)

        # Two plots
        self.plot_top = PlotWidget("Graph 1")
        self.plot_bottom = PlotWidget("Graph 2")
        if hasattr(self.plot_bottom, 'plot'):
            self.plot_bottom.plot.setXLink(self.plot_top.plot)

        self.plot_top.request_add_signal.connect(self._open_signal_picker_for_plot)
        self.plot_bottom.request_add_signal.connect(self._open_signal_picker_for_plot)

        left_layout.addWidget(self.plot_top, 1)
        left_layout.addWidget(self.plot_bottom, 1)

        # ---------- Right side (consoles) ----------
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
        self.timer.setInterval(10)  # ~60 Hz
        self.timer.timeout.connect(self._on_tick)
        self.timer.start()

    def _on_tick(self):
        if not self.is_running:
            return

        if self.provider is None or not self.provider.is_connected():
            return

        try:
            counter, ts = self.provider.read_header()
            frame = self.provider.read_frame()
        except Exception as e:
            self._log(f"[System] frame read failed: {e}")
            return

        # Choose X: counter is perfect for sync. (Or use ts for wall time.)
        x = float(counter)

        self.plot_top.tick(frame, x)
        self.plot_bottom.tick(frame, x)

    def _log(self, msg: str, level: int = logging.INFO):
        """
        Log a message to both UI console and log file.
        """
        # ---- Log to Python logging ----
        logging.log(level, msg)

        # ---- Log to UI console ----
        # Add timestamp + level so UI matches file
        ts = datetime.now().strftime("%H:%M:%S")
        level_name = logging.getLevelName(level)
        ui_msg = f"[{ts}] [{level_name}] {msg}"

        self.console_a.append_line(ui_msg)

    def _on_target_changed(self, idx: int):
        # disconnect old provider
        if self.provider is not None:
            try:
                self.provider.disconnect()
            except Exception:
                pass
            self.provider = None

        name = self.target_combo.currentText()

        # instantiate provider
        try:
            if name == "Windows MMAP Emulator":
                self.provider = WinMmapProvider(tagname="VoroSim_Telemetry", capacity=1024)
                self.provider.connect()
                self._log("[System] Connected to Windows MMAP Emulator (VoroSim_Telemetry).")
            else:
                self._log(f"[System] Unknown provider: {name}")
                self.provider = None
        except Exception as e:
            self._log(f"[System] Failed to connect: {e}")
            self.provider = None

    def _open_signal_picker_for_plot(self, plot_widget: PlotWidget):
        if self.provider is None or not self.provider.is_connected():
            self._log("[System] No provider connected. Start emulator and select target.")
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
            if self.provider is not None:
                self.provider.disconnect()
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
