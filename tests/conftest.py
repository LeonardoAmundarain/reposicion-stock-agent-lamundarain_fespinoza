"""Fixtures: cada test parte de una base limpia y nunca toca la base de la demo."""
import shutil

import pytest

from config import settings

FECHA = "2026-11-03"


@pytest.fixture(scope="session")
def entorno(tmp_path_factory):
    """Crea una sola vez los datos simulados y el índice semántico en una carpeta temporal."""
    carpeta = tmp_path_factory.mktemp("agente")
    parche = pytest.MonkeyPatch()
    parche.setattr(settings, "FUENTE_DATOS", "simulado")
    parche.setattr(settings, "GOOGLE_API_KEY", None)
    parche.setattr(settings, "ANTHROPIC_API_KEY", None)
    parche.setattr(settings, "LLM_PROVEEDOR", "gemini")
    parche.setattr(settings, "PERMITIR_LLM_CON_DATOS_REALES", False)
    parche.setattr(settings, "RUTA_VENTAS", settings.DATA_DIR / "muestra" / "ventas_simuladas.xlsx")
    parche.setattr(settings, "RUTA_STOCK", settings.DATA_DIR / "muestra" / "stock_simulado.xlsx")
    parche.setattr(settings, "DB_PATH", carpeta / "plantilla.db")
    parche.setattr(settings, "CHROMA_DIR", carpeta / "chroma")

    from scripts.index_politicas import indexar
    from scripts.seed_data import sembrar
    resumen = sembrar()
    indexar()
    yield {"carpeta": carpeta, "plantilla": carpeta / "plantilla.db", "resumen": resumen}
    parche.undo()


@pytest.fixture(autouse=True)
def base_limpia(entorno, monkeypatch, tmp_path):
    """Entrega a cada test su propia copia de la base de datos."""
    from agent.memory.semantic import borrar_casos_aprendidos

    copia = tmp_path / "agente.db"
    shutil.copy(entorno["plantilla"], copia)
    monkeypatch.setattr(settings, "DB_PATH", copia)
    borrar_casos_aprendidos()
