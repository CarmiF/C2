# c2/server/cli_recorder.py
import os
import sys
import time
import threading
import queue
import logging
from typing import Optional, TextIO
from .config import LOGS_DIRECTORY

class _WriterThread(threading.Thread):
    def __init__(self, q: "queue.Queue[str]", filepath: str, flush_interval: float = 0.5):
        super().__init__(daemon=True)
        self.q = q
        self.filepath = filepath
        self.flush_interval = flush_interval
        self._stop_event = threading.Event()
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self._fh = open(self.filepath, "a", encoding="utf-8", buffering=1)

    def run(self):
        last_flush = time.time()
        while not self._stop_event.is_set():
            try:
                line = self.q.get(timeout=0.2)
                if line:
                    self._fh.write(line)
            except queue.Empty:
                pass

            if time.time() - last_flush >= self.flush_interval:
                self._fh.flush()
                last_flush = time.time()

        # final drain
        while True:
            try:
                line = self.q.get_nowait()
                self._fh.write(line)
            except queue.Empty:
                break

        self._fh.flush()
        self._fh.close()

    def stop(self):
        self._stop_event.set()


class _TeeStream:
    """
    Duplicate console output to a background writer queue.
    No extra timestamps. Ensures newline separation.
    """
    def __init__(self, real: TextIO, q: "queue.Queue[str]"):
        self._real = real
        self._q = q
        self._buffer: list[str] = []
        self.encoding = getattr(real, "encoding", "utf-8")

    def write(self, s: str):
        # Write to real console
        self._real.write(s)

        # Buffer and push complete lines to queue
        self._buffer.append(s)
        joined = "".join(self._buffer)
        while True:
            pos = joined.find("\n")
            if pos == -1:
                break
            line = joined[:pos + 1]           # include newline
            joined = joined[pos + 1:]
            self._q.put(line)
        self._buffer = [joined] if joined else []

    def flush(self):
        self._real.flush()
        # Optionally flush any partial line as a line
        if self._buffer:
            self._q.put("".join(self._buffer) + "\n")
            self._buffer.clear()

    # Keep common stream API
    def isatty(self):
        return self._real.isatty()
    def fileno(self):
        return self._real.fileno()


class CLISessionRecorder:
    """
    Capture EVERYTHING printed to CLI (stdout/stderr and console logging).

    Writes to:  base_dir/<session_name>/cli.log
    """
    def __init__(self, base_dir: str = LOGS_DIRECTORY):
        self.base_dir = base_dir
        self._orig_stdout: Optional[TextIO] = None
        self._orig_stderr: Optional[TextIO] = None
        self._q: "queue.Queue[str]" = queue.Queue()
        self._writer: Optional[_WriterThread] = None
        self.filepath = os.path.join(self.base_dir, "cli.log")

    def _retarget_console_handlers(self):
        """
        Rebind only console StreamHandlers that pointed to original stdio.
        Do NOT touch FileHandlers/RotatingFileHandlers.
        """
        original_streams = {sys.__stdout__, sys.__stderr__}
        # Root plus real loggers; skip PlaceHolders
        all_names = list(logging.root.manager.loggerDict.keys())
        loggers = [logging.getLogger()] + [
            lg for name in all_names
            if isinstance((lg := logging.getLogger(name)), logging.Logger)
        ]

        for lg in loggers:
            for h in getattr(lg, "handlers", []):
                # Leave file-based handlers alone (they need seek(), rotate, etc.)
                if isinstance(h, logging.FileHandler):
                    continue
                if isinstance(h, logging.StreamHandler):
                    try:
                        # Only retarget handlers bound to original stdio
                        if getattr(h, "stream", None) in original_streams:
                            h.setStream(sys.stdout)  # our TeeStream
                    except Exception:
                        # Best-effort; ignore odd handlers
                        pass

    def start(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        self._writer = _WriterThread(self._q, self.filepath)
        self._writer.start()

        # Swap stdio to tee
        self._orig_stdout, self._orig_stderr = sys.stdout, sys.stderr
        sys.stdout = _TeeStream(self._orig_stdout, self._q)  # no timestamping
        sys.stderr = _TeeStream(self._orig_stderr, self._q)

        # Ensure existing console logging points to tee, but skip file handlers
        self._retarget_console_handlers()

        print(f"[CLI Recorder] Logging to {self.filepath}")

    def stop(self):
        print("[CLI Recorder] Stopping recording…")

        # Restore stdio first so post-stop prints do not go into queue
        if self._orig_stdout is not None:
            sys.stdout = self._orig_stdout
        if self._orig_stderr is not None:
            sys.stderr = self._orig_stderr

        if self._writer is not None:
            self._writer.stop()
            self._writer.join(timeout=2.0)
            self._writer = None

        print(f"[CLI Recorder] Saved log to {self.filepath}")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()
