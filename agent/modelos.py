"""Modelos que se pueden elegir en el panel y orden de respaldo de Gemini."""
from config import settings


def listar_modelos(proveedor: str) -> list[str]:
    """Modelos que ofrece el panel para cada proveedor."""
    if proveedor == "claude":
        return list(settings.CLAUDE_MODELOS)
    return list(settings.GEMINI_MODELOS)


def modelos_a_intentar(proveedor: str, elegido: str | None = None) -> list[str]:
    """Claude es de pago: solo el elegido. Gemini es gratis: si uno falla, prueba el siguiente."""
    if proveedor == "claude":
        return [elegido or settings.CLAUDE_MODEL]
    inicio = elegido or settings.LLM_MODEL
    cadena = [inicio] + [m for m in settings.GEMINI_MODELOS if m != inicio]
    return cadena[:settings.MAX_INTENTOS_GEMINI]
