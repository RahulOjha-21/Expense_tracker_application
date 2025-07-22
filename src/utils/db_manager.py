import sqlite3
from utils.logger import setup_logger
from datetime import datetime

logger = setup_logger()

CREATE_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS ImageData (
    id TEXT PRIMARY KEY,
    amount TEXT,
    date DATETIME,
    original_path TEXT,
    rename_name TEXT,
    category TEXT DEFAULT '',
    tags TEXT DEFAULT ''
)
"""

DELETE_ALL_QUERY = "DELETE FROM ImageData"
INSERT_DATA_QUERY = """
INSERT INTO ImageData (id, amount, date, original_path, rename_name, category, tags)
VALUES (?, ?, ?, ?, ?, ?, ?)
"""
SELECT_ALL_QUERY = "SELECT * FROM ImageData ORDER BY id"


class DatabaseManager:
    """A context manager for handling SQLite database connections."""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def __enter__(self):
        """Opens the database connection and returns the cursor."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            logger.debug(f"Database connection opened to {self.db_path}")
            return self.cursor
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database {self.db_path}: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Commits changes and closes the database connection."""
        if self.conn:
            if exc_type:
                logger.warning("Rolling back transaction due to an exception.")
                self.conn.rollback()
            else:
                logger.debug("Committing transaction.")
                self.conn.commit()
            self.conn.close()
            logger.debug("Database connection closed.")

def save_to_sqlite_db(unique_id: str, amount: str, date: datetime, original_path: str, rename_name: str, db_path: str, category: str = '', tags: str = '') -> None:
    """
    Saves data to the SQLite database.
    """
    try:
        with DatabaseManager(db_path) as cursor:
            cursor.execute(CREATE_TABLE_QUERY)
            cursor.execute(INSERT_DATA_QUERY, (
                unique_id,
                amount,
                date.strftime('%Y-%m-%d'),  # Convert datetime object to string
                original_path,
                rename_name,
                category,
                tags
            ))
            logger.info("Data inserted into SQLite database successfully.")
    except sqlite3.IntegrityError:
        logger.info(f"Data with ID {unique_id} already exists. Skipping insertion.")
    except Exception as e:
        logger.error(f"Error in save_to_sqlite_db function during execution: {str(e)}")

def clear_db_data(db_path: str) -> None:
    """
    Clears all existing data from the SQLite database.
    """
    try:
        with DatabaseManager(db_path) as cursor:
            cursor.execute(DELETE_ALL_QUERY)
            logger.info("All existing data cleared from SQLite database.")
    except Exception as e:
        logger.error(f"Error in clear_db_data function during execution: {str(e)}")

def browse_db_data(db_path: str) -> None:
    """
    Fetches and logs all data from the SQLite database.
    """
    try:
        with DatabaseManager(db_path) as cursor:
            cursor.execute(SELECT_ALL_QUERY)
            rows = cursor.fetchall()
            for row in rows:
                logger.info(f"DB Record: {row}")
    except Exception as e:
        logger.error(f"Error in browse_db_data function during execution: {str(e)}") 