import os

import pyodbc
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    server = os.getenv('DB_SERVER', 'localhost')
    database = os.getenv('DB_DATABASE', 'MarketInsight')
    driver = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
    username = os.getenv('DB_USERNAME')
    password = os.getenv('DB_PASSWORD')

    if username and password:
        conn_str = (
            f'DRIVER={{{driver}}};SERVER={server};DATABASE={database};'
            f'UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes;'
        )
    else:
        conn_str = (
            f'DRIVER={{{driver}}};SERVER={server};DATABASE={database};'
            'Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;'
        )

    return pyodbc.connect(conn_str)


def read_valid_offers(limit: int | None = None):
    query = 'SELECT * FROM dbo.v_OffresValidees'
    if limit is not None:
        query = query + f' ORDER BY id_offre OFFSET 0 ROWS FETCH NEXT {int(limit)} ROWS ONLY'

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(query).fetchall()
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
    except Exception:
        return []
