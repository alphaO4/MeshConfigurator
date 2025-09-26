# ui/logging_utils.py
from __future__ import annotations
import logging
import queue

class QueueLogHandler(logging.Handler):
    """Push logging records to a thread-safe queue for the UI to pull."""
    def __init__(self, q: queue.Queue):
        super().__init__()
        self.q = q

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            self.q.put_nowait(msg)
        except Exception:
            pass
