import logging
from datetime import datetime
from pathlib import Path


def setup_logging():
    # ./logs directory
    logs_dir = Path.cwd() / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Timestamped log filename
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"vorosim_{ts}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),  # optional: also prints to console
        ],
    )

    logging.info("==== VoroSim started ====")


setup_logging()
