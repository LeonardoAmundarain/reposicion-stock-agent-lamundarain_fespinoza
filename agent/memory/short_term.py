"""Memoria de corto plazo: buffer de la conversación actual."""
import re

from langchain_classic.memory import ConversationBufferMemory

PATRON_LOCAL = re.compile(r"\b(?:local|tienda|bodega|caja)\s*(14|15|16|37)\b", re.IGNORECASE)
PALABRAS_LOCAL = {"diseñador": 14, "disenador": 14, "árabe": 15, "arabe": 15, "online": 16}


def crear_memoria_corto_plazo() -> ConversationBufferMemory:
    """Crea una memoria de conversación en RAM.

    Se guarda en st.session_state para persistir durante la sesión.
    """
    return ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        input_key="input",
        output_key="output",
    )


def detectar_local(texto: str) -> int | None:
    """Reconoce un local por número, caja o nombre de la línea."""
    encontrado = PATRON_LOCAL.search(texto)
    if encontrado:
        numero = int(encontrado.group(1))
        return 16 if numero == 37 else numero
    minusculas = texto.lower()
    for palabra, local in PALABRAS_LOCAL.items():
        if palabra in minusculas:
            return local
    return None


def local_en_contexto(memoria: ConversationBufferMemory) -> int | None:
    """Devuelve el último local mencionado en la conversación."""
    for mensaje in reversed(memoria.chat_memory.messages):
        local = detectar_local(str(mensaje.content))
        if local:
            return local
    return None
