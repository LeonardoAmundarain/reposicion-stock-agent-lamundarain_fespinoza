"""Compara modelos de embeddings: ¿recuperan la sección correcta de la política?"""
import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings

from scripts.index_politicas import documentos_por_seccion, documentos_politicas

MODELOS = [
    "sentence-transformers/all-MiniLM-L6-v2",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
]
# (pregunta redactada sin copiar las palabras de la política, sección esperada)
PREGUNTAS = [
    ("cuántos días de venta debe alcanzar a cubrir la mercadería de una tienda", "Reposición de tiendas"),
    ("en cuánto tiempo llega lo que pide un local", "Reposición de tiendas"),
    ("cada cuánto puede pedir productos un local físico", "Reposición de tiendas"),
    ("hay un límite de dinero para autorizar un pedido", "Aprobación de solicitudes"),
    ("un local pidió más unidades de las que necesita", "Aprobación de solicitudes"),
    ("qué hago con un perfume que nadie compra hace dos meses", "Devoluciones a bodega central"),
    ("cómo libero espacio en el local", "Devoluciones a bodega central"),
    ("cuántas veces al mes se abastece la bodega de internet", "Bodega online"),
    ("qué surtido mínimo debe tener la venta por internet", "Bodega online"),
    ("en qué fechas sube la venta por navidad", "Temporada alta"),
    ("cuánto más se vende en fin de año", "Temporada alta"),
    ("no queda mercadería suficiente en la central para lo proyectado", "Compras"),
    ("cuándo se avisa a adquisiciones que falta producto", "Compras"),
    ("a quién se atiende primero si no alcanza el stock", "Prioridades cuando la bodega central no alcanza"),
    ("qué producto tiene preferencia cuando hay poco", "Prioridades cuando la bodega central no alcanza"),
    ("se cuentan las ventas al por mayor para calcular cuánto pedir", "Cálculo de la demanda"),
    ("cómo se tratan las devoluciones de clientes en las ventas", "Cálculo de la demanda"),
]


def evaluar(embeddings, documentos) -> tuple[int, int, list[str]]:
    """Cuenta cuántas preguntas encuentran su sección en el 1.er o en los 2 primeros lugares."""
    matriz = np.array(embeddings.embed_documents([d.page_content for d in documentos]))
    matriz /= np.linalg.norm(matriz, axis=1, keepdims=True)
    secciones = [d.metadata["seccion"] for d in documentos]
    top1, top2, errores = 0, 0, []
    for pregunta, esperada in PREGUNTAS:
        vector = np.array(embeddings.embed_query(pregunta))
        orden = np.argsort(-(matriz @ (vector / np.linalg.norm(vector))))
        if secciones[orden[0]] == esperada:
            top1 += 1
        else:
            errores.append(f'"{pregunta}": devolvió "{secciones[orden[0]]}", se esperaba "{esperada}"')
        if esperada in (secciones[orden[0]], secciones[orden[1]]):
            top2 += 1
    return top1, top2, errores


if __name__ == "__main__":
    fragmentos = {"por sección": documentos_por_seccion(), "por regla": documentos_politicas()}
    lineas = [
        "# Evaluación de embeddings", "",
        f"{len(PREGUNTAS)} preguntas en español, redactadas sin copiar las palabras de `data/politicas.md`.",
        "Se mide si la sección esperada aparece en el primer resultado o entre los dos primeros.", "",
        "| Modelo | Fragmentos | 1.er lugar | Entre los 2 primeros |", "|---|---|---|---|",
    ]
    detalle = []
    for modelo in MODELOS:
        nombre_modelo = modelo.split("/")[1]
        embeddings = HuggingFaceEmbeddings(model_name=modelo)
        for nombre, documentos in fragmentos.items():
            top1, top2, errores = evaluar(embeddings, documentos)
            total = len(PREGUNTAS)
            lineas.append(f"| `{nombre_modelo}` | {nombre} ({len(documentos)}) | {top1}/{total} | {top2}/{total} |")
            detalle += ["", f"## Errores: `{nombre_modelo}`, {nombre}", ""] + [f"- {e}" for e in errores]
    salida = "\n".join(lineas + detalle) + "\n"
    with open("evidence/eval_embeddings.md", "w", encoding="utf-8") as archivo:
        archivo.write(salida)
    print(salida)
