"""Database manager using SQLite for server and script storage."""
import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database for VPS server and script records."""

    def __init__(self, db_path: str | Path | None = None):
        # Resolve DB path relative to this file's directory
        if db_path is None:
            db_path = Path(__file__).resolve().parent.parent / "vps_manager.db"
        self.db_path = Path(db_path)
        self.init_database()

    def init_database(self):
        """Initialize tables if they don't exist."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                ip TEXT NOT NULL,
                username TEXT NOT NULL,
                pem_path TEXT NOT NULL,
                port INTEGER DEFAULT 22,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id INTEGER,
                name TEXT NOT NULL,
                script_path TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY (server_id) REFERENCES servers (id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        conn.close()

    # ── Server CRUD ──────────────────────────────────────────────

    def add_server(self, name: str, ip: str, username: str,
                   pem_path: str, port: int = 22, description: str = "") -> int:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO servers (name, ip, username, pem_path, port, description) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (name, ip, username, pem_path, port, description),
        )
        server_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return server_id

    def get_servers(self) -> list[tuple]:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, ip, username, pem_path, port, description "
            "FROM servers ORDER BY created_at DESC"
        )
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_server(self, server_id: int) -> tuple | None:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, ip, username, pem_path, port, description "
            "FROM servers WHERE id = ?", (server_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return row

    def update_server(self, server_id: int, **kwargs):
        allowed = {"name", "ip", "username", "pem_path", "port", "description"}
        sets = {k: v for k, v in kwargs.items() if k in allowed}
        if not sets:
            return
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        clauses = ", ".join(f"{k} = ?" for k in sets)
        values = list(sets.values()) + [server_id]
        cursor.execute(f"UPDATE servers SET {clauses} WHERE id = ?", values)
        conn.commit()
        conn.close()

    def delete_server(self, server_id: int):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM servers WHERE id = ?", (server_id,))
        conn.commit()
        conn.close()

    # ── Script CRUD ──────────────────────────────────────────────

    def add_script(self, server_id: int, name: str,
                   script_path: str, description: str = ""):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO scripts (server_id, name, script_path, description) "
            "VALUES (?, ?, ?, ?)",
            (server_id, name, script_path, description),
        )
        conn.commit()
        conn.close()

    def get_scripts_for_server(self, server_id: int) -> list[tuple]:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, script_path, description "
            "FROM scripts WHERE server_id = ? ORDER BY name", (server_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return rows

    def delete_script(self, script_id: int):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scripts WHERE id = ?", (script_id,))
        conn.commit()
        conn.close()
