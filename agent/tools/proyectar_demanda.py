"""Tool: proyecta la demanda considerando la temporada alta. Solo calcula."""
from datetime import timedelta

from langchain_core.tools import tool

from agent import demanda
from agent.db import conectar
from agent.inventario import ventas_por_producto
from config import settings


@tool
def proyectar_demanda(local: int, codigo: str = "", fecha: str = "") -> dict:
    """Proyecta la venta de un local (14, 15 o 16) desde una fecha AAAA-MM-DD.

    Con codigo proyecta ese producto; sin codigo, todo el local. Devuelve el factor de
    temporada, la venta del próximo período de reposición y la venta hasta fin de diciembre.
    """
    if local not in settings.LOCALES:
        return {"error": f"Local {local} no existe. Usa 14, 15 o 16"}
    dia = settings.fecha_plan(fecha or None)
    conn = conectar()
    ventas = ventas_por_producto(conn, local)
    conn.close()
    if codigo.strip():
        ventas = {c: v for c, v in ventas.items() if c.upper() == codigo.strip().upper()}
    diaria = sum(v["venta_diaria"] for v in ventas.values() if v["activo"])
    if settings.LOCALES[local]["tipo"] == "online":
        hasta = demanda.fin_de_quincena(dia)
        dias = (hasta - dia).days + 1
    else:
        dias = settings.DIAS_COBERTURA_TIENDA + settings.DIAS_REPOSICION
        hasta = dia + timedelta(days=dias - 1)
    return {
        "local": local,
        "codigo": codigo,
        "fecha": dia.isoformat(),
        "factor_temporada": demanda.factor_temporada(dia),
        "venta_diaria_normal": round(diaria, 2),
        "periodo_hasta": hasta.isoformat(),
        "venta_periodo": round(diaria * demanda.dias_equivalentes(dia, dias), 1),
        "venta_hasta_fin_de_diciembre": round(demanda.proyeccion_hasta_fin(diaria, dia), 1),
    }
