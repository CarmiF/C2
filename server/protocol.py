
from dataclasses import dataclass
from typing import Dict, Any

# Message types
TYPE_HANDSHAKE = "handshake"
TYPE_EXEC = "exec"
TYPE_EXEC_RESULT = "exec_result"

@dataclass
class Handshake:
    id: str
    hostname: str
    os: str
    username: str
    privilege: str
    pid: int

    def to_dict(self) -> Dict[str, Any]:
        return {"type": TYPE_HANDSHAKE, "payload": {
            "id": self.id,
            "hostname": self.hostname,
            "os": self.os,
            "username": self.username,
            "privilege": self.privilege,
            "pid": self.pid
        }}

def exec_request(cmd: str) -> Dict[str, Any]:
    return {"type": TYPE_EXEC, "payload": {"cmd": cmd}}

def is_exec_result(msg: dict) -> bool:
    return msg.get("type") == TYPE_EXEC_RESULT
