
from dataclasses import dataclass, field
from queue import Queue
from typing import Dict, Optional
import threading
from C2.common.models import AgentInfo
import logging
import os
from datetime import datetime
import queue
from .config import LOGS_DIRECTORY


class AgentEntry:
    def __init__(self, info, conn):
        self.info = info                  # AgentInfo
        self.conn = conn                  # socket
        self.inbox = queue.Queue()
        self.alive = True
        self.lock = threading.Lock()

        # Optional per-session working directory state
        self.cwd = None

        # ---- short id exposed as attribute (or use @property below) ----
        # If id is numeric or string, use it directly; otherwise take first 8 chars
        _id = str(info.id)
        self.short = _id if _id.isdigit() else _id[:8]

        # ---- per-agent session logger ----
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_host = (info.hostname or "unknown").replace(os.sep, "_")
        base_dir = os.path.join(LOGS_DIRECTORY, "agents", f"{self.short}-{safe_host}")
        os.makedirs(base_dir, exist_ok=True)

        self.log_path = os.path.join(base_dir, "session.log")
        self.logger = logging.getLogger(f"agent.{self.short}.{ts}")
        self.logger.setLevel(logging.INFO)

        fh = logging.FileHandler(self.log_path, encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        self.logger.addHandler(fh)
        self.logger.propagate = False  # keep these logs out of the global console/file

        self.logger.info("=== Agent session started ===")
        self.logger.info(
            "AgentID=%s Hostname=%s OS=%s User=%s Priv=%s PID=%s Addr=%s",
            self.info.id, self.info.hostname, self.info.os, self.info.username,
            self.info.privilege, self.info.pid, self.info.addr
        )

class SessionRegistry:
    def __init__(self):
        self._by_id: Dict[str, AgentEntry] = {}
        self._lock = threading.Lock()

    def add(self, entry: AgentEntry) -> None:
        with self._lock:
            self._by_id[entry.info.id] = entry

    def remove(self, id: str) -> None:
        with self._lock:
            self._by_id.pop(id, None)

    def list(self) -> Dict[str, AgentEntry]:
        with self._lock:
            return dict(self._by_id)

    def get(self, id: str) -> Optional[AgentEntry]:
        with self._lock:
            return self._by_id.get(id)

    def get_by_short_prefix(self, prefix: str) -> Optional[AgentEntry]:
        with self._lock:
            for e in self._by_id.values():
                if e.short.startswith(prefix):
                    return e
            return None
