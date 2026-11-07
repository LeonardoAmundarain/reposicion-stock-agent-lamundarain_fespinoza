"""Carga ventas y stock en SQLite. Borra las solicitudes y ciclos anteriores."""
import sqlite3

import pandas as pd

from agent.datos import agrupar_ventas, cruzar_con_stock, leer_stock, leer_ventas, limpiar_ventas
from config import settings

ESQUEMA = """
DROP TABLE IF EXISTS productos;
DROP TABLE IF EXISTS stock;
DROP TABLE IF EXISTS stock_inicial;
DROP TABLE IF EXISTS ventas;
DROP TABLE IF EXISTS sin_cruce;
DROP TABLE IF EXISTS solicitudes;
DROP TABLE IF EXISTS ciclos;
CREATE TABLE productos (
    codigo TEXT PRIMARY KEY, ean TEXT, producto TEXT, marca TEXT,
    subfamilia TEXT, nicho TEXT
);
CREATE TABLE stock (
    codigo TEXT PRIMARY KEY, b14 INTEGER, b15 INTEGER, b16 INTEGER, total INTEGER
);
CREATE TABLE ventas (
    local INTEGER, fecha TEXT, codigo TEXT, mayorista INTEGER,
    unidades INTEGER, monto REAL, costo REAL
);
CREATE INDEX idx_ventas ON ventas (local, codigo);
CREATE TABLE sin_cruce (local INTEGER, codigo TEXT, descripcion TEXT, unidades INTEGER);
CREATE TABLE solicitudes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ciclo TEXT, tipo TEXT, local INTEGER, codigo TEXT, cantidad INTEGER,
    estado TEXT, razon TEXT, fecha TEXT
);
CREATE TABLE ciclos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ciclo TEXT, local INTEGER, fecha TEXT, con_pedido INTEGER, resumen TEXT
);
"""


class ArchivoOcupado(Exception):
    """Un archivo de datos no se puede leer, normalmente porque está abierto en Excel."""


def sembrar() -> dict:
    """Recrea la base desde los archivos y devuelve un resumen de la limpieza."""
    try:
        stock = leer_stock(settings.RUTA_STOCK)
        limpias, resumen = limpiar_ventas(leer_ventas(settings.RUTA_VENTAS))
    except PermissionError as error:
        raise ArchivoOcupado(
            f"No se pudo leer {error.filename}. Cierra el archivo en Excel e inténtalo de nuevo."
        ) from error
    cruzadas, sin_cruce = cruzar_con_stock(limpias, stock)

    settings.DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(settings.DB_PATH)
    conn.executescript(ESQUEMA)
    stock[["codigo", "ean", "producto", "marca", "subfamilia", "nicho"]].to_sql(
        "productos", conn, if_exists="append", index=False)
    stock[["codigo", "b14", "b15", "b16", "total"]].to_sql(
        "stock", conn, if_exists="append", index=False)
    # Copia del stock original: permite reiniciar la demo sin volver a leer los archivos.
    conn.execute("CREATE TABLE stock_inicial AS SELECT * FROM stock")
    agrupar_ventas(cruzadas).to_sql("ventas", conn, if_exists="append", index=False)
    pendientes = (
        sin_cruce.groupby(["local", "codigo", "DESCRIPCION"], as_index=False)["unidades"].sum()
        .rename(columns={"DESCRIPCION": "descripcion"})
    )
    pd.DataFrame(pendientes).to_sql("sin_cruce", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()
    resumen.update(productos_sin_cruce=len(pendientes),
                   unidades_sin_cruce=int(pendientes["unidades"].sum()))
    return resumen


def reiniciar_demo() -> None:
    """Borra las solicitudes de prueba y restaura el stock inicial. No lee los archivos."""
    conn = sqlite3.connect(settings.DB_PATH)
    tiene_copia = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'stock_inicial'"
    ).fetchone()
    if not tiene_copia:
        conn.close()
        sembrar()
        return
    conn.executescript("""
        DELETE FROM solicitudes;
        DELETE FROM ciclos;
        DELETE FROM stock;
        INSERT INTO stock SELECT * FROM stock_inicial;
    """)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    try:
        print(sembrar())
    except ArchivoOcupado as error:
        raise SystemExit(str(error)) from error
    print(f"SQLite listo en {settings.DB_PATH}")
