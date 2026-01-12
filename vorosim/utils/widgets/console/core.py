from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QPlainTextEdit,
)


class ConsoleWidget(QWidget):
    """A small titled console with a clear button."""
    def __init__(self, title: str, parent=None):
        super().__init__(parent)

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.clear_btn = QPushButton("✕")
        self.clear_btn.setFixedSize(22, 22)
        self.clear_btn.setToolTip("Clear console")

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)
        header.addWidget(self.title_label)
        header.addStretch(1)
        header.addWidget(self.clear_btn)

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setPlaceholderText(f"{title} output...")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addLayout(header)
        layout.addWidget(self.console, 1)

        self.clear_btn.clicked.connect(self.console.clear)

    def append_line(self, text: str):
        self.console.appendPlainText(text)