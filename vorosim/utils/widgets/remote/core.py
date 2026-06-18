"""
Remote control widget — connects to a Vorosim payload over UDP.

Sends an initial handshake ("Vorosim: v{version}") on connect; further data
packages are defined later and go through ``send()``, which honors the
enable/disable sending toggle.

UDP is connectionless: "connect" creates a socket bound to the target peer
(via ``socket.connect``) so we can ``send()`` without re-specifying the address,
and sends the handshake. "Disconnect" closes the socket.
"""

import socket
import struct

from typing import Callable, List, Optional, Sequence

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QCheckBox,
)

from vorosim.version import __version__


DEFAULT_REMOTE_HOST = "127.0.0.1"
DEFAULT_REMOTE_PORT = 6767


class RemoteWidget(QGroupBox):
    """UDP client panel: connect/disconnect, status, port field, send toggle."""

    log = pyqtSignal(str)               # human-readable log lines for the host
    connected_changed = pyqtSignal(bool)

    def __init__(self, host: str = DEFAULT_REMOTE_HOST,
                 port: int = DEFAULT_REMOTE_PORT, parent=None):
        super().__init__("Remote (UDP)", parent)
        self._sock = None
        self._sending_enabled = False

        # Callable returning the names of signals to stream over UDP. Set by the
        # host window; queried once per connection to announce the signal list.
        self.signal_name_provider: Optional[Callable[[], List[str]]] = None
        self._signal_list_sent = False

        self._build_ui(host, port)

    # ---------- UI ----------
    def _build_ui(self, host: str, port: int):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Host:"))
        self.host_edit = QLineEdit(host)
        row1.addWidget(self.host_edit, 1)
        row1.addWidget(QLabel("Port:"))
        self.port_edit = QLineEdit(str(port))
        self.port_edit.setValidator(QIntValidator(1, 65535, self))
        self.port_edit.setFixedWidth(70)
        row1.addWidget(self.port_edit)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self._toggle_connection)
        row2.addWidget(self.connect_btn)
        self.send_toggle = QCheckBox("Enable sending")
        self.send_toggle.setChecked(False)
        self.send_toggle.toggled.connect(self._on_send_toggle)
        row2.addWidget(self.send_toggle)
        row2.addStretch(1)
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Status:"))
        self.status_label = QLabel("Disconnected")
        self.status_label.setStyleSheet("font-weight: bold;")
        row3.addWidget(self.status_label)
        row3.addStretch(1)
        layout.addLayout(row3)

    # ---------- helpers ----------
    def port(self) -> int:
        try:
            return int(self.port_edit.text())
        except (TypeError, ValueError):
            return DEFAULT_REMOTE_PORT

    def is_connected(self) -> bool:
        return self._sock is not None

    def _set_status(self, text: str):
        self.status_label.setText(text)

    # ---------- connection control ----------
    def _toggle_connection(self):
        if self.is_connected():
            self.disconnect_remote()
        else:
            self.connect_remote()

    def connect_remote(self):
        if self.is_connected():
            return

        host = self.host_edit.text().strip() or DEFAULT_REMOTE_HOST
        port = self.port()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect((host, port))  # sets default peer for send()
            self._sock = sock
        except OSError as e:
            self._set_status(f"Error: {e}")
            self.log.emit(f"[Remote] Connect failed: {e}")
            return

        self._set_status(f"Connected to {host}:{port}")
        self.log.emit(f"[Remote] Connected to {host}:{port}")
        self.connect_btn.setText("Disconnect")
        self.host_edit.setEnabled(False)
        self.port_edit.setEnabled(False)

        self._send_handshake()
        self._send_signal_list()
        self.connected_changed.emit(True)

    def _send_handshake(self):
        """Send the initial "Vorosim: v{version}" message on connect.

        Always sent on connect — bypasses the enable/disable send toggle.
        """
        message = f"Vorosim: v{__version__}"
        if self._send_raw(message):
            self.log.emit(f"[Remote] Sent handshake: {message}")

    def _send_signal_list(self):
        """Send, once per connection, the names of the signals selected for UDP
        streaming. Sent right after the handshake; bypasses the send toggle.
        """
        if self._signal_list_sent:
            return

        names = list(self.signal_name_provider()) if self.signal_name_provider else []
        message = "Signals: " + ",".join(names)
        if self._send_raw(message):
            self._signal_list_sent = True
            self.log.emit(f"[Remote] Sent signal list: {message}")

    def disconnect_remote(self):
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

        self._signal_list_sent = False
        self._set_status("Disconnected")
        self.log.emit("[Remote] Disconnected")
        self.connect_btn.setText("Connect")
        self.host_edit.setEnabled(True)
        self.port_edit.setEnabled(True)
        self.connected_changed.emit(False)

    # ---------- sending ----------
    def _on_send_toggle(self, checked: bool):
        self._sending_enabled = checked

    def _send_bytes(self, data: bytes) -> bool:
        """Send raw bytes over the connected socket, bypassing the toggle."""
        if self._sock is None:
            return False
        try:
            self._sock.send(data)
            return True
        except OSError as e:
            self.log.emit(f"[Remote] Send failed: {e}")
            return False

    def _send_raw(self, message: str) -> bool:
        """Send a text message, bypassing the enable/disable toggle."""
        return self._send_bytes(message.encode("utf-8"))

    def send(self, message: str) -> bool:
        """Send a text data package, honoring the enable/disable sending toggle.

        Returns False (without sending) when sending is disabled or not
        connected.
        """
        if not self._sending_enabled:
            return False
        return self._send_raw(message)

    def send_values(self, values: Sequence[float]) -> bool:
        """Stream the current raw signal values, honoring the sending toggle.

        Values are packed as little-endian float32, in the same order as the
        signal list announced on connect. No-op when sending is disabled or not
        connected.
        """
        if not self._sending_enabled or self._sock is None:
            return False
        payload = struct.pack(f"<{len(values)}f", *(float(v) for v in values))
        return self._send_bytes(payload)

    # ---------- cleanup ----------
    def closeEvent(self, event):
        self.disconnect_remote()
        super().closeEvent(event)
