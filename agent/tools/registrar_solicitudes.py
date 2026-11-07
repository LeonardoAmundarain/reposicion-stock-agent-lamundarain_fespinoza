"""Tool: registra reposiciones y devoluciones hacia o desde la bodega central."""
from langchain_core.tools import tool

from agent.db import conectar
from agent.inventario import central_disponible


@tool
def registrar_solicitudes(ciclo: str, local: int, tipo: str, items: list[dict],
                          fecha: str) -> dict:
    """Registra solicitudes tipo 'reposicion' o 'devolucion' de un local.

    Cada item lleva codigo, cantidad y razon. Vuelve a revisar la central justo antes
    de guardar: si cambió, registra lo que alcanza e informa el ajuste.
    Devuelve {'registradas': int, 'unidades': int, 'ajustes': list[dict]}.
    """
    if tipo not in ("reposicion", "devolucion"):
        return {"error": f"Tipo no válido: {tipo}"}
    conn = conectar()
    registradas, unidades, ajustes = 0, 0, []
    for item in items:
        cantidad = item["cantidad"]
        if tipo == "reposicion":
            disponible = central_disponible(conn, item["codigo"])
            if disponible < cantidad:
                ajustes.append({"codigo": item["codigo"], "pedido": cantidad,
                                "aprobado": disponible})
                cantidad = disponible
        if cantidad <= 0:
            continue
        conn.execute(
            "INSERT INTO solicitudes (ciclo, tipo, local, codigo, cantidad, estado, razon, fecha) "
            "VALUES (?, ?, ?, ?, ?, 'en_transito', ?, ?)",
            (ciclo, tipo, local, item["codigo"], cantidad, item["razon"], fecha),
        )
        registradas += 1
        unidades += cantidad
    conn.commit()
    conn.close()
    return {"registradas": registradas, "unidades": unidades, "ajustes": ajustes}
