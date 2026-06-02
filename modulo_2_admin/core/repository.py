"""Repositorio local para persistencia del Módulo 2.

Almacena el historial de operaciones localmente en SQLite
para que el usuario pueda verlo incluso sin conexión al servicio.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class LocalRepository:
    """Repositorio SQLite local para el historial de operaciones."""

    def __init__(self, db_path: str | None = None) -> None:
        if db_path is None:
            db_path = str(Path.home() / ".scrapper_generico" / "admin.db")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._migrate()

    def _migrate(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                operation_id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                config_json TEXT NOT NULL,
                total_found INTEGER DEFAULT 0,
                errors INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL,
                results_json TEXT
            )
        """)
        self._conn.commit()

    def save_operation(
        self,
        operation_id: str,
        source: str,
        config: dict[str, Any],
    ) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO history "
            "(operation_id, source, config_json, status, created_at) "
            "VALUES (?, ?, ?, 'running', ?)",
            (
                operation_id,
                source,
                json.dumps(config),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self._conn.commit()

    def update_results(
        self,
        operation_id: str,
        total_found: int,
        errors_count: int,
        results: dict[str, Any] | None = None,
    ) -> None:
        self._conn.execute(
            "UPDATE history SET total_found=?, errors=?, "
            "status=?, results_json=? WHERE operation_id=?",
            (
                total_found,
                errors_count,
                "completed" if errors_count == 0 else "completed_with_errors",
                json.dumps(results) if results else None,
                operation_id,
            ),
        )
        self._conn.commit()

    def get_history(
        self, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        cursor = self._conn.execute(
            "SELECT operation_id, source, total_found, errors, "
            "status, created_at FROM history "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        return [
            {
                "operation_id": row[0],
                "source": row[1],
                "total_found": row[2],
                "errors": row[3],
                "status": row[4],
                "created_at": row[5],
            }
            for row in cursor.fetchall()
        ]

    def get_operation(self, operation_id: str) -> dict[str, Any] | None:
        cursor = self._conn.execute(
            "SELECT * FROM history WHERE operation_id = ?",
            (operation_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {
            "operation_id": row[0],
            "source": row[1],
            "config": json.loads(row[2]) if row[2] else {},
            "total_found": row[3],
            "errors": row[4],
            "status": row[5],
            "created_at": row[6],
            "results": json.loads(row[7]) if row[7] else None,
        }

    def close(self) -> None:
        self._conn.close()
