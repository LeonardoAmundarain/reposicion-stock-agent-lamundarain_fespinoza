"""Configuración central del proyecto."""
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Evita que Chroma envíe telemetría anónima a internet.
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Fuente de datos: "simulado" (lo que se publica) o "real" (solo en el computador local).
FUENTE_DATOS = os.getenv("FUENTE_DATOS", "simulado")
# Una ruta relativa se cuenta desde la carpeta del proyecto.
RUTA_VENTAS = BASE_DIR / os.getenv("RUTA_VENTAS", "data/muestra/ventas_simuladas.xlsx")
RUTA_STOCK = BASE_DIR / os.getenv("RUTA_STOCK", "data/muestra/stock_simulado.xlsx")
DB_PATH = DATA_DIR / f"agente_{FUENTE_DATOS}.db"
CHROMA_DIR = DATA_DIR / f"chroma_{FUENTE_DATOS}"

# Locales: cada uno vende por una caja y se abastece desde una bodega.
LOCALES = {
    # "lineas": valores de la columna NICHO que se reponen; None significa todos.
    14: {"nombre": "Tienda Diseñador", "caja": 14, "bodega": "b14", "tipo": "tienda", "lineas": {"DISEÑADOR"}},
    15: {"nombre": "Tienda Árabes", "caja": 15, "bodega": "b15", "tipo": "tienda", "lineas": {"ARABES / DUPES"}},
    16: {"nombre": "Online", "caja": 37, "bodega": "b16", "tipo": "online", "lineas": None},
}
CAJA_A_LOCAL = {datos["caja"]: local for local, datos in LOCALES.items()}

# Limpieza de ventas
INICIO_VENTAS = "2026-06-01"
UMBRAL_MAYORISTA = 10  # Líneas con esta cantidad o más no cuentan como venta normal.

# Reglas de reposición
DIAS_COBERTURA_TIENDA = 7
DIAS_REPOSICION = 2  # Demora entre la solicitud y la llegada a la tienda.
DIAS_SIN_MOVIMIENTO = 60

# Temporada alta: 1,5 veces un mes normal desde la segunda quincena de noviembre
# hasta la tercera semana de diciembre.
FACTOR_PICO = 1.5
PICO_INICIO = date(2026, 11, 16)
PICO_FIN = date(2026, 12, 21)
FIN_HORIZONTE = date(2026, 12, 31)

# Fecha que el agente considera como "hoy" si no se indica otra.
FECHA_PLAN = os.getenv("FECHA_PLAN", "2026-11-03")

# LLM: "gemini" (por defecto) o "claude". En la interfaz también se puede cambiar.
LLM_PROVEEDOR = os.getenv("LLM_PROVEEDOR", "gemini")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.6-flash")
# Si el modelo principal está saturado o no responde, se intenta con este.
LLM_RESPALDO = os.getenv("LLM_RESPALDO", "gemini-3.5-flash-lite")
# Modelos que ofrece el panel. En Gemini, este también es el orden en que se prueban
# cuando uno se queda sin cuota o no responde.
GEMINI_MODELOS = list(dict.fromkeys([LLM_MODEL, LLM_RESPALDO] + [
    "gemini-3-flash-preview", "gemini-3.7-flash", "gemini-3.5-flash",
    "gemini-3.8-flash", "gemini-3.1-flash-lite",
]))
MAX_INTENTOS_GEMINI = int(os.getenv("MAX_INTENTOS_GEMINI", str(len(GEMINI_MODELOS))))
CLAUDE_MODELOS = ["claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5", "claude-fable-5-1"]
# En el nivel gratuito, Google puede usar el contenido para mejorar sus productos.
# Por eso, con datos reales el LLM queda apagado salvo que se autorice expresamente.
PERMITIR_LLM_CON_DATOS_REALES = os.getenv("PERMITIR_LLM_CON_DATOS_REALES", "false").lower() == "true"

# Embeddings: modelo gratuito y local (ver evidence/eval_embeddings.md)
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)


def clave_configurada(proveedor: str) -> bool:
    """Revisa si el .env tiene una API key real para el proveedor."""
    clave = ANTHROPIC_API_KEY if proveedor == "claude" else GOOGLE_API_KEY
    return bool(clave) and clave != "tu_api_key_aqui"


def llm_habilitado(proveedor: str | None = None) -> bool:
    """Indica si el agente puede enviar información al proveedor."""
    if not clave_configurada(proveedor or LLM_PROVEEDOR):
        return False
    return FUENTE_DATOS != "real" or PERMITIR_LLM_CON_DATOS_REALES


def motivo_llm_apagado(proveedor: str) -> str:
    """Explica por qué un proveedor no se puede usar."""
    if not clave_configurada(proveedor):
        variable = "ANTHROPIC_API_KEY" if proveedor == "claude" else "GOOGLE_API_KEY"
        return f"Falta {variable} en el archivo .env; el chat usará reglas."
    return "Con datos reales falta autorizar el LLM en el .env; el chat usará reglas."


def fecha_plan(fecha: str | date | None = None) -> date:
    """Convierte la fecha recibida; sin fecha, usa la fecha configurada."""
    if isinstance(fecha, date):
        return fecha
    return date.fromisoformat(fecha or FECHA_PLAN)
