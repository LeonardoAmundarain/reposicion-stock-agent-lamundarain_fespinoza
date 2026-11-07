"""Memoria semántica: políticas y casos en Chroma, recuperados por significado."""
import uuid
from functools import lru_cache

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from config import settings

FUENTE_AGENTE = "decision_agente"


@lru_cache(maxsize=1)
def obtener_embeddings() -> HuggingFaceEmbeddings:
    """Carga el modelo una sola vez: es la operación más lenta de la búsqueda."""
    return HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)


def _coleccion(nombre: str) -> Chroma:
    return Chroma(
        collection_name=nombre,
        embedding_function=obtener_embeddings(),
        persist_directory=str(settings.CHROMA_DIR),
    )


def buscar(coleccion: str, texto: str, k: int = 2) -> list[dict]:
    """Devuelve los k fragmentos más cercanos, o una lista vacía si no hay índice.

    Si la memoria semántica falla, el agente sigue: las reglas no dependen de ella.
    """
    try:
        resultados = _coleccion(coleccion).similarity_search_with_score(texto, k=k)
    except Exception as error:
        print(f"[AVISO] Memoria semántica no disponible: {error}")
        return []
    return [
        {"texto": doc.page_content, "meta": doc.metadata, "distancia": round(float(dist), 3)}
        for doc, dist in resultados
    ]


def registrar_caso(texto: str, ciclo: str) -> None:
    """Agrega un ciclo resuelto, para que futuras búsquedas puedan encontrarlo."""
    try:
        _coleccion("casos_previos").add_texts(
            [texto],
            metadatas=[{"fuente": FUENTE_AGENTE, "ciclo": ciclo}],
            ids=[str(uuid.uuid4())],
        )
    except Exception as error:
        print(f"[AVISO] No se pudo guardar el caso en Chroma: {error}")


def borrar_casos_aprendidos() -> None:
    """Quita los casos agregados por el agente; deja los casos base y las políticas."""
    coleccion = _coleccion("casos_previos")
    ids = coleccion.get(where={"fuente": FUENTE_AGENTE})["ids"]
    if ids:
        coleccion.delete(ids=ids)
