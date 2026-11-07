"""Tool: envía una notificación simulada al responsable."""
from langchain_core.tools import tool


@tool
def notificar_responsable(destino: str, mensaje: str) -> dict:
    """Registra una notificación simulada para la tienda, bodega o compras.

    Devuelve {'ok': bool, 'canal': str}.
    """
    # En un caso real, aquí se conectaría un correo o un sistema de mensajería.
    print(f"[NOTIF] -> {destino}: {mensaje}")
    return {"ok": True, "canal": "mock", "destino": destino}
