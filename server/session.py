
from dataclasses import dataclass, field
from queue import Queue
from typing import Dict, Optional
import threading
from c2.common.models import AgentInfo
from c2.common.utils import short_id

@dataclass
class AgentEntry:
    info: AgentInfo
    conn: object
    inbox: Queue = field(default_factory=Queue)
    lock: threading.Lock = field(default_factory=threading.Lock)
    alive: bool = True

    @property
    def short(self) -> str:
        return short_id(self.info.id)

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
