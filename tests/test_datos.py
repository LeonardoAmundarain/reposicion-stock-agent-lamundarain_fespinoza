"""Tests de la limpieza y el cruce de datos."""
import pandas as pd

from agent.datos import cruzar_con_stock, limpiar_ventas
from agent.db import conectar


def _linea(modulo="GUIA DESPACHO", fecha="2026-07-01", caja=15, codigo="A", ean="111",
           descripcion="PERFUME A", cant=1, venta=1000):
    return {"MODULO": modulo, "FECHA": fecha, "CAJA": caja, "CODIGO": codigo, "COD ALT": ean,
            "DESCRIPCION": descripcion, "CANT": cant, "COSTO": 500, "VENTA": venta}


def test_excluye_lo_que_no_es_venta():
    df = pd.DataFrame([
        _linea(),
        _linea(modulo="COTIZACION"),
        _linea(descripcion="PRUEBA TIENDA"),
        _linea(fecha="2026-02-02"),
        _linea(venta=0),
    ])
    limpio, resumen = limpiar_ventas(df)
    assert len(limpio) == 1
    assert resumen["cotizaciones"] == 1
    assert resumen["pruebas"] == 1
    assert resumen["fuera_de_periodo"] == 1
    assert resumen["venta_cero"] == 1


def test_venta_negativa_resta_unidades():
    limpio, _ = limpiar_ventas(pd.DataFrame([_linea(cant=2), _linea(cant=1, venta=-1000)]))
    assert limpio["unidades"].sum() == 1


def test_linea_grande_queda_marcada_como_mayorista():
    limpio, _ = limpiar_ventas(pd.DataFrame([_linea(cant=9), _linea(cant=10)]))
    assert limpio["mayorista"].tolist() == [0, 1]


def test_caja_37_corresponde_al_local_16():
    limpio, _ = limpiar_ventas(pd.DataFrame([_linea(caja=37)]))
    assert limpio["local"].iloc[0] == 16


def test_cruce_por_codigo_y_luego_por_ean():
    stock = pd.DataFrame({"codigo": ["A", "B"], "ean": ["111", "222"]})
    ventas = pd.DataFrame({"codigo": ["A", "OTRO", "NADA"], "ean": [None, "222", "999"]})
    cruzadas, sin_cruce = cruzar_con_stock(ventas, stock)
    assert cruzadas["codigo_stock"].tolist() == ["A", "B"]
    assert sin_cruce["codigo"].tolist() == ["NADA"]


def test_seed_registra_lo_que_no_cruzo(entorno):
    assert entorno["resumen"]["productos_sin_cruce"] == 1
    conn = conectar()
    assert conn.execute("SELECT codigo FROM sin_cruce").fetchone()[0] == "NO_EXISTE"
    conn.close()
