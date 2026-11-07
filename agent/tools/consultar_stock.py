"""Tool: consulta el stock de un producto o el resumen de la bodega de un local."""
from langchain_core.tools import tool

from agent.inventario import buscar_productos, resumen_stock_local


@tool
def consultar_stock(consulta: str = "", local: int = 0) -> dict:
    """Consulta stock por código, EAN o nombre del producto.

    Con consulta devuelve las bodegas 14, 15, 16 y la central de cada coincidencia.
    Sin consulta y con local (14, 15 o 16) devuelve el resumen de esa bodega.
    """
    if consulta.strip():
        productos = buscar_productos(consulta)
        if not productos:
            return {"error": f"No se encontró el producto '{consulta}'"}
        return {"productos": productos}
    if local:
        return resumen_stock_local(local)
    return {"error": "Indica un producto o un local"}
