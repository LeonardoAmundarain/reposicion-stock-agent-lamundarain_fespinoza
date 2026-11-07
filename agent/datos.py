"""Lee y limpia los archivos de ventas y stock antes de cargarlos en SQLite."""
import numpy as np
import pandas as pd

from config import settings


def _codigo_texto(valor) -> str | None:
    """Deja un código como texto: 6291106480771.0 pasa a '6291106480771'."""
    if pd.isna(valor):
        return None
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    texto = str(valor).strip()
    return texto or None


def leer_stock(ruta) -> pd.DataFrame:
    """Lee el stock. La columna STOCK es el total, incluidas las bodegas 14, 15 y 16."""
    df = pd.read_excel(ruta)
    return pd.DataFrame({
        "codigo": df["CODIGO"].map(_codigo_texto),
        "ean": df["CODIGO BARRA"].map(_codigo_texto),
        "producto": df["PRODUCTO"].astype(str).str.strip(),
        "marca": df["CATEGORIA"].astype(str).str.strip(),
        "subfamilia": df["SUBFAMILIA"].fillna("Sin subfamilia"),
        "nicho": df["NICHO"].fillna("SIN NICHO"),
        "b14": df["B14"].astype(int),
        "b15": df["B15"].astype(int),
        "b16": df["B16"].astype(int),
        "total": df["STOCK"].astype(int),
    }).dropna(subset=["codigo"]).drop_duplicates("codigo")


def leer_ventas(ruta) -> pd.DataFrame:
    """Une las hojas 'CAJA n' del archivo de ventas en una sola tabla."""
    hojas = pd.read_excel(ruta, sheet_name=None)
    tablas = [h for nombre, h in hojas.items() if str(nombre).upper().startswith("CAJA")]
    columnas = ["MODULO", "FECHA", "CAJA", "CODIGO", "COD ALT", "DESCRIPCION",
                "CANT", "COSTO", "VENTA"]
    return pd.concat([t[columnas] for t in tablas], ignore_index=True)


def limpiar_ventas(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Deja solo la venta útil para estimar la demanda y resume lo que se quitó."""
    resumen = {"lineas_originales": len(df)}
    es_cotizacion = df["MODULO"].astype(str).str.upper().eq("COTIZACION")
    es_prueba = df["DESCRIPCION"].astype(str).str.upper().str.startswith("PRUEBA")
    es_antigua = pd.to_datetime(df["FECHA"]) < pd.Timestamp(settings.INICIO_VENTAS)
    sin_valor = df["VENTA"].eq(0)
    resumen.update(
        cotizaciones=int(es_cotizacion.sum()),
        pruebas=int(es_prueba.sum()),
        fuera_de_periodo=int(es_antigua.sum()),
        venta_cero=int(sin_valor.sum()),
    )
    limpio = df[~(es_cotizacion | es_prueba | es_antigua | sin_valor)].copy()

    limpio["fecha"] = pd.to_datetime(limpio["FECHA"]).dt.strftime("%Y-%m-%d")
    limpio["local"] = limpio["CAJA"].map(settings.CAJA_A_LOCAL)
    limpio = limpio.dropna(subset=["local"])
    limpio["local"] = limpio["local"].astype(int)
    # Venta negativa con cantidad positiva = devolución de un cliente: se resta.
    limpio["unidades"] = limpio["CANT"] * np.sign(limpio["VENTA"]).astype(int)
    limpio["mayorista"] = limpio["CANT"].ge(settings.UMBRAL_MAYORISTA).astype(int)
    limpio["codigo"] = limpio["CODIGO"].map(_codigo_texto)
    limpio["ean"] = limpio["COD ALT"].map(_codigo_texto)
    resumen.update(
        devoluciones_clientes=int((limpio["VENTA"] < 0).sum()),
        lineas_mayoristas=int(limpio["mayorista"].sum()),
        lineas_utiles=len(limpio),
    )
    return limpio, resumen


def cruzar_con_stock(ventas: pd.DataFrame, stock: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Une ventas y stock por código y, si no calza, por EAN.

    Devuelve las ventas con su código de stock y las líneas que no se pudieron cruzar.
    """
    codigos = set(stock["codigo"])
    por_ean = stock.dropna(subset=["ean"]).drop_duplicates("ean").set_index("ean")["codigo"]
    ventas = ventas.copy()
    encontrado = ventas["codigo"].where(ventas["codigo"].isin(codigos))
    ventas["codigo_stock"] = encontrado.fillna(ventas["ean"].map(por_ean))
    sin_cruce = ventas[ventas["codigo_stock"].isna()]
    return ventas.dropna(subset=["codigo_stock"]), sin_cruce


def agrupar_ventas(ventas: pd.DataFrame) -> pd.DataFrame:
    """Resume por local, día y producto: es lo único que necesita el agente."""
    return (
        ventas.groupby(["local", "fecha", "codigo_stock", "mayorista"], as_index=False)
        .agg(unidades=("unidades", "sum"), monto=("VENTA", "sum"), costo=("COSTO", "sum"))
        .rename(columns={"codigo_stock": "codigo"})
    )
