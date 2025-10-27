
from c2.server.protocol import TYPE_HANDSHAKE, TYPE_EXEC, TYPE_EXEC_RESULT
def make_handshake(payload: dict) -> dict:
    return {"type": TYPE_HANDSHAKE, "payload": payload}
