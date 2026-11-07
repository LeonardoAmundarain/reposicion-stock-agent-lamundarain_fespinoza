"""Tests del iniciador: cómo actualiza el archivo .env."""
import io

from scripts.iniciar import SIN_CLAVE, fijar_variable, leer_variable, preguntar, tiene_clave

ENV = "FUENTE_DATOS=simulado\nGOOGLE_API_KEY=tu_api_key_aqui\n"


def test_reemplaza_una_variable_existente():
    texto = fijar_variable(ENV, "GOOGLE_API_KEY", "nueva")
    assert leer_variable(texto, "GOOGLE_API_KEY") == "nueva"
    assert leer_variable(texto, "FUENTE_DATOS") == "simulado"


def test_agrega_una_variable_que_falta():
    texto = fijar_variable(ENV, "ANTHROPIC_API_KEY", "otra")
    assert texto.endswith("ANTHROPIC_API_KEY=otra\n")


def test_un_valor_con_caracteres_especiales_se_guarda_tal_cual():
    texto = fijar_variable(ENV, "GOOGLE_API_KEY", r"a\1b$c")
    assert leer_variable(texto, "GOOGLE_API_KEY") == r"a\1b$c"


def test_el_texto_de_ejemplo_no_cuenta_como_clave():
    assert tiene_clave(ENV, "GOOGLE_API_KEY") is False
    assert tiene_clave(fijar_variable(ENV, "GOOGLE_API_KEY", "x"), "GOOGLE_API_KEY") is True
    assert SIN_CLAVE in ENV


def test_sin_respuesta_se_toma_como_enter(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    assert preguntar("Key: ", oculto=True) == ""
