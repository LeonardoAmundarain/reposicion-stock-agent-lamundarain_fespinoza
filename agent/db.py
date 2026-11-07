"""Conexión a SQLite usada por las tools y la memoria."""
import sqlite3

from config import settings


def conectar() -> sqlite3.Connection:
    """Abre la base de datos; las filas se pueden leer por nombre de columna."""
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
