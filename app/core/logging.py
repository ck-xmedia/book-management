import json
import logging
import sys
from typing import Any, Dict


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log: Dict[str, Any] = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if record.exc_info:
            log["exc_info"] = self.formatException(record.exc_info)
        if hasattr(record, "asctime"):
            log["time"] = getattr(record, "asctime")
        # Include extra
        for key, value in record.__dict__.items():
            if key not in ("name", "msg", "args", "levelname", "levelno", "pathname", "filename", "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName", "created", "msecs", "relativeCreated", "thread", "threadName", "processName", "process"):
                try:
                    json.dumps({key: value})
                    log[key] = value
                except Exception:
                    log[key] = str(value)
        return json.dumps(log)


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.handlers = []
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(level.upper())


logger = logging.getLogger("app")
