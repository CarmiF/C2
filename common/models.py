
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import datetime

@dataclass
class AgentInfo:
    id: str
    addr: str
    hostname: Optional[str]
    os: Optional[str]
    username: Optional[str]
    privilege: Optional[str]
    pid: Optional[int]
    connected_at: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z")

    def summary(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "addr": self.addr,
            "hostname": self.hostname,
            "os": self.os,
            "username": self.username,
            "privilege": self.privilege,
            "pid": self.pid,
            "connected_at": self.connected_at
        }
