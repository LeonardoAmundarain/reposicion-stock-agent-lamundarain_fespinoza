"""Tool: consulta las ventas de un local."""
from langchain_core.tools import tool

from agent.db import conectar
from agent.inventario import periodo_ventas, ventas_por_producto
from config import settings


@tool
def consultar_ventas(local: int, codigo: str = "", limite: int = 5) -> dict:
    """Consulta las ventas de un local (14, 15 o 16) por producto.

    Con codigo devuelve las ventas de ese producto. Sin codigo devuelve los más vendidos.
    Las unidades ya descuentan devoluciones; venta_diaria excluye ventas mayoristas.
    """
    if local not in settings.LOCALES:
        return {"error": f"Local {local} no existe. Usa 14, 15 o 16"}
    conn = conectar()
    ventas = ventas_por_producto(conn, local)
    corte, dias = periodo_ventas(conn)
    nombres = {f["codigo"]: f["producto"]
               for f in conn.execute("SELECT codigo, producto FROM productos")}
    conn.close()
    filas = [{"codigo": c, "producto": nombres.get(c, c), **v} for c, v in ventas.items()]
    if codigo.strip():
        filas = [f for f in filas if f["codigo"].upper() == codigo.strip().upper()]
    filas.sort(key=lambda f: f["venta_diaria"], reverse=True)
    return {
        "local": local,
        "hasta": corte.isoformat(),
        "dias_periodo": dias,
        "unidades_totales": sum(v["unidades"] for v in ventas.values()),
        "productos_con_venta": len(ventas),
        "productos": filas[:limite],
    }
