from __future__ import annotations

import logging
import pymysql
from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
import app.models  # noqa: F401  # ensure model metadata is registered


logger = logging.getLogger("axiomflow.db.bootstrap")


def ensure_database_exists() -> None:
    """
    Ensure the target MySQL database exists.

    - If the DSN points to a missing database, create it automatically.
    - Does NOT require the database to exist to connect (connects to server without db).
    """
    settings = get_settings()
    url = make_url(settings.MYSQL_DSN)

    db_name = url.database
    if not db_name:
        return

    # Use raw PyMySQL connection without selecting DB, so missing DB won't break startup.
    conn = pymysql.connect(
        host=url.host or "127.0.0.1",
        port=int(url.port or 3306),
        user=url.username,
        password=url.password,
        charset="utf8mb4",
        autocommit=True,
    )
    try:
        safe_name = db_name.replace("`", "``")
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{safe_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
            )
    finally:
        conn.close()


def ensure_username_unique_index() -> None:
    """
    Best-effort migration: add unique index on users.username if missing.
    Fails gracefully when duplicates exist or permissions are insufficient.
    """
    try:
        insp = inspect(engine)
        if not insp.has_table("users"):
            return
        for idx in insp.get_indexes("users"):
            if idx.get("unique") and tuple(idx.get("column_names") or ()) == ("username",):
                return
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD UNIQUE INDEX uq_users_username (username)"))
        logger.info("Added unique index uq_users_username on users.username")
    except Exception:
        logger.warning(
            "Could not ensure unique index on users.username "
            "(remove duplicate usernames manually or run ALTER TABLE).",
            exc_info=True,
        )


def ensure_users_avatar_column() -> None:
    """
    Best-effort migration: ensure users.avatar_url exists and can store long data URIs.
    """
    try:
        insp = inspect(engine)
        if not insp.has_table("users"):
            return
        columns = {c.get("name"): c for c in insp.get_columns("users")}
        with engine.begin() as conn:
            if "avatar_url" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url TEXT NULL"))
                logger.info("Added users.avatar_url column as TEXT")
                return
            # Widen existing column for legacy deployments using VARCHAR(1024).
            col_type = str(columns["avatar_url"].get("type") or "").lower()
            if "text" not in col_type:
                conn.execute(text("ALTER TABLE users MODIFY COLUMN avatar_url TEXT NULL"))
                logger.info("Altered users.avatar_url column to TEXT")
    except Exception:
        logger.warning("Could not ensure users.avatar_url column/type", exc_info=True)


def ensure_users_oauth_verified_column() -> None:
    """
    Best-effort migration: add users.is_oauth_verified if missing.
    """
    try:
        insp = inspect(engine)
        if not insp.has_table("users"):
            return
        cols = {c.get("name") for c in insp.get_columns("users")}
        if "is_oauth_verified" in cols:
            return
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_oauth_verified TINYINT(1) NOT NULL DEFAULT 0"))
        logger.info("Added users.is_oauth_verified column")
    except Exception:
        logger.warning("Could not ensure users.is_oauth_verified column", exc_info=True)


def ensure_database_ready() -> None:
    try:
        ensure_database_exists()
    except Exception:
        logger.exception("ensure_database_exists_failed")
        raise

    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        logger.exception("create_tables_failed")
        raise

    ensure_username_unique_index()
    ensure_users_avatar_column()
    ensure_users_oauth_verified_column()

