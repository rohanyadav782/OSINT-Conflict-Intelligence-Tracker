"""SQLite database layer — schema creation, CRUD operations."""
from __future__ import annotations

import sqlite3
import json
from pathlib import Path
from typing import Optional
from config import DB_PATH


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Get a SQLite connection with row factory."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: Path = DB_PATH):
    """Create all tables and indexes."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS events (
            event_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            event_datetime_utc TEXT NOT NULL,
            source_name       TEXT NOT NULL,
            source_url        TEXT NOT NULL UNIQUE,
            source_type       TEXT NOT NULL,
            claim_text        TEXT NOT NULL,
            country           TEXT,
            location_text     TEXT,
            latitude          REAL,
            longitude         REAL,
            actor_1           TEXT,
            actor_2           TEXT,
            event_type        TEXT DEFAULT 'unknown',
            domain            TEXT DEFAULT 'unknown',
            severity_score    REAL DEFAULT 5.0 CHECK(severity_score BETWEEN 0 AND 10),
            confidence_score  REAL DEFAULT 0.5 CHECK(confidence_score BETWEEN 0 AND 1),
            verification_status TEXT DEFAULT 'unverified',
            tags              TEXT DEFAULT '[]',
            conflict_flag     INTEGER DEFAULT 0,
            raw_text          TEXT,
            cameo_code        TEXT,
            fatalities        INTEGER,
            last_updated_at   TEXT NOT NULL,
            created_at        TEXT NOT NULL DEFAULT (datetime('now')),
            dedup_cluster_id  INTEGER
        );

        CREATE TABLE IF NOT EXISTS event_sources (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id          INTEGER NOT NULL REFERENCES events(event_id),
            source_name       TEXT NOT NULL,
            source_url        TEXT NOT NULL,
            source_type       TEXT NOT NULL,
            claim_text        TEXT,
            retrieved_at      TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS source_reliability (
            source_name       TEXT PRIMARY KEY,
            total_reports     INTEGER DEFAULT 0,
            confirmed_reports INTEGER DEFAULT 0,
            reliability_score REAL DEFAULT 0.5,
            last_evaluated    TEXT
        );

        CREATE TABLE IF NOT EXISTS escalation_index (
            date_utc          TEXT PRIMARY KEY,
            event_count       INTEGER,
            avg_severity      REAL,
            max_severity      REAL,
            escalation_score  REAL,
            dominant_domain   TEXT,
            anomaly_flag      INTEGER DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS idx_events_datetime ON events(event_datetime_utc);
        CREATE INDEX IF NOT EXISTS idx_events_country ON events(country);
        CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type);
        CREATE INDEX IF NOT EXISTS idx_events_actor1 ON events(actor_1);
        CREATE INDEX IF NOT EXISTS idx_events_severity ON events(severity_score);
        CREATE INDEX IF NOT EXISTS idx_events_cluster ON events(dedup_cluster_id);
    """)

    conn.commit()
    conn.close()


def insert_event(event_dict: dict, db_path: Path = DB_PATH) -> Optional[int]:
    """Insert a single event. Returns event_id or None if duplicate URL."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute("""
            INSERT INTO events (
                event_datetime_utc, source_name, source_url, source_type,
                claim_text, country, location_text, latitude, longitude,
                actor_1, actor_2, event_type, domain, severity_score,
                confidence_score, verification_status, tags, conflict_flag,
                raw_text, cameo_code, fatalities, last_updated_at, dedup_cluster_id
            ) VALUES (
                :event_datetime_utc, :source_name, :source_url, :source_type,
                :claim_text, :country, :location_text, :latitude, :longitude,
                :actor_1, :actor_2, :event_type, :domain, :severity_score,
                :confidence_score, :verification_status, :tags, :conflict_flag,
                :raw_text, :cameo_code, :fatalities, :last_updated_at, :dedup_cluster_id
            )
        """, event_dict)
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        # Duplicate source_url
        return None
    finally:
        conn.close()


def insert_event_source(source_dict: dict, db_path: Path = DB_PATH):
    """Insert a corroborating source for an event."""
    conn = get_connection(db_path)
    conn.execute("""
        INSERT INTO event_sources (event_id, source_name, source_url, source_type, claim_text, retrieved_at)
        VALUES (:event_id, :source_name, :source_url, :source_type, :claim_text, :retrieved_at)
    """, source_dict)
    conn.commit()
    conn.close()


def url_exists(url: str, db_path: Path = DB_PATH) -> bool:
    """Check if a URL already exists in the events table."""
    conn = get_connection(db_path)
    row = conn.execute("SELECT 1 FROM events WHERE source_url = ?", (url,)).fetchone()
    conn.close()
    return row is not None


def get_recent_events(hours: int = 48, db_path: Path = DB_PATH) -> list[dict]:
    """Get events from the last N hours for dedup comparison."""
    conn = get_connection(db_path)
    rows = conn.execute("""
        SELECT * FROM events
        WHERE event_datetime_utc >= datetime('now', ? || ' hours')
        ORDER BY event_datetime_utc DESC
    """, (f"-{hours}",)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_events(db_path: Path = DB_PATH) -> list[dict]:
    """Get all events ordered by datetime."""
    conn = get_connection(db_path)
    rows = conn.execute(
        "SELECT * FROM events ORDER BY event_datetime_utc DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_events_dataframe(db_path: Path = DB_PATH):
    """Get all events as a pandas DataFrame."""
    import pandas as pd
    conn = get_connection(db_path)
    df = pd.read_sql_query(
        "SELECT * FROM events ORDER BY event_datetime_utc DESC", conn
    )
    conn.close()
    return df


def get_escalation_index(db_path: Path = DB_PATH):
    """Get escalation index as pandas DataFrame."""
    import pandas as pd
    conn = get_connection(db_path)
    df = pd.read_sql_query(
        "SELECT * FROM escalation_index ORDER BY date_utc", conn
    )
    conn.close()
    return df


def upsert_escalation(record: dict, db_path: Path = DB_PATH):
    """Insert or update daily escalation index."""
    conn = get_connection(db_path)
    conn.execute("""
        INSERT INTO escalation_index (date_utc, event_count, avg_severity, max_severity,
                                       escalation_score, dominant_domain, anomaly_flag)
        VALUES (:date_utc, :event_count, :avg_severity, :max_severity,
                :escalation_score, :dominant_domain, :anomaly_flag)
        ON CONFLICT(date_utc) DO UPDATE SET
            event_count = :event_count,
            avg_severity = :avg_severity,
            max_severity = :max_severity,
            escalation_score = :escalation_score,
            dominant_domain = :dominant_domain,
            anomaly_flag = :anomaly_flag
    """, record)
    conn.commit()
    conn.close()


def update_event(event_id: int, updates: dict, db_path: Path = DB_PATH):
    """Update specific fields of an event."""
    conn = get_connection(db_path)
    set_clause = ", ".join(f"{k} = :{k}" for k in updates)
    updates["event_id"] = event_id
    conn.execute(f"UPDATE events SET {set_clause} WHERE event_id = :event_id", updates)
    conn.commit()
    conn.close()


def get_source_reliability(db_path: Path = DB_PATH) -> list[dict]:
    """Get source reliability scores."""
    conn = get_connection(db_path)
    rows = conn.execute(
        "SELECT * FROM source_reliability ORDER BY reliability_score DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_event_sources(event_id: int, db_path: Path = DB_PATH) -> list[dict]:
    """Get all corroborating sources for an event."""
    conn = get_connection(db_path)
    rows = conn.execute(
        "SELECT * FROM event_sources WHERE event_id = ?", (event_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_next_cluster_id(db_path: Path = DB_PATH) -> int:
    """Get the next available cluster ID."""
    conn = get_connection(db_path)
    row = conn.execute(
        "SELECT COALESCE(MAX(dedup_cluster_id), 0) + 1 as next_id FROM events"
    ).fetchone()
    conn.close()
    return row["next_id"]
