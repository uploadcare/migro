"""

    migro.db.db_manager
    ~~~~~~~~~~~~~~~~~~~

    Database manager.

"""

import sqlite3
from sqlite3 import Error, Connection
from pathlib import Path
import click
from typing import Optional, Tuple


class DBManager:
    def __init__(self):
        """
        Initialize the DBManager with the database file.
        """
        self.db_file: Path = Path(__file__).resolve().parent / "migration.db"
        self.conn: Connection = self.create_connection()
        if self.conn is not None:
            self.create_tables()
        else:
            raise Error("Failed to connect to the database.")

    def create_connection(self) -> Connection:
        """
        Create a database connection to the SQLite database specified by db_file.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_file, check_same_thread=False)
            click.secho(f"Connected to the database: {self.db_file}", fg='green')
            click.secho(f"SQLite version: {sqlite3.version}", fg='green')
        except Error as e:
            click.secho(f"Failed to connect to the database: {self.db_file}", fg='red')
            click.secho(f"Error: {e}", fg='red')
        return conn

    def execute_sql(self, sql_script: str) -> None:
        """
        Execute an SQL script.
        """
        try:
            c = self.conn.cursor()
            c.executescript(sql_script) if ';' in sql_script else c.execute(sql_script)
            self.conn.commit()
        except Error as e:
            click.secho(f"Failed to execute SQL script:", fg='red')
            click.secho(f"Error: {e}", fg='red')

    def create_tables(self) -> None:
        """
        Create `attempts` and `files` tables if they don't exist already.
        """
        sql_create_attempts_table = """
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            files_count INTEGER NOT NULL,
            successful_uploads INTEGER NULL,
            failed_uploads INTEGER NULL,
            started_at DATETIME,
            finished_at DATETIME NULL,
            error BOOLEAN DEFAULT 0
        );
        """
        sql_create_files_table = """
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL,
            source TEXT NOT NULL,
            file_size INTEGER,
            uploadcare_uuid TEXT,
            status TEXT NOT NULL,
            error TEXT,
            last_attempt_id INTEGER,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(last_attempt_id) REFERENCES attempts(id)
        );
        """
        self.execute_sql(sql_create_attempts_table)
        self.execute_sql(sql_create_files_table)

    def clear_database(self) -> None:
        """
        Clear the database.
        """
        sql_clear_files_table = """
        DELETE FROM files;
        DELETE FROM attempts;
        """
        self.execute_sql(sql_clear_files_table)
        self.conn.commit()
        # VACUUM the database to free up space
        try:
            self.conn.execute('VACUUM;')
            self.conn.commit()
        except Error as e:
            click.secho(f"Error: {e}", fg='red')

    def file_exists(self, source: str, path: str) -> bool:
        """
        Check if a file key already exists in the database.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM files WHERE path = ? AND source = ?", (path, source))
        return cursor.fetchone() is not None

    def insert_file(self, path: str, source: str, file_size: Optional[int] = None) -> None:
        """
        Insert a new file record into the database if it
        doesn't already exist, including the file size.
        """
        if not self.file_exists(source, path):
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO files (path, source, file_size, status) VALUES (?, ?, ?, 'pending')",
                           (path, source, file_size))
            self.conn.commit()

    def start_attempt(self, source: str, files_count: int) -> int:
        """
        Start a new attempt and return its ID.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO attempts (source, files_count, started_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (source, files_count)
        )
        self.conn.commit()
        return cursor.lastrowid

    def finish_attempt(self, attempt_id: int) -> tuple:
        """
        Retrieve attempt details including file list, and count of 'uploaded' and 'error' statuses.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT path, file_size, uploadcare_uuid, status, error FROM files WHERE last_attempt_id = ?",
                       (attempt_id,))
        file_list = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM files WHERE last_attempt_id = ? AND status = 'uploaded'", (attempt_id,))
        count_uploaded = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM files WHERE last_attempt_id = ? AND status = 'error'", (attempt_id,))
        count_error = cursor.fetchone()[0]

        cursor.execute(
            "UPDATE attempts SET finished_at = CURRENT_TIMESTAMP, successful_uploads = ?, failed_uploads = ? "
            "WHERE id = ?",
            (count_uploaded, count_error, attempt_id))

        return file_list, attempt_id, count_uploaded, count_error

    def set_attempt_for_files(self, attempt_id: int, ignore_errors: bool = False) -> None:
        """
        Set the last attempt ID for all files.
        """
        attempt: Tuple = self.get_attempt_by_id(attempt_id)
        if attempt is not None:
            cursor = self.conn.cursor()
            if ignore_errors:
                cursor.execute("SELECT id FROM files WHERE status = 'pending' AND source = ?",
                               (attempt[1],))
            else:
                cursor.execute("SELECT id FROM files WHERE status IN ('pending', 'error') AND source = ?",
                               (attempt[1],))
            files = cursor.fetchall()
            for file in files:
                cursor.execute("UPDATE files SET last_attempt_id = ? WHERE id = ?", (attempt_id, file[0]))
            self.conn.commit()

    def get_not_uploaded_files_size(self) -> int:
        """
        Get the total size of files that are not uploaded yet.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT SUM(file_size) FROM files WHERE status != 'uploaded'")
        return cursor.fetchone()[0]

    def get_not_uploaded_files_info(self) -> tuple:
        """
        Get the total size and the number of files that are not uploaded yet.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*), SUM(file_size) FROM files WHERE status != 'uploaded'")
        result = cursor.fetchone()
        number_of_files = result[0] if result[0] is not None else 0
        total_size = result[1] if result[1] is not None else 0
        return number_of_files, total_size

    def get_pending_files(self, source, include_errors: bool = True) -> list[str]:
        """
        Get the list of pending files.
        """
        cursor = self.conn.cursor()
        query = "SELECT path FROM files WHERE status = 'pending' AND source = ?"
        if include_errors:
            query = "SELECT path FROM files WHERE status IN ('pending', 'error') AND source = ?"

        cursor.execute(query, (source,))
        return [row[0] for row in cursor.fetchall()]

    def set_file_uploaded(self, path: str, source: str, attempt: int, uploadcare_uuid: str) -> None:
        """
        Set the status of a file to uploaded and save the uploadcare UUID.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE files 
            SET status = 'uploaded', 
            error = NULL, 
            uploadcare_uuid = ?, 
            last_attempt_id = ?
            WHERE path = ? 
            AND source = ?
            """,
            (uploadcare_uuid, attempt, path, source)
        )
        self.conn.commit()

    def set_file_error(self, path: str, source: str, error: str) -> None:
        """
        Set the status of a file to error and save the error message.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE files SET status = 'error', error = ? WHERE path = ? AND source = ?",
            (error, path, source)
        )
        self.conn.commit()

    def get_attempt_by_id(self, attempt_id: int) -> Tuple:
        """
        Get an attempt by ID.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM attempts WHERE id = ?", (attempt_id,))
        return cursor.fetchone()

    def close_connection(self) -> None:
        """
        Close the database connection.
        """
        if self.conn:
            self.conn.close()
