import sqlite3

def fetch_data_from_db(db_path, table_name):
    """
    Fetch all data from the specified table in the given SQLite .db file.

    Args:
        db_path (str): Path to the .db file.
        table_name (str): Name of the table to fetch data from.

    Returns:
        list of tuple: All rows from the table.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        return rows
    finally:
        conn.close()

# Example usage:
db_file = "outputs/DB/image_data.db"
table = "ImageData"
data = fetch_data_from_db(db_file, table)
print(data)
