from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QLabel
)


class SignalPickerDialog(QDialog):
    def __init__(self, signals: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add signals")
        self.resize(520, 480)

        self._all_signals = list(signals)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search signals...")
        self.search.textChanged.connect(self._apply_filter)

        self.list = QListWidget()
        self.list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)

        self.hint = QLabel("Tip: Ctrl/Shift for multi-select")
        self.hint.setAlignment(Qt.AlignmentFlag.AlignLeft)

        btn_add = QPushButton("Add Selected")
        btn_cancel = QPushButton("Cancel")
        btn_add.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_cancel)

        layout = QVBoxLayout(self)
        layout.addWidget(self.search)
        layout.addWidget(self.list, 1)
        layout.addWidget(self.hint)
        layout.addLayout(btn_row)

        self._populate(self._all_signals)

    def _populate(self, signals: list[str]):
        self.list.clear()
        for s in signals:
            self.list.addItem(QListWidgetItem(s))

    def _apply_filter(self):
        q = self.search.text().strip().lower()
        if not q:
            self._populate(self._all_signals)
            return

        filtered = [s for s in self._all_signals if q in s.lower()]
        self._populate(filtered)

    def selected_signals(self) -> list[str]:
        return [i.text() for i in self.list.selectedItems()]
