"""Tool: solicita comprar lo que la bodega central no alcanza a cubrir."""
from langchain_core.tools import tool

from agent.db import conectar


@tool
def solicitar_compra(ciclo: str, items: list[dict], fecha: str) -> dict:
    """Crea solicitudes de compra pendientes para el área de compras.

    Cada item lleva codigo, cantidad y razon. No compra nada: deja la solicitud
    pendiente hasta que una persona confirme la recepción.
    Devuelve {'registradas': int, 'unidades': int}.
    """
    conn = conectar()
    for item in items:
        conn.execute(
            "INSERT INTO solicitudes (ciclo, tipo, local, codigo, cantidad, estado, razon, fecha) "
            "VALUES (?, 'compra', 0, ?, ?, 'pendiente_compra', ?, ?)",
            (ciclo, item["codigo"], item["cantidad"], item["razon"], fecha),
        )
    conn.commit()
    conn.close()
    return {"registradas": len(items), "unidades": sum(i["cantidad"] for i in items)}
