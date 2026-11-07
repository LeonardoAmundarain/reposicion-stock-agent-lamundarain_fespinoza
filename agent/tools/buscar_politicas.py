"""Tool: recupera políticas y casos anteriores por significado (RAG)."""
from langchain_core.tools import tool

from agent.memory.semantic import buscar


@tool
def buscar_politicas(texto: str) -> list[dict]:
    """Busca por significado políticas de reposición y casos anteriores similares.

    Devuelve fragmentos con tipo ('politica' o 'caso'), texto y fuente.
    """
    return (
        [{"tipo": "politica", **d} for d in buscar("politicas", texto, k=2)]
        + [{"tipo": "caso", **d} for d in buscar("casos_previos", texto, k=2)]
    )
