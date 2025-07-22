# filepath: d:\01_Rahul_Personal\Python_projects\03_Expense_Tracker_app\src\core\database.py
from utils.logger import setup_logger
import sqlite3
from datetime import datetime
from typing import Optional, Dict
import json
import logging
import sys
import os

logger = logging.getLogger(__name__)

# Load configuration settings
def load_config(file_path: str) -> dict:
    with open(file_path, 'r') as file:
        config = json.load(file)
    return config

def resource_path(relative_path: str) -> str:
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

config_path = resource_path('config/settings.json')
config = load_config(config_path)
logger = setup_logger()

DB_PATH = config['database']['path']
CREATE_TABLE_QUERY = config['database']['queries']['create_table']
DELETE_ALL_QUERY = config['database']['queries']['delete_all']
INSERT_DATA_QUERY = config['database']['queries']['insert_data']
SELECT_ALL_QUERY = config['database']['queries']['select_all']

def save_to_sqlite_db(unique_id: str, amount: str, date: datetime, original_path: str, rename_name: str, db_path: str) -> None:
    """
    Saves data to the SQLite database.

    Args:
        unique_id (str): Unique identifier for the record.
        amount (str): Amount extracted from the image.
        date (datetime): Date extracted from the image.
        original_path (str): Original file path of the image.
        rename_name (str): Renamed file name.
        db_path (str): Path to the SQLite database.
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(CREATE_TABLE_QUERY)
            cursor.execute(INSERT_DATA_QUERY, (unique_id, amount, date, original_path, rename_name))
            logger.info("Data inserted into SQLite database successfully.")
    except sqlite3.IntegrityError:
        logger.info(f"Data with ID {unique_id} already exists. Skipping insertion.")
    except Exception as e:
        logger.error(f"Error in save_to_sqlite_db function during execution: {str(e)}")

def clear_db_data(db_path: str) -> None:
    """
    Clears all existing data from the SQLite database.

    Args:
        db_path (str): Path to the SQLite database.
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(DELETE_ALL_QUERY)
            logger.info("All existing data cleared from SQLite database.")
    except Exception as e:
        logger.error(f"Error in clear_db_data function during execution: {str(e)}")

def browse_db_data(db_path: str) -> None:
    """
    Fetches and logs all data from the SQLite database.

    Args:
        db_path (str): Path to the SQLite database.
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(SELECT_ALL_QUERY)
            rows = cursor.fetchall()
            for row in rows:
                logger.info(f"DB Record: {row}")
    except Exception as e:
        logger.error(f"Error in browse_db_data function during execution: {str(e)}")