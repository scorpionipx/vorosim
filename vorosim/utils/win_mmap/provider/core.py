from __future__ import annotations

import mmap
import os
import struct
from typing import Dict, Tuple

IS_WINDOWS = os.name == "nt"

MAGIC = b"VSM1"
HEADER_FMT = "<4sI Q d I"   # magic, version, counter, timestamp, capacity
HEADER_SIZE = struct.calcsize(HEADER_FMT)

SLOT_NAME_BYTES = 64
SLOT_FMT = f"<{SLOT_NAME_BYTES}s d I I"  # name[64], value(float64), flags(uint32), pad(uint32)
SLOT_SIZE = struct.calcsize(SLOT_FMT)

FLAG_ACTIVE = 1


def _decode_name(name_bytes: bytes) -> str:
    name_bytes = name_bytes.split(b"\x00", 1)[0]
    return name_bytes.decode("utf-8", errors="replace")


class WinMmapProvider:
    name = "Windows MMAP Emulator"

    def __init__(self, tagname: str = "VoroSim_Telemetry", capacity: int = 1024):
        self.tagname = tagname
        self.capacity = capacity
        self._buf: mmap.mmap | None = None
        self._index: dict[str, int] = {}

    def connect(self) -> None:
        if not IS_WINDOWS:
            raise RuntimeError("WinMmapProvider requires Windows (os.name == 'nt').")

        size = HEADER_SIZE + self.capacity * SLOT_SIZE
        self._buf = mmap.mmap(-1, size, tagname=self.tagname, access=mmap.ACCESS_READ)

        magic, version, counter, ts, cap = struct.unpack_from(HEADER_FMT, self._buf, 0)
        if magic != MAGIC:
            self.disconnect()
            raise RuntimeError("Bad mapping magic. Is the emulator running?")

        self.capacity = int(cap)
        self._rebuild_index()

    def disconnect(self) -> None:
        if self._buf is not None:
            self._buf.close()
            self._buf = None
        self._index.clear()

    def is_connected(self) -> bool:
        return self._buf is not None

    def read_header(self) -> Tuple[int, float]:
        """
        Returns (counter, timestamp_seconds).
        """
        if self._buf is None:
            raise RuntimeError("Not connected.")
        magic, version, counter, ts, cap = struct.unpack_from(HEADER_FMT, self._buf, 0)
        return int(counter), float(ts)

    def _rebuild_index(self) -> None:
        if self._buf is None:
            return

        idx: dict[str, int] = {}
        for i in range(self.capacity):
            off = HEADER_SIZE + i * SLOT_SIZE
            name_bytes, value, flags, pad = struct.unpack_from(SLOT_FMT, self._buf, off)
            if flags & FLAG_ACTIVE:
                name = _decode_name(name_bytes)
                if name:
                    idx[name] = i
        self._index = idx

    def list_signals(self) -> list[str]:
        self._rebuild_index()
        return sorted(self._index.keys())

    def read_frame(self) -> Dict[str, float]:
        """
        Reads a whole 'frame' of current values once.
        Returns {signal_name: value} for all active signals.
        """
        if self._buf is None:
            raise RuntimeError("Not connected.")

        # Refresh index so newly-added signals appear
        self._rebuild_index()

        frame: Dict[str, float] = {}
        for name, i in self._index.items():
            off = HEADER_SIZE + i * SLOT_SIZE
            # only need value; unpack full slot anyway (still cheap)
            name_bytes, value, flags, pad = struct.unpack_from(SLOT_FMT, self._buf, off)
            frame[name] = float(value)

        return frame
