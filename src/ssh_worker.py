"""SSH worker thread with interactive console support."""
import logging
import os
import threading
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class SSHWorker(QThread):
    """Worker thread that manages one SSH connection.
    
    Supports both one-shot command execution and an interactive shell
    where commands can be sent incrementally.
    """

    output_received = Signal(str)
    command_finished = Signal(int, str)  # exit_code, output
    connection_status = Signal(str)      # "connected" | "disconnected" | "error"
    error_occurred = Signal(str)         # error message

    def __init__(self, hostname: str, port: int, username: str,
                 pem_path: str, command: str | None = None):
        super().__init__()
        self.hostname = hostname
        self.port = port
        self.username = username
        self.pem_path = pem_path
        self.initial_command = command

        self.client = None
        self.channel = None
        self._stop_event = threading.Event()
        self._cmd_queue: list[str] = []
        self._cmd_lock = threading.Lock()
        self._connected = False

    # ── Public control methods ───────────────────────────────────

    def is_connected(self) -> bool:
        return self._connected

    def send_command(self, command: str):
        """Queue a command for the interactive shell."""
        with self._cmd_lock:
            self._cmd_queue.append(command)

    def disconnect(self):
        """Signal the worker to close the connection."""
        self._stop_event.set()

    def execute_script(self, script_content: str, remote_path: str):
        """Upload script content and execute it remotely.
        
        Uses SFTP to upload, then executes via shell.
        """
        # Queue: first upload the script, then make executable, then run
        self.send_command(f"cat > {remote_path} << 'VPS_MANAGER_EOF'\n{script_content}\nVPS_MANAGER_EOF")
        self.send_command(f"chmod +x {remote_path}")
        self.send_command(f"bash {remote_path}")

    # ── Thread run loop ──────────────────────────────────────────

    def run(self):
        try:
            import paramiko
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            self.output_received.emit(f"[Connecting to {self.username}@{self.hostname}:{self.port}...]\n")

            self.client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                key_filename=self.pem_path,
                timeout=10,
            )

            self._connected = True
            self.connection_status.emit("connected")
            self.output_received.emit(f"[Connected to {self.hostname}]\n")

            if self.initial_command:
                self._run_command_mode(self.initial_command)
            else:
                self._run_interactive_shell()

        except Exception as e:
            self.error_occurred.emit(str(e))
            self.output_received.emit(f"[ERROR] {e}\n")
            self.command_finished.emit(-1, str(e))
        finally:
            self._cleanup()

    # ── Command mode (one-shot) ──────────────────────────────────

    def _run_command_mode(self, command: str):
        """Execute a single command and exit."""
        import paramiko
        stdin, stdout, stderr = self.client.exec_command(command, timeout=30)
        exit_code = stdout.channel.recv_exit_status()

        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")

        if out:
            self.output_received.emit(out)
        if err:
            self.output_received.emit(f"[STDERR]\n{err}")

        self.output_received.emit(f"\n[Exit code: {exit_code}]\n")
        self.command_finished.emit(exit_code, out + err)

    # ── Interactive shell mode ───────────────────────────────────

    def _run_interactive_shell(self):
        """Keep an interactive shell open and process queued commands."""
        import paramiko
        self.channel = self.client.invoke_shell(term="xterm-256color", width=120, height=40)

        self.output_received.emit("[Interactive shell opened. Type commands below.]\n")

        while not self._stop_event.is_set() and not self.channel.closed:
            # Read available output from the channel
            if self.channel.recv_ready():
                try:
                    data = self.channel.recv(4096).decode("utf-8", errors="replace")
                    self.output_received.emit(data)
                except Exception as e:
                    logger.warning("Error reading channel: %s", e)
                    break

            if self.channel.recv_stderr_ready():
                try:
                    data = self.channel.recv_stderr(4096).decode("utf-8", errors="replace")
                    self.output_received.emit(f"[stderr] {data}")
                except Exception:
                    break

            # Send queued commands
            with self._cmd_lock:
                if self._cmd_queue:
                    cmd = self._cmd_queue.pop(0)
                    self.channel.send(cmd + "\n")
                    self.output_received.emit(f"> {cmd}\n")

            # Sleep to avoid busy-waiting
            self.msleep(50)

        if not self.channel.closed:
            self.channel.close()

    # ── Cleanup ──────────────────────────────────────────────────

    def _cleanup(self):
        self._connected = False
        self.connection_status.emit("disconnected")
        try:
            if self.channel and not self.channel.closed:
                self.channel.close()
        except Exception:
            pass
        try:
            if self.client:
                self.client.close()
        except Exception:
            pass
