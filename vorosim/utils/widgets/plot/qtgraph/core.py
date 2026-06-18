from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict

import pyqtgraph as pg
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QSizePolicy, QColorDialog, QCheckBox
)


pg.setConfigOptions(useOpenGL=True, antialias=False)


@dataclass
class SignalTrack:
    signal_name: str
    curve: pg.PlotDataItem
    x: list[float]
    y: list[float]
    color: QColor
    visible: bool = True
    send_udp: bool = False
    min_val: float | None = None
    max_val: float | None = None


class SignalRow(QWidget):
    color_clicked = pyqtSignal()
    remove_clicked = pyqtSignal()
    visibility_toggled = pyqtSignal(bool)
    send_udp_toggled = pyqtSignal(bool)

    def __init__(self, signal_name: str, color: QColor, parent=None):
        super().__init__(parent)
        self.signal_name = signal_name

        self.btn_color = QPushButton("")
        self.btn_color.setFixedSize(18, 18)
        self.btn_color.setToolTip("Select signal color")
        self._apply_color(color)

        self.lbl = QLabel(signal_name)
        self.lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.lbl_stats= QLabel("min: —   max: —")
        self.lbl_stats.setStyleSheet("font-size: 10px; color: #888;")

        self.chk_send = QCheckBox()
        self.chk_send.setFixedWidth(20)
        self.chk_send.setToolTip("Send this signal over UDP")

        self.btn_eye = QPushButton("👁")
        self.btn_eye.setFixedSize(26, 22)
        self.btn_eye.setCheckable(True)
        self.btn_eye.setChecked(True)
        self.btn_eye.setToolTip("Show/Hide")

        self.btn_remove = QPushButton("✕")
        self.btn_remove.setFixedSize(26, 22)
        self.btn_remove.setToolTip("Remove signal")

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        text_layout.addWidget(self.lbl)
        text_layout.addWidget(self.lbl_stats)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        lay.addWidget(self.btn_color)
        lay.addLayout(text_layout, 1)  # <-- IMPORTANT: stretch here
        lay.addWidget(self.chk_send)
        lay.addWidget(self.btn_eye)
        lay.addWidget(self.btn_remove)

        self.btn_color.clicked.connect(self.color_clicked.emit)
        self.btn_remove.clicked.connect(self.remove_clicked.emit)
        self.btn_eye.toggled.connect(self.visibility_toggled.emit)
        self.chk_send.toggled.connect(self.send_udp_toggled.emit)

    def set_send_udp(self, checked: bool):
        """Set the send-over-UDP checkbox without emitting (for config load)."""
        self.chk_send.blockSignals(True)
        self.chk_send.setChecked(checked)
        self.chk_send.blockSignals(False)

    def set_stats(self, vmin: float | None, vmax: float | None):
        if vmin is None or vmax is None:
            self.lbl_stats.setText("min: —   max: —")
        else:
            self.lbl_stats.setText(f"min: {vmin:.3f}   max: {vmax:.3f}")

    def _apply_color(self, color: QColor):
        self.btn_color.setStyleSheet(
            f"background-color: {color.name()}; border: 1px solid #666; border-radius: 3px;"
        )

    def set_color(self, color: QColor):
        self._apply_color(color)


class PlotWidget(QWidget):
    request_add_signal = pyqtSignal(object)  # emits self

    def __init__(self, title: str, parent=None):
        super().__init__(parent)

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        pg.setConfigOptions(antialias=False)
        self.plot = pg.PlotWidget()
        self.plot.setClipToView(True)
        self.plot.setDownsampling(auto=True, mode="peak")
        self.plot.setBackground(None)
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.plot.setLabel("left", "Y")
        self.plot.setLabel("bottom", "X")
        self.plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        left_stack = QVBoxLayout()
        left_stack.setContentsMargins(0, 0, 0, 0)
        left_stack.setSpacing(6)
        left_stack.addWidget(self.title_label)
        left_stack.addWidget(self.plot, 1)

        self.btn_add = QPushButton("Add Signal")
        self.btn_add.setFixedSize(80, 28)
        self.btn_add.setToolTip("Add signal")

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setFixedSize(50, 28)
        self.btn_clear.setToolTip("Remove all signals")

        rail_header = QHBoxLayout()
        rail_header.setContentsMargins(0, 0, 0, 0)
        rail_header.setSpacing(6)
        rail_header.addWidget(self.btn_add)
        rail_header.addWidget(self.btn_clear)
        rail_header.addStretch(1)

        self.rows_container = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_container)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(6)
        self.rows_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(self.rows_container)

        self.rail = QWidget()
        self.rail.setFixedWidth(330)
        rail_layout = QVBoxLayout(self.rail)
        rail_layout.setContentsMargins(0, 0, 0, 0)
        rail_layout.setSpacing(8)
        rail_layout.addLayout(rail_header)
        rail_layout.addWidget(scroll, 1)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)
        root.addLayout(left_stack, 1)
        root.addWidget(self.rail, 0)

        self._tracks: dict[str, SignalTrack] = {}
        self._rows: dict[str, SignalRow] = {}

        self.btn_add.clicked.connect(lambda: self.request_add_signal.emit(self))
        self.btn_clear.clicked.connect(self.clear_signals)

    def export_config(self) -> dict:
        """
        Returns JSON-serializable config for this plot.
        """
        signals = []
        for name, tr in self._tracks.items():
            signals.append({
                "name": name,
                "color": tr.color.name(),  # "#RRGGBB"
                "visible": bool(tr.visible),
                "send_udp": bool(tr.send_udp),
            })
        return {
            "title": self.title_label.text(),
            "signals": signals,
        }

    def import_config(self, cfg: dict):
        """
        Loads config into this plot (signals + colors + visibility).
        Does not require a provider; it only restores the plot state.
        """
        self.clear_signals()

        for s in cfg.get("signals", []):
            name = s.get("name")
            if not name:
                continue

            color_hex = s.get("color", "#ffffff")
            visible = bool(s.get("visible", True))
            send_udp = bool(s.get("send_udp", False))

            self.add_signal(name, color=QColor(color_hex))
            self.set_signal_visible(name, visible)
            self.set_signal_send_udp(name, send_udp)

    def add_signal(self, signal_name: str, color: Optional[QColor] = None):
        if signal_name in self._tracks:
            return

        if color is None:
            color = QColor(255, 255, 255)

        pen = pg.mkPen(color)
        curve = self.plot.plot([], [], pen=pen, name=signal_name)

        tr = SignalTrack(signal_name, curve, [], [], color, True)
        self._tracks[signal_name] = tr

        row = SignalRow(signal_name, color)
        self._rows[signal_name] = row
        self.rows_layout.insertWidget(self.rows_layout.count() - 1, row)

        row.remove_clicked.connect(lambda sn=signal_name: self.remove_signal(sn))
        row.visibility_toggled.connect(lambda checked, sn=signal_name: self.set_signal_visible(sn, checked))
        row.color_clicked.connect(lambda sn=signal_name: self.pick_color(sn))
        row.send_udp_toggled.connect(lambda checked, sn=signal_name: self.set_signal_send_udp(sn, checked))

    def remove_signal(self, signal_name: str):
        tr = self._tracks.pop(signal_name, None)
        row = self._rows.pop(signal_name, None)
        if tr:
            self.plot.removeItem(tr.curve)
        if row:
            row.setParent(None)
            row.deleteLater()

    def clear_signals(self):
        for sn in list(self._tracks.keys()):
            self.remove_signal(sn)

    def set_signal_visible(self, signal_name: str, visible: bool):
        tr = self._tracks.get(signal_name)
        if not tr:
            return
        tr.visible = visible
        tr.curve.setVisible(visible)

    def set_signal_send_udp(self, signal_name: str, send_udp: bool):
        tr = self._tracks.get(signal_name)
        row = self._rows.get(signal_name)
        if not tr:
            return
        tr.send_udp = send_udp
        if row:
            row.set_send_udp(send_udp)

    def udp_signal_names(self) -> list[str]:
        """Names of signals flagged to be streamed over UDP, in insertion order."""
        return [name for name, tr in self._tracks.items() if tr.send_udp]

    def pick_color(self, signal_name: str):
        tr = self._tracks.get(signal_name)
        row = self._rows.get(signal_name)
        if not tr or not row:
            return
        col = QColorDialog.getColor(tr.color, self, f"Select color: {signal_name}")
        if not col.isValid():
            return
        tr.color = col
        tr.curve.setPen(pg.mkPen(col))
        row.set_color(col)

    def tick(self, frame: Dict[str, float], x_value: float, max_points: int = 500):
        """
        Update all tracks from a single shared frame read.
        """
        for tr in self._tracks.values():
            if tr.signal_name not in frame:
                continue

            v = frame[tr.signal_name]

            changed = False
            if tr.min_val is None or v < tr.min_val:
                tr.min_val = v
                changed = True
            if tr.max_val is None or v > tr.max_val:
                tr.max_val = v
                changed = True

            row = self._rows.get(tr.signal_name)
            if changed and row:
                row.set_stats(tr.min_val, tr.max_val)

            tr.x.append(x_value)
            tr.y.append(v)

            if len(tr.x) > max_points:
                tr.x = tr.x[-max_points:]
                tr.y = tr.y[-max_points:]

            tr.curve.setData(tr.x, tr.y)
