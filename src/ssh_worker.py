"""SSH worker thread with interactive console support and SFTP script upload."""
import logging
import threading

from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class SSHWorker(QThread):
    """Worker thread that manages one SSH connection.

    Supports both one-shot command execution and an interactive shell
    where commands can be sent incrementally. Scripts are uploaded via
    SFTP on the background thread before execution.
    """

    output_received = Signal(str)
    command_finished = Signal(int, str)   # exit_code, output
    connection_status = Signal(str)       # "connected" | "disconnected"
    error_occurred = Signal(str)          # error message

    # ── Internal action types for the queue ─────────────────────────────────
    _CMD   = "cmd"     # send a shell command string
    _EXEC  = "exec"    # upload script bytes via SFTP then run it

    def __init__(
        self,
        hostname: str,
        port: int,
        username: str,
        pem_path: str,
        command: str | None = None,
    ):
        super().__init__()
        self.hostname = hostname
        self.port = port
        self.username = username
        self.pem_path = pem_path
        self.initial_command = command

        self.client = None
        self.channel = None
        self._stop_event = threading.Event()
        self._queue: list[dict] = []
        self._queue_lock = threading.Lock()
        self._connected = False

    # ── Public control methods ────────────────────────────────────────────────

    def is_connected(self) -> bool:
        return self._connected

    def send_command(self, command: str):
        """Queue a raw command to be typed into the interactive shell."""
        with self._queue_lock:
            self._queue.append({"type": self._CMD, "data": command})

    def disconnect(self):
        """Signal the worker to close the connection."""
        self._stop_event.set()

    def execute_script(self, script_content: str, remote_path: str):
        """Queue a script for SFTP upload + remote execution.

        The script bytes are uploaded via a dedicated SFTP channel (opened
        on the background thread) so the operation never blocks the GUI.
        After uploading, ``bash <remote_path>`` is injected into the shell
        so output streams naturally in real time.
        """
        with self._queue_lock:
            self._queue.append({
                "type": self._EXEC,
                "content": script_content,
                "remote_path": remote_path,
            })

    # ── Thread run loop ───────────────────────────────────────────────────────

    def run(self):
        try:
            import paramiko
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            self.output_received.emit(
                f"\x1b[1;34m[Connecting to {self.username}@{self.hostname}:{self.port}...]\x1b[0m\n"
            )

            self.client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                key_filename=self.pem_path,
                timeout=15,
            )

            self._connected = True
            self.connection_status.emit("connected")
            self.output_received.emit(
                f"\x1b[1;32m[Connected to {self.hostname}]\x1b[0m\n"
            )

            if self.initial_command:
                self._run_command_mode(self.initial_command)
            else:
                self._run_interactive_shell()

        except Exception as e:
            self.error_occurred.emit(str(e))
            self.output_received.emit(f"\x1b[1;31m[ERROR] {e}\x1b[0m\n")
            self.command_finished.emit(-1, str(e))
        finally:
            self._cleanup()

    # ── Command mode (one-shot) ───────────────────────────────────────────────

    def _run_command_mode(self, command: str):
        """Execute a single command and exit."""
        stdin, stdout, stderr = self.client.exec_command(command, timeout=60)
        exit_code = stdout.channel.recv_exit_status()

        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")

        if out:
            self.output_received.emit(out)
        if err:
            self.output_received.emit(f"\x1b[33m[STDERR]\x1b[0m\n{err}")

        self.output_received.emit(f"\n\x1b[90m[Exit code: {exit_code}]\x1b[0m\n")
        self.command_finished.emit(exit_code, out + err)

    # ── Interactive shell mode ────────────────────────────────────────────────

    def _run_interactive_shell(self):
        """Keep an interactive shell open and process queued actions."""
        self.channel = self.client.invoke_shell(
            term="xterm-256color", width=220, height=50
        )
        self.output_received.emit(
            "\x1b[1;36m[Interactive shell opened. Type commands below.]\x1b[0m\n"
        )

        while not self._stop_event.is_set() and not self.channel.closed:
            # Read available stdout from the channel
            if self.channel.recv_ready():
                try:
                    data = self.channel.recv(4096).decode("utf-8", errors="replace")
                    self.output_received.emit(data)
                except Exception as e:
                    logger.warning("Error reading channel: %s", e)
                    break

            # Read available stderr from the channel
            if self.channel.recv_stderr_ready():
                try:
                    data = self.channel.recv_stderr(4096).decode("utf-8", errors="replace")
                    self.output_received.emit(f"\x1b[33m[stderr]\x1b[0m {data}")
                except Exception:
                    break

            # Process next queued action
            action = None
            with self._queue_lock:
                if self._queue:
                    action = self._queue.pop(0)

            if action:
                if action["type"] == self._CMD:
                    cmd = action["data"]
                    self.channel.send(cmd + "\n")

                elif action["type"] == self._EXEC:
                    self._upload_and_execute(action["content"], action["remote_path"])

            self.msleep(50)

        if not self.channel.closed:
            self.channel.close()

    # ── SFTP upload helper ────────────────────────────────────────────────────

    def _upload_and_execute(self, script_content: str, remote_path: str):
        """Upload script via SFTP and execute it in the interactive shell."""
        script_name = remote_path.split("/")[-1]

        self.output_received.emit(
            f"\x1b[1;34m[Uploading {script_name} via SFTP...]\x1b[0m\n"
        )
        try:
            sftp = self.client.open_sftp()
            try:
                # Write script as UTF-8 bytes on the remote server
                with sftp.open(remote_path, "w") as remote_file:
                    remote_file.write(script_content.encode("utf-8"))
            finally:
                sftp.close()

            self.output_received.emit(
                f"\x1b[1;32m[Upload complete. Executing {script_name}...]\x1b[0m\n"
            )
            # Make executable and run; output will appear naturally in the shell stream
            self.channel.send(f"chmod +x {remote_path} && bash {remote_path}\n")

        except Exception as e:
            logger.exception("SFTP upload failed: %s", e)
            self.output_received.emit(
                f"\x1b[1;31m[Upload failed: {e}]\x1b[0m\n"
            )

    # ── Cleanup ───────────────────────────────────────────────────────────────

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
