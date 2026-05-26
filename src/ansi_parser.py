"""ANSI escape sequence parser for the VPS Manager terminal console.

Converts raw terminal output (including ANSI CSI and OSC sequences) into
richly formatted text inserted into a QTextEdit widget.

Supported:
  - SGR (Select Graphic Rendition): colors, bold, italic, underline, reset
  - ED (Erase Display): clears the QTextEdit on \\033[2J / \\033[3J
  - Bracketed paste mode and other private mode sequences: stripped silently
  - OSC sequences (window title changes, etc.): stripped silently
  - Carriage-return handling: move cursor to line start
"""

import re

from PySide6.QtGui import QColor, QFont, QTextCharFormat

# ── ANSI color palettes ───────────────────────────────────────────────────────
# Modern, dark-terminal-friendly color mapping

_ANSI_COLORS_NORMAL = {
    30: "#4a4a5a",   # Black  -> dark gray (visible on dark bg)
    31: "#ff5f57",   # Red    -> vivid coral
    32: "#28c840",   # Green  -> bright green
    33: "#febc2e",   # Yellow -> amber
    34: "#1e90ff",   # Blue   -> dodger blue
    35: "#bf5af2",   # Magenta -> purple
    36: "#5ac8fa",   # Cyan   -> sky blue
    37: "#e0e0e0",   # White  -> light gray
}

_ANSI_COLORS_BRIGHT = {
    90: "#767690",   # Bright Black (dark gray)
    91: "#ff6e6e",   # Bright Red
    92: "#5af78e",   # Bright Green
    93: "#f4f99d",   # Bright Yellow
    94: "#57c7ff",   # Bright Blue
    95: "#ff6ac1",   # Bright Magenta
    96: "#9aedfe",   # Bright Cyan
    97: "#ffffff",   # Bright White
}

# Background colors (40-47, 100-107) — we map them but keep subtle on dark bg
_ANSI_BG_COLORS_NORMAL = {
    40: "#1a1a2e",
    41: "#3d0c0c",
    42: "#0c3d1a",
    43: "#3d350c",
    44: "#0c1a3d",
    45: "#2d0c3d",
    46: "#0c2d3d",
    47: "#2a2a3a",
}

_ANSI_BG_COLORS_BRIGHT = {
    100: "#3a3a4a",
    101: "#6d2020",
    102: "#206d35",
    103: "#6d5c20",
    104: "#203a6d",
    105: "#4d1f6d",
    106: "#1f4d6d",
    107: "#5a5a6a",
}

# Regex to find the next ANSI escape sequence
_ESC_RE = re.compile(
    r"\x1b(?:"
    r"(?P<csi>\[[\x30-\x3f]*[\x20-\x2f]*[\x40-\x7e])"  # CSI sequence
    r"|(?P<osc>\][^\x07\x1b]*(?:\x07|\x1b\\))"           # OSC sequence
    r"|(?P<other>[^\\[])"                                  # Other 2-char esc
    r")"
)


class AnsiConsoleParser:
    """Stateful ANSI parser that writes to a QTextEdit.

    Usage::

        parser = AnsiConsoleParser(text_edit_widget)
        parser.feed(raw_ssh_data)
    """

    def __init__(self, text_edit):
        self._widget = text_edit
        self._fmt = QTextCharFormat()
        self._reset_format()
        self._buf = ""  # incomplete escape sequence buffer

    def _reset_format(self):
        """Reset to default terminal colors."""
        self._fmt = QTextCharFormat()
        self._fmt.setForeground(QColor("#e0e0e0"))
        self._fmt.setBackground(QColor("#0d1117"))
        self._fmt.setFontWeight(QFont.Weight.Normal)
        self._fmt.setFontItalic(False)
        self._fmt.setFontUnderline(False)

    def feed(self, data: str):
        """Process a chunk of raw terminal data and write to the text edit."""
        # Prepend any leftover partial escape from last call
        data = self._buf + data
        self._buf = ""

        cursor = self._widget.textCursor()

        pos = 0
        while pos < len(data):
            esc_pos = data.find("\x1b", pos)

            if esc_pos == -1:
                # No more escape sequences — write the rest as plain text
                self._write_plain(cursor, data[pos:])
                pos = len(data)
                continue

            # Write any text before the escape
            if esc_pos > pos:
                self._write_plain(cursor, data[pos:esc_pos])

            # Check if we have a complete escape sequence
            m = _ESC_RE.match(data, esc_pos)
            if m is None:
                # Possibly incomplete — buffer and wait for next chunk
                self._buf = data[esc_pos:]
                break

            if m.group("csi"):
                self._handle_csi(cursor, m.group("csi"))
            # osc and other sequences are silently ignored

            pos = m.end()

        # Scroll to bottom
        sb = self._widget.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ── Private helpers ───────────────────────────────────────────────────────

    def _write_plain(self, cursor, text: str):
        """Write plain text, handling \\r and \\n properly."""
        if not text:
            return

        # Handle carriage returns: \r goes to start of line; \r\n is newline
        # Process character by character for correctness
        parts = re.split(r"(\r\n|\r|\n)", text)
        for part in parts:
            if part in ("\r\n", "\n"):
                cursor.movePosition(cursor.MoveOperation.End)
                cursor.insertText("\n", self._fmt)
            elif part == "\r":
                # Move to start of current line — overwrite (like a terminal)
                cursor.movePosition(cursor.MoveOperation.StartOfLine)
            else:
                cursor.insertText(part, self._fmt)

        self._widget.setTextCursor(cursor)

    def _handle_csi(self, cursor, seq: str):
        """Dispatch CSI escape sequences."""
        cmd = seq[-1]     # final byte identifies the command
        params = seq[1:-1]  # everything between '[' and the command

        # Private mode (starts with ?)  — strip silently (bracketed paste, etc.)
        if params.startswith("?"):
            return

        if cmd == "m":
            # SGR — Set Graphic Rendition
            self._handle_sgr(params)
        elif cmd in ("J", "K"):
            # Erase in Display / Line
            self._handle_erase(cursor, cmd, params)
        elif cmd in ("H", "f"):
            # Cursor Position — for a text widget we just ignore positioning
            pass
        elif cmd in ("A", "B", "C", "D", "E", "F", "G"):
            # Cursor movement — ignore in a log-style text widget
            pass
        # All other CSI sequences are silently ignored

    def _handle_sgr(self, params: str):
        """Handle SGR (color/style) sequences."""
        if not params:
            codes = [0]
        else:
            try:
                codes = [int(p) for p in params.split(";")]
            except ValueError:
                return

        i = 0
        while i < len(codes):
            code = codes[i]

            if code == 0:
                self._reset_format()
            elif code == 1:
                self._fmt.setFontWeight(QFont.Weight.Bold)
            elif code == 2:
                self._fmt.setFontWeight(QFont.Weight.Light)
            elif code == 3:
                self._fmt.setFontItalic(True)
            elif code == 4:
                self._fmt.setFontUnderline(True)
            elif code == 22:
                self._fmt.setFontWeight(QFont.Weight.Normal)
            elif code == 23:
                self._fmt.setFontItalic(False)
            elif code == 24:
                self._fmt.setFontUnderline(False)
            elif code == 39:
                self._fmt.setForeground(QColor("#e0e0e0"))
            elif code == 49:
                self._fmt.setBackground(QColor("#0d1117"))
            elif code in _ANSI_COLORS_NORMAL:
                self._fmt.setForeground(QColor(_ANSI_COLORS_NORMAL[code]))
            elif code in _ANSI_COLORS_BRIGHT:
                self._fmt.setForeground(QColor(_ANSI_COLORS_BRIGHT[code]))
            elif code in _ANSI_BG_COLORS_NORMAL:
                self._fmt.setBackground(QColor(_ANSI_BG_COLORS_NORMAL[code]))
            elif code in _ANSI_BG_COLORS_BRIGHT:
                self._fmt.setBackground(QColor(_ANSI_BG_COLORS_BRIGHT[code]))
            elif code == 38:
                # Extended foreground color: 38;5;n or 38;2;r;g;b
                if i + 2 < len(codes) and codes[i + 1] == 5:
                    color = self._xterm256(codes[i + 2])
                    self._fmt.setForeground(color)
                    i += 2
                elif i + 4 < len(codes) and codes[i + 1] == 2:
                    r, g, b = codes[i + 2], codes[i + 3], codes[i + 4]
                    self._fmt.setForeground(QColor(r, g, b))
                    i += 4
            elif code == 48:
                # Extended background color: 48;5;n or 48;2;r;g;b
                if i + 2 < len(codes) and codes[i + 1] == 5:
                    color = self._xterm256(codes[i + 2])
                    self._fmt.setBackground(color)
                    i += 2
                elif i + 4 < len(codes) and codes[i + 1] == 2:
                    r, g, b = codes[i + 2], codes[i + 3], codes[i + 4]
                    self._fmt.setBackground(QColor(r, g, b))
                    i += 4

            i += 1

    def _handle_erase(self, cursor, cmd: str, params: str):
        """Handle ED (erase display) and EL (erase line)."""
        n = int(params) if params.isdigit() else 0
        if cmd == "J" and n in (2, 3):
            # Clear entire display
            self._widget.clear()
        elif cmd == "K" and n == 2:
            # Clear entire line — select from line start to end and delete
            cursor.movePosition(cursor.MoveOperation.StartOfLine)
            cursor.movePosition(
                cursor.MoveOperation.EndOfLine,
                cursor.MoveMode.KeepAnchor,
            )
            cursor.removeSelectedText()

    @staticmethod
    def _xterm256(n: int) -> QColor:
        """Convert xterm 256-color index to QColor."""
        if n < 16:
            # Standard colors (reuse our palette where possible)
            standard = list(_ANSI_COLORS_NORMAL.values()) + list(_ANSI_COLORS_BRIGHT.values())
            if n < len(standard):
                return QColor(standard[n])
            return QColor("#e0e0e0")
        elif n < 232:
            # 6x6x6 color cube
            n -= 16
            b = n % 6
            g = (n // 6) % 6
            r = n // 36

            def to_byte(v: int) -> int:
                return 0 if v == 0 else 55 + v * 40

            return QColor(to_byte(r), to_byte(g), to_byte(b))
        else:
            # Grayscale ramp
            gray = 8 + (n - 232) * 10
            return QColor(gray, gray, gray)
