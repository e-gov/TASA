"""TASA DB Logic"""

import os
from typing import Callable, List, Tuple
import sqlite3


def initialize_db_connection(db: str) -> Tuple[sqlite3.Connection, sqlite3.Cursor, str]:
    """
    Initializes the SQLite database connection and returns the connection,
    cursor, and the table name.

    Args:
        db (str): The database file path.

    Returns:
        Tuple[sqlite3.Connection, sqlite3.Cursor, str]: A tuple containing the database
        connection, cursor, and table name.
    """
    conn = sqlite3.connect(db, detect_types=sqlite3.PARSE_DECLTYPES)
    cursor = conn.cursor()
    table_name = db.replace(".db", "")
    return conn, cursor, table_name


def db_exists(db: str, callback: Callable[[str], None] = print) -> bool:
    """
    Checks whether the database file exists.

    Args:
        db (str): The name of the database file (without '.db' extension).
        callback (Callable[[str], None]): A callback function for logging errors.

    Returns:
        bool: True if the database file exists, False otherwise.
    """
    if os.path.exists(f"{db}.db"):
        return True
    callback("Project doesn't exist!")
    return False


def create_db(db: str, callback: Callable[[str], None] = print) -> None:
    """
    Creates the database and tables required for the application.

    Args:
        db (str): The name of the database file.
        callback (Callable): A function for logging messages, default is `print`.
    """
    conn, cursor, table_name = initialize_db_connection(db)

    try:
        create_base_tables(cursor)
        create_initial_table(cursor, table_name)
        create_env_tables(cursor, table_name)
        conn.commit()
        callback(f"Database and tables created successfully in: {db}")
    except sqlite3.Error as error:
        callback(f"Error creating database tables: {error}")
    finally:
        cursor.close()
        conn.close()


def create_base_tables(cursor: sqlite3.Cursor) -> None:
    """
    Creates the base tables like 'last_run'.

    Args:
        cursor (sqlite3.Cursor): The SQLite database cursor.
    """
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS last_run (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_sync_timestamp TEXT,
            status TEXT
        )
        """
    )

    cursor.execute(
        """
        INSERT INTO last_run (last_sync_timestamp, status)
        VALUES (datetime('now'), 'initial')
        """
    )


def create_initial_table(cursor: sqlite3.Cursor, table_name: str) -> None:
    """
    Creates the initial table for the project.

    Args:
        cursor (sqlite3.Cursor): The SQLite database cursor.
        table_name (str): The base name of the table.
    """
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name}_initial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            locale TEXT,
            title TEXT,
            tags TEXT,
            path TEXT,
            content TEXT
        )
        """
    )


def create_env_tables(cursor: sqlite3.Cursor, table_name: str) -> None:
    """
    Creates the environment-specific tables and triggers.

    Args:
        cursor (sqlite3.Cursor): The SQLite database cursor.
        table_name (str): The base name of the table.
    """
    envs = ["_dev", "_test", "_prod"]
    for env in envs:
        env_table_name = f"{table_name}{env}"
        create_main_env_table(cursor, env_table_name)
        create_update_trigger(cursor, env_table_name)
        create_related_tables(cursor, env_table_name)


def create_main_env_table(cursor: sqlite3.Cursor, table_name: str) -> None:
    """
    Creates the main environment-specific table.

    Args:
        cursor (sqlite3.Cursor): The SQLite database cursor.
        table_name (str): The environment-specific table name.
    """
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            exp_article_id INTEGER,
            article_id INTEGER PRIMARY KEY,
            locale TEXT,
            title TEXT,
            tags TEXT,
            path TEXT,
            content TEXT,
            status TEXT,
            modified_timestamp TEXT
        )
        """
    )


def create_update_trigger(cursor: sqlite3.Cursor, table_name: str) -> None:
    """
    Creates a trigger to update the modified timestamp on the environment table.

    Args:
        cursor (sqlite3.Cursor): The SQLite database cursor.
        table_name (str): The environment-specific table name.
    """
    cursor.execute(
        f"""
        CREATE TRIGGER IF NOT EXISTS update_modified_timestamp_{table_name}
        AFTER UPDATE ON {table_name}
        BEGIN
            UPDATE {table_name}
            SET modified_timestamp = datetime('now')
            WHERE article_id = NEW.article_id;
        END
        """
    )


def create_related_tables(cursor: sqlite3.Cursor, table_name: str) -> None:
    """
    Creates the related tables for the environment.

    Args:
        cursor (sqlite3.Cursor): The SQLite database cursor.
        table_name (str): The environment-specific table name.
    """
    related_tables = {
        "arva_institution": f"""
            id INTEGER,
            pageId INTEGER,
            name TEXT,
            url TEXT,
            isResponsible BOOLEAN,
            FOREIGN KEY(pageId) REFERENCES {table_name}(article_id) ON DELETE CASCADE
        """,
        "arva_legal_act": f"""
            id INTEGER,
            pageId INTEGER,
            title TEXT,
            url TEXT,
            legalActType TEXT,
            globalId REAL,
            groupId INTEGER,
            versionStartDate TEXT,
            FOREIGN KEY(pageId) REFERENCES {table_name}(article_id) ON DELETE CASCADE
        """,
        "arva_page_contact": f"""
            id INTEGER,
            contactId INTEGER,
            pageId INTEGER,
            role TEXT,
            firstName TEXT,
            lastName TEXT,
            company TEXT,
            email TEXT,
            countryCode TEXT,
            nationalNumber TEXT,
            FOREIGN KEY(pageId) REFERENCES {table_name}(article_id) ON DELETE CASCADE
        """,
        "arva_related_pages": f"""
            id INTEGER,
            pageId INTEGER,
            title TEXT,
            locale TEXT,
            FOREIGN KEY(pageId) REFERENCES {table_name}(article_id) ON DELETE CASCADE
        """,
        "arva_service": f"""
            id INTEGER,
            pageId INTEGER,
            name TEXT,
            url TEXT,
            FOREIGN KEY(pageId) REFERENCES {table_name}(article_id) ON DELETE CASCADE
        """,
    }

    for table_suffix, schema in related_tables.items():
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table_name}_{table_suffix} (
                {schema}
            )
            """
        )


def copy_table(
    db: str, source_env: str, target_env: str, callback: Callable[[str], None] = print
) -> None:
    """
    Copies data from a source table to a target table in the same SQLite database,
    including associated related tables.

    Args:
        db (str): The name of the database file.
        source_env (str): The source environment identifier (e.g., 'dev').
        target_env (str): The target environment identifier (e.g., 'prod').
        callback (Callable): A function for error or status messages, default is `print`.
    """
    conn, cursor, table_name = initialize_db_connection(db)

    try:
        # Copy main table data
        _copy_main_table(cursor, table_name, source_env, target_env)

        # Copy related tables
        related_tables = [
            "arva_institution",
            "arva_legal_act",
            "arva_page_contact",
            "arva_related_pages",
            "arva_service",
        ]
        _copy_related_tables(cursor, table_name, source_env, target_env, related_tables)

        # Commit changes
        conn.commit()
        callback("Data copied successfully.")
    except sqlite3.Error as error:
        callback(f"An error occurred: {error}")


def _copy_main_table(
    cursor: sqlite3.Cursor, table_name: str, source_env: str, target_env: str
) -> None:
    """
    Copies data from the main source table to the target table.

    Args:
        cursor: SQLite database cursor.
        table_name (str): Base table name.
        source_env (str): Source environment identifier.
        target_env (str): Target environment identifier.
    """
    source_table = f"{table_name}_{source_env}"
    target_table = f"{table_name}_{target_env}"

    cursor.execute(
        f"""
        INSERT INTO {target_table} (article_id, locale, title, tags, path, content)
        SELECT article_id, locale, title, tags, path, content
        FROM {source_table}
        """
    )


def _copy_related_tables(
    cursor: sqlite3.Cursor,
    table_name: str,
    source_env: str,
    target_env: str,
    related_tables: List[str],
) -> None:
    """
    Copies data from related source tables to the target tables.

    Args:
        cursor: SQLite database cursor.
        table_name (str): Base table name.
        source_env (str): Source environment identifier.
        target_env (str): Target environment identifier.
        related_tables (list): List of related table names to copy.
    """
    for related_table in related_tables:
        source_related_table = f"{table_name}_{source_env}_{related_table}"
        target_related_table = f"{table_name}_{target_env}_{related_table}"

        # Dynamically fetch column names starting from the 3rd column
        columns = cursor.execute(
            f"PRAGMA table_info({source_related_table})"
        ).fetchall()[2:]
        column_names = ", ".join(column[1] for column in columns)

        cursor.execute(
            f"""
            INSERT INTO {target_related_table} (id, pageId, {column_names})
            SELECT id, pageId, {column_names}
            FROM {source_related_table}
            """
        )
