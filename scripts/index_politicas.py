"""Indexa políticas y casos anteriores en Chroma."""
from langchain_chroma import Chroma
from langchain_core.documents import Document

from agent.memory.semantic import obtener_embeddings
from config import settings

CASOS = [
    "Caso: un perfume sin ventas en 60 días ocupaba espacio en tienda; se devolvió a la central.",
    "Caso: un producto muy vendido quedó sin stock en tienda; se repuso con prioridad máxima.",
    "Caso: la central no alcanzó para la temporada alta; se solicitó comprar la diferencia.",
    "Caso: una tienda pidió más de lo que vendía en la semana; se aprobó solo lo requerido.",
]


def documentos_por_seccion() -> list[Document]:
    """Crea un fragmento por sección ## de la política (se usa solo para comparar)."""
    texto = (settings.DATA_DIR / "politicas.md").read_text(encoding="utf-8")
    secciones = [s.strip() for s in texto.split("\n## ")[1:] if s.strip()]
    return [
        Document(page_content=s,
                 metadata={"fuente": "politicas.md", "seccion": s.splitlines()[0]})
        for s in secciones
    ]


def documentos_politicas() -> list[Document]:
    """Crea un fragmento por regla: el título de la sección más una línea de la política."""
    documentos = []
    for seccion in documentos_por_seccion():
        titulo, *reglas = seccion.page_content.splitlines()
        for regla in reglas:
            documentos.append(Document(
                page_content=f"{titulo}: {regla.lstrip('- ').strip()}",
                metadata=seccion.metadata,
            ))
    return documentos


def documentos_casos() -> list[Document]:
    return [
        Document(page_content=c, metadata={"fuente": "caso_previo", "id": f"C{i}"})
        for i, c in enumerate(CASOS)
    ]


def _recrear(nombre: str, documentos: list[Document]) -> None:
    Chroma(
        collection_name=nombre,
        embedding_function=obtener_embeddings(),
        persist_directory=str(settings.CHROMA_DIR),
    ).delete_collection()
    Chroma.from_documents(
        documentos, obtener_embeddings(),
        collection_name=nombre,
        persist_directory=str(settings.CHROMA_DIR),
    )


def indexar() -> tuple[int, int]:
    politicas, casos = documentos_politicas(), documentos_casos()
    _recrear("politicas", politicas)
    _recrear("casos_previos", casos)
    return len(politicas), len(casos)


if __name__ == "__main__":
    n_politicas, n_casos = indexar()
    print(f"Indexados {n_politicas} fragmentos de políticas y {n_casos} casos anteriores.")
