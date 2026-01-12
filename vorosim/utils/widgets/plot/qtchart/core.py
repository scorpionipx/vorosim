from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict

from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QColor, QPen, QPainter
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QSizePolicy, QColorDialog
)

from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis


@dataclass
class SignalTrack:
    signal_name: str
    series: QLineSeries
    x: list[float]
    y: list[float]
    color: QColor
    visible: bool = True
    min_val: float | None = None
    max_val: float | None = None


class SignalRow(QWidget):
    color_clicked = pyqtSignal()
    remove_clicked = pyqtSignal()
    visibility_toggled = pyqtSignal(bool)

    def __init__(self, signal_name: str, color: QColor, parent=None):
        super().__init__(parent)
        self.signal_name = signal_name

        self.btn_color = QPushButton("")
        self.btn_color.setFixedSize(18, 18)
        self.btn_color.setToolTip("Select signal color")
        self._apply_color(color)

        self.lbl = QLabel(signal_name)
        self.lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.lbl_stats = QLabel("min: —   max: —")
        self.lbl_stats.setStyleSheet("font-size: 10px; color: #888;")

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
        lay.addLayout(text_layout, 1)
        lay.addWidget(self.btn_eye)
        lay.addWidget(self.btn_remove)

        self.btn_color.clicked.connect(self.color_clicked.emit)
        self.btn_remove.clicked.connect(self.remove_clicked.emit)
        self.btn_eye.toggled.connect(self.visibility_toggled.emit)

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

        # --- QtCharts: chart + view ---
        self.chart = QChart()
        self.chart.legend().hide()

        # Axes (we manage ranges explicitly for a nice stable plot)
        self.axis_x = QValueAxis()
        self.axis_y = QValueAxis()
        self.axis_x.setTitleText("X")
        self.axis_y.setTitleText("Y")

        self.chart.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)

        # Initial ranges (you can override later)
        self.axis_x.setRange(0.0, 10.0)
        self.axis_y.setRange(0.0, 200.0)

        self.view = QChartView(self.chart)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        self.view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        left_stack = QVBoxLayout()
        left_stack.setContentsMargins(0, 0, 0, 0)
        left_stack.setSpacing(6)
        left_stack.addWidget(self.title_label)
        left_stack.addWidget(self.view, 1)

        # --- rail buttons ---
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
        self.rail.setFixedWidth(200)
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

        self._last_x_min: Optional[float] = None
        self._last_x_max: Optional[float] = None

        self.btn_add.clicked.connect(lambda: self.request_add_signal.emit(self))
        self.btn_clear.clicked.connect(self.clear_signals)

    # ---- optional helpers for axis behavior ----
    def set_y_range(self, ymin: float, ymax: float):
        self.axis_y.setRange(ymin, ymax)

    def set_x_range(self, xmin: float, xmax: float):
        self.axis_x.setRange(xmin, xmax)

    def export_config(self) -> dict:
        signals = []
        for name, tr in self._tracks.items():
            signals.append({
                "name": name,
                "color": tr.color.name(),
                "visible": bool(tr.visible),
            })
        return {
            "title": self.title_label.text(),
            "signals": signals,
        }

    def import_config(self, cfg: dict):
        self.clear_signals()

        for s in cfg.get("signals", []):
            name = s.get("name")
            if not name:
                continue

            color_hex = s.get("color", "#ffffff")
            visible = bool(s.get("visible", True))

            self.add_signal(name, color=QColor(color_hex))
            self.set_signal_visible(name, visible)

    def add_signal(self, signal_name: str, color: Optional[QColor] = None):
        if signal_name in self._tracks:
            return

        if color is None:
            color = QColor(255, 255, 255)

        series = QLineSeries()
        series.setName(signal_name)

        pen = QPen(color)
        pen.setWidth(2)
        series.setPen(pen)

        self.chart.addSeries(series)
        series.attachAxis(self.axis_x)
        series.attachAxis(self.axis_y)

        tr = SignalTrack(signal_name, series, [], [], color, True)
        self._tracks[signal_name] = tr

        row = SignalRow(signal_name, color)
        self._rows[signal_name] = row
        self.rows_layout.insertWidget(self.rows_layout.count() - 1, row)

        row.remove_clicked.connect(lambda sn=signal_name: self.remove_signal(sn))
        row.visibility_toggled.connect(lambda checked, sn=signal_name: self.set_signal_visible(sn, checked))
        row.color_clicked.connect(lambda sn=signal_name: self.pick_color(sn))

    def remove_signal(self, signal_name: str):
        tr = self._tracks.pop(signal_name, None)
        row = self._rows.pop(signal_name, None)
        if tr:
            self.chart.removeSeries(tr.series)
        if row:
            row.setParent(None)
            row.deleteLater()

    def clear_signals(self):
        for sn in list(self._tracks.keys()):
            self.remove_signal(sn)

        self._last_x_min = None
        self._last_x_max = None

    def set_signal_visible(self, signal_name: str, visible: bool):
        tr = self._tracks.get(signal_name)
        if not tr:
            return
        tr.visible = visible
        tr.series.setVisible(visible)

    def pick_color(self, signal_name: str):
        tr = self._tracks.get(signal_name)
        row = self._rows.get(signal_name)
        if not tr or not row:
            return

        col = QColorDialog.getColor(tr.color, self, f"Select color: {signal_name}")
        if not col.isValid():
            return

        tr.color = col
        pen = tr.series.pen()
        pen.setColor(col)
        tr.series.setPen(pen)
        row.set_color(col)

    def tick(self, frame: Dict[str, float], x_value: float, max_points: int = 1000):
        """
        Update all tracks from a single shared frame read.
        - frame: dict {signal_name: value}
        - x_value: current x (time, index, etc.)
        """
        # Track x-range from x_value and buffer window
        # We compute xmin/xmax based on whichever tracks have data.
        visible_any = False
        global_y_min: Optional[float] = None
        global_y_max: Optional[float] = None

        for tr in self._tracks.values():
            if tr.signal_name not in frame:
                continue

            v = frame[tr.signal_name]

            # Stats
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

            # Append
            tr.x.append(x_value)
            tr.y.append(v)

            if len(tr.x) > max_points:
                tr.x = tr.x[-max_points:]
                tr.y = tr.y[-max_points:]

            # Push points to QtCharts
            points = [QPointF(xx, yy) for xx, yy in zip(tr.x, tr.y)]
            tr.series.replace(points)

            # Track global visible y range (for autoscale)
            if tr.visible and points:
                visible_any = True
                ymin = min(tr.y)
                ymax = max(tr.y)
                global_y_min = ymin if global_y_min is None else min(global_y_min, ymin)
                global_y_max = ymax if global_y_max is None else max(global_y_max, ymax)

        # X axis range: follow the latest window (based on any track’s x buffer)
        # Use the first track we find to derive x window (they all share x_value anyway)
        any_track = next(iter(self._tracks.values()), None)
        if any_track and any_track.x:
            xmin = any_track.x[0]
            xmax = any_track.x[-1]
            if xmin != self._last_x_min or xmax != self._last_x_max:
                self.axis_x.setRange(xmin, xmax)
                self._last_x_min = xmin
                self._last_x_max = xmax

        # Optional Y autoscale based on visible series
        # (Comment this out if you want a fixed 0..200 scale always)
        if visible_any and global_y_min is not None and global_y_max is not None:
            if global_y_min == global_y_max:
                # avoid flat range
                global_y_min -= 1.0
                global_y_max += 1.0
            pad = 0.05 * (global_y_max - global_y_min)
            self.axis_y.setRange(global_y_min - pad, global_y_max + pad)
