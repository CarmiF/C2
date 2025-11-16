
import json
import struct
import socket
from typing import Optional
from C2.server.config import RECV_BUFFER

def send_message(sock: socket.socket, obj: dict) -> None:
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    sock.sendall(struct.pack(">I", len(data)) + data)

def _recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return b""
        buf += chunk
    return buf

def recv_message(sock: socket.socket) -> Optional[dict]:
    hdr = _recv_exact(sock, 4)
    if not hdr:
        return None
    n = struct.unpack(">I", hdr)[0]
    payload = b""
    while len(payload) < n:
        chunk = sock.recv(min(RECV_BUFFER, n - len(payload)))
        if not chunk:
            return None
        payload += chunk
    try:
        return json.loads(payload.decode("utf-8"))
    except Exception as e:
        raise ProtocolError(f"Invalid JSON payload: {e}")
