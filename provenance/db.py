from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional


@dataclass
class BatchOp:
    batch_id: str
    description: str
    config_json: dict
    expected_units: dict


@dataclass
class ArtifactRecord:
    batch_id: str
    file_path: str
    input_hash: str
    output_hash: str
    status: str


class ProvenanceDB:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS batch_ops (
                    batch_id TEXT PRIMARY KEY,
                    description TEXT,
                    config_json TEXT,
                    expected_units TEXT,
                    timestamp DATETIME
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS artifacts (
                    id INTEGER PRIMARY KEY,
                    batch_id TEXT,
                    file_path TEXT,
                    input_hash CHAR(64),
                    output_hash CHAR(64),
                    status TEXT,
                    FOREIGN KEY(batch_id) REFERENCES batch_ops(batch_id)
                );
                """
            )

    def log_batch(self, batch: BatchOp, timestamp: Optional[datetime] = None) -> None:
        timestamp = timestamp or datetime.utcnow()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO batch_ops (batch_id, description, config_json, expected_units, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    batch.batch_id,
                    batch.description,
                    json.dumps(batch.config_json),
                    json.dumps(batch.expected_units),
                    timestamp.isoformat(),
                ),
            )

    def log_artifacts(self, artifacts: Iterable[ArtifactRecord]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                """
                INSERT INTO artifacts (batch_id, file_path, input_hash, output_hash, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        artifact.batch_id,
                        artifact.file_path,
                        artifact.input_hash,
                        artifact.output_hash,
                        artifact.status,
                    )
                    for artifact in artifacts
                ],
            )
