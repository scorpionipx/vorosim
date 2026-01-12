from __future__ import annotations

import csv
import math
import mmap
import os
import struct
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

IS_WINDOWS = os.name == "nt"

MAGIC = b"VSM1"
VERSION = 1

HEADER_FMT = "<4sI Q d I"  # magic, version, counter, timestamp, capacity
HEADER_SIZE = struct.calcsize(HEADER_FMT)

SLOT_NAME_BYTES = 64
SLOT_FMT = f"<{SLOT_NAME_BYTES}s d I I"
SLOT_SIZE = struct.calcsize(SLOT_FMT)

FLAG_ACTIVE = 1


@dataclass
class WinMmapEmulatorConfig:
    tagname: str = "VoroSim_Telemetry"
    capacity: int = 1024
    hz: float = 60.0
    csv_path: Optional[str] = None   # <-- optional now


def _encode_name(name: str) -> bytes:
    raw = name.encode("utf-8")[: SLOT_NAME_BYTES - 1]
    return raw + b"\x00" * (SLOT_NAME_BYTES - len(raw))


def _write_slot(buf: mmap.mmap, idx: int, name: str, value: float, active: bool = True):
    off = HEADER_SIZE + idx * SLOT_SIZE
    flags = FLAG_ACTIVE if active else 0
    struct.pack_into(SLOT_FMT, buf, off, _encode_name(name), float(value), flags, 0)


def _init_mapping(buf: mmap.mmap, capacity: int):
    struct.pack_into(HEADER_FMT, buf, 0, MAGIC, VERSION, 0, time.time(), capacity)
    for i in range(capacity):
        _write_slot(buf, i, "", 0.0, active=False)


# ---------------- CSV support ----------------

def _load_csv_rows(csv_path: str) -> List[Dict[str, float]]:
    rows: List[Dict[str, float]] = []
    with open(csv_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row")

        for r in reader:
            out: Dict[str, float] = {}
            for k, v in r.items():
                try:
                    out[k] = float(v)
                except (TypeError, ValueError):
                    out[k] = 0.0
            rows.append(out)

    if not rows:
        raise ValueError("CSV has no data rows")

    return rows


# ---------------- Main emulator ----------------

def run_emulator(cfg: WinMmapEmulatorConfig):
    if not IS_WINDOWS:
        raise RuntimeError("WinMmapEmulator requires Windows (os.name == 'nt').")

    use_csv = bool(cfg.csv_path and os.path.isfile(cfg.csv_path))
    csv_rows: List[Dict[str, float]] = []
    if use_csv:
        csv_rows = _load_csv_rows(cfg.csv_path)
        print(f"Loaded {len(csv_rows)} rows from {cfg.csv_path}")
    else:
        print("Running in synthetic signal mode")

    size = HEADER_SIZE + cfg.capacity * SLOT_SIZE
    buf = mmap.mmap(-1, size, tagname=cfg.tagname, access=mmap.ACCESS_WRITE)

    _init_mapping(buf, cfg.capacity)

    base_signals = [
        "vehicle.speed_kmh",
        "engine.rpm",
        "throttle",
        "brake",
        "steer",
    ]

    for i, s in enumerate(base_signals):
        _write_slot(buf, i, s, 0.0, active=True)

    counter = 0
    t0 = time.perf_counter()
    dt = 1.0 / max(cfg.hz, 1.0)

    row_idx = 0
    n_rows = len(csv_rows)

    try:
        while True:
            # ---------------- CSV mode ----------------
            if use_csv:
                row = csv_rows[row_idx]

                values = [
                    row.get("vehicle.speed_kmh", 0.0),
                    row.get("engine.rpm", 0.0),
                    row.get("throttle", 0.0),
                    row.get("brake", 0.0),
                    row.get("steer", 0.0),
                ]

                row_idx += 1
                if row_idx >= n_rows:
                    row_idx = 0

            # ---------------- Synthetic mode ----------------
            else:
                t = time.perf_counter() - t0
                values = [
                    100 + 20 * math.sin(t * 0.5),
                    2000 + 1500 * (0.5 + 0.5 * math.sin(t * 1.2)),
                    max(0.0, math.sin(t * 0.8)),
                    max(0.0, math.sin(t * 0.8 + math.pi)),
                    math.sin(t * 0.7),
                ]

            # Write to shared memory
            for i, v in enumerate(values):
                off = HEADER_SIZE + i * SLOT_SIZE
                name_bytes, _, flags, pad = struct.unpack_from(SLOT_FMT, buf, off)
                struct.pack_into(SLOT_FMT, buf, off, name_bytes, float(v), flags, pad)

            counter += 1
            struct.pack_into(HEADER_FMT, buf, 0, MAGIC, VERSION, counter, time.time(), cfg.capacity)

            time.sleep(dt)

    except KeyboardInterrupt:
        pass
    finally:
        buf.close()


if __name__ == "__main__":
    # run_emulator(WinMmapEmulatorConfig(csv_path=None))
    run_emulator(WinMmapEmulatorConfig(csv_path=r"C:\Users\uidq6025\Downloads\telemetry_20000.csv"))
