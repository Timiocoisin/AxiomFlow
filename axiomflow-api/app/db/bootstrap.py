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
                conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url MEDIUMTEXT NULL"))
                logger.info("Added users.avatar_url column as MEDIUMTEXT")
                return
            # Widen existing column for legacy deployments using VARCHAR/TEXT.
            col_type = str(columns["avatar_url"].get("type") or "").lower()
            if "mediumtext" not in col_type:
                conn.execute(text("ALTER TABLE users MODIFY COLUMN avatar_url MEDIUMTEXT NULL"))
                logger.info("Altered users.avatar_url column to MEDIUMTEXT")
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


def ensure_users_usage_columns() -> None:
    """
    Best-effort migration: add usage/stat columns on users if missing.
    """
    try:
        insp = inspect(engine)
        if not insp.has_table("users"):
            return
        cols = {c.get("name") for c in insp.get_columns("users")}
        with engine.begin() as conn:
            if "translated_documents" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN translated_documents INT NOT NULL DEFAULT 0"))
                logger.info("Added users.translated_documents column")
            if "translated_words" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN translated_words INT NOT NULL DEFAULT 0"))
                logger.info("Added users.translated_words column")
            if "credits_balance" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN credits_balance INT NOT NULL DEFAULT 0"))
                logger.info("Added users.credits_balance column")
    except Exception:
        logger.warning("Could not ensure users usage columns", exc_info=True)


def ensure_users_notification_columns() -> None:
    """
    Best-effort migration: add notification preference columns on users if missing.
    """
    try:
        insp = inspect(engine)
        if not insp.has_table("users"):
            return
        cols = {c.get("name") for c in insp.get_columns("users")}
        with engine.begin() as conn:
            if "notify_email" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN notify_email TINYINT(1) NOT NULL DEFAULT 1"))
                logger.info("Added users.notify_email column")
            if "notify_browser" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN notify_browser TINYINT(1) NOT NULL DEFAULT 0"))
                logger.info("Added users.notify_browser column")
            if "notify_marketing" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN notify_marketing TINYINT(1) NOT NULL DEFAULT 0"))
                logger.info("Added users.notify_marketing column")
    except Exception:
        logger.warning("Could not ensure users notification columns", exc_info=True)


def ensure_users_preference_columns() -> None:
    """
    Best-effort migration: add preference columns on users if missing.
    """
    try:
        insp = inspect(engine)
        if not insp.has_table("users"):
            return
        cols = {c.get("name") for c in insp.get_columns("users")}
        with engine.begin() as conn:
            if "preferred_target_language" not in cols:
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN preferred_target_language VARCHAR(32) NOT NULL DEFAULT 'zh-CN'")
                )
                logger.info("Added users.preferred_target_language column")
            if "ui_language" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN ui_language VARCHAR(16) NOT NULL DEFAULT 'zh-CN'"))
                logger.info("Added users.ui_language column")
            if "auto_save_history" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN auto_save_history TINYINT(1) NOT NULL DEFAULT 1"))
                logger.info("Added users.auto_save_history column")
            if "enable_shortcuts" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN enable_shortcuts TINYINT(1) NOT NULL DEFAULT 1"))
                logger.info("Added users.enable_shortcuts column")
            if "upload_size_limit_mb" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN upload_size_limit_mb INT NOT NULL DEFAULT 20"))
                logger.info("Added users.upload_size_limit_mb column")
            if "auto_import_provider" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN auto_import_provider VARCHAR(32) NOT NULL DEFAULT 'none'"))
                logger.info("Added users.auto_import_provider column")
            if "default_output_format" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN default_output_format VARCHAR(16) NOT NULL DEFAULT 'pdf'"))
                logger.info("Added users.default_output_format column")
            if "data_retention_days" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN data_retention_days INT NOT NULL DEFAULT 7"))
                logger.info("Added users.data_retention_days column")
    except Exception:
        logger.warning("Could not ensure users preference columns", exc_info=True)


def ensure_user_documents_columns() -> None:
    """
    Best-effort migration: ensure user_documents storage columns exist.
    """
    try:
        insp = inspect(engine)
        if not insp.has_table("user_documents"):
            return
        cols = {c.get("name") for c in insp.get_columns("user_documents")}
        with engine.begin() as conn:
            if "mime_type" not in cols:
                conn.execute(
                    text(
                        "ALTER TABLE user_documents "
                        "ADD COLUMN mime_type VARCHAR(128) NOT NULL DEFAULT 'application/octet-stream'"
                    )
                )
            if "original_storage_path" not in cols:
                conn.execute(
                    text(
                        "ALTER TABLE user_documents "
                        "ADD COLUMN original_storage_path VARCHAR(1024) NOT NULL DEFAULT ''"
                    )
                )
            if "translated_storage_path" not in cols:
                conn.execute(
                    text(
                        "ALTER TABLE user_documents "
                        "ADD COLUMN translated_storage_path VARCHAR(1024) NULL"
                    )
                )
    except Exception:
        logger.warning("Could not ensure user_documents storage columns", exc_info=True)


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
    ensure_users_usage_columns()
    ensure_users_notification_columns()
    ensure_users_preference_columns()
    ensure_user_documents_columns()

