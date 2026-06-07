"""Repositorio local para persistencia del Módulo 2.

Almacena el historial de operaciones y servicios de scraping
localmente en SQLite.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from modulo_2_admin.core.models import ServiceDefinition


class LocalRepository:
    """Repositorio SQLite local para el historial de operaciones y servicios."""

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
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS services (
                service_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                config_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS service_runs (
                run_id TEXT PRIMARY KEY,
                service_id TEXT NOT NULL,
                operation_id TEXT NOT NULL,
                filter_values TEXT,
                total_found INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL,
                FOREIGN KEY (service_id) REFERENCES services(service_id)
            )
        """)
        self._conn.commit()

    # ─── Operaciones (existente) ─────────────────────────────

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

    # ─── Servicios (nuevo) ───────────────────────────────────

    def save_service(self, service: ServiceDefinition) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO services "
            "(service_id, name, description, config_json, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                service.service_id,
                service.name,
                service.description,
                json.dumps(service.to_dict()),
                service.created_at,
                service.updated_at,
            ),
        )
        self._conn.commit()

    def get_services(self) -> list[dict[str, Any]]:
        cursor = self._conn.execute(
            "SELECT service_id, name, description, config_json, "
            "created_at, updated_at FROM services "
            "ORDER BY updated_at DESC"
        )
        result = []
        for row in cursor.fetchall():
            config = json.loads(row[3]) if row[3] else {}
            sources = config.get("sources", [])
            result.append({
                "service_id": row[0],
                "name": row[1],
                "description": row[2],
                "source": sources[0]["url"] if sources else config.get("source", ""),
                "sources_count": len(sources),
                "sources": [s["url"] for s in sources],
                "field_count": len(config.get("fields", [])),
                "filter_count": len(config.get("field_filters", [])),
                "created_at": row[4],
                "updated_at": row[5],
            })
        return result

    def get_service(self, service_id: str) -> ServiceDefinition | None:
        cursor = self._conn.execute(
            "SELECT config_json FROM services WHERE service_id = ?",
            (service_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        data = json.loads(row[0])
        return ServiceDefinition.from_dict(data)

    def delete_service(self, service_id: str) -> None:
        self._conn.execute(
            "DELETE FROM service_runs WHERE service_id = ?",
            (service_id,),
        )
        self._conn.execute(
            "DELETE FROM services WHERE service_id = ?",
            (service_id,),
        )
        self._conn.commit()

    # ─── Service runs ────────────────────────────────────────

    def save_service_run(
        self,
        run_id: str,
        service_id: str,
        operation_id: str,
        filter_values: dict[str, Any] | None = None,
        total_found: int = 0,
        status: str = "running",
    ) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO service_runs "
            "(run_id, service_id, operation_id, filter_values, total_found, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                run_id,
                service_id,
                operation_id,
                json.dumps(filter_values) if filter_values else "{}",
                total_found,
                status,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self._conn.commit()

    def get_service_runs(self, service_id: str) -> list[dict[str, Any]]:
        cursor = self._conn.execute(
            "SELECT run_id, operation_id, filter_values, total_found, "
            "status, created_at FROM service_runs "
            "WHERE service_id = ? ORDER BY created_at DESC LIMIT 20",
            (service_id,),
        )
        return [
            {
                "run_id": row[0],
                "operation_id": row[1],
                "filter_values": json.loads(row[2]) if row[2] else {},
                "total_found": row[3],
                "status": row[4],
                "created_at": row[5],
            }
            for row in cursor.fetchall()
        ]

    def close(self) -> None:
        self._conn.close()
