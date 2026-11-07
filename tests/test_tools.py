"""Tests de cada tool con los datos simulados."""
from agent.db import conectar
from agent.inventario import central_disponible
from agent.tools.buscar_politicas import buscar_politicas
from agent.tools.consultar_stock import consultar_stock
from agent.tools.consultar_ventas import consultar_ventas
from agent.tools.notificar_responsable import notificar_responsable
from agent.tools.proyectar_demanda import proyectar_demanda
from agent.tools.registrar_solicitudes import registrar_solicitudes
from agent.tools.solicitar_compra import solicitar_compra


def test_consultar_stock_por_codigo():
    r = consultar_stock.invoke({"consulta": "CUBIERTO14"})
    assert r["productos"][0]["b14"] == 30
    assert r["productos"][0]["central"] == 100


def test_consultar_stock_inexistente():
    assert "error" in consultar_stock.invoke({"consulta": "NO_HAY_ESTO"})


def test_consultar_stock_resumen_de_local():
    assert consultar_stock.invoke({"local": 14})["unidades"] > 0


def test_consultar_ventas_del_local():
    r = consultar_ventas.invoke({"local": 15, "codigo": "QUIEBRE15"})
    assert r["productos"][0]["unidades"] == 152
    assert round(r["productos"][0]["venta_diaria"], 2) == 1.0


def test_consultar_ventas_local_invalido():
    assert "error" in consultar_ventas.invoke({"local": 99})


def test_proyectar_demanda_sube_en_temporada_alta():
    normal = proyectar_demanda.invoke({"local": 15, "codigo": "QUIEBRE15", "fecha": "2026-11-03"})
    alta = proyectar_demanda.invoke({"local": 15, "codigo": "QUIEBRE15", "fecha": "2026-11-20"})
    assert normal["venta_periodo"] == 9
    assert alta["venta_periodo"] == 13.5
    assert alta["factor_temporada"] == 1.5


def test_buscar_politicas_encuentra_compras():
    r = buscar_politicas.invoke({"texto": "la central no alcanza para lo proyectado, solicitar comprar"})
    politicas = [x for x in r if x["tipo"] == "politica"]
    assert politicas[0]["meta"]["seccion"] == "Compras"


def test_registrar_reposicion_compromete_la_central():
    conn = conectar()
    antes = central_disponible(conn, "QUIEBRE15")
    conn.close()
    r = registrar_solicitudes.invoke({
        "ciclo": "c1", "local": 15, "tipo": "reposicion", "fecha": "2026-11-03",
        "items": [{"codigo": "QUIEBRE15", "cantidad": 9, "razon": "test"}],
    })
    assert r["registradas"] == 1
    conn = conectar()
    assert central_disponible(conn, "QUIEBRE15") == antes - 9
    conn.close()


def test_registrar_reposicion_ajusta_si_no_alcanza():
    r = registrar_solicitudes.invoke({
        "ciclo": "c1", "local": 15, "tipo": "reposicion", "fecha": "2026-11-03",
        "items": [{"codigo": "ESCASO", "cantidad": 50, "razon": "test"}],
    })
    assert r["unidades"] == 6
    assert r["ajustes"] == [{"codigo": "ESCASO", "pedido": 50, "aprobado": 6}]


def test_solicitar_compra_queda_pendiente():
    r = solicitar_compra.invoke({
        "ciclo": "c1", "fecha": "2026-11-03",
        "items": [{"codigo": "AGOTADO15", "cantidad": 30, "razon": "test"}],
    })
    assert r["unidades"] == 30
    conn = conectar()
    assert conn.execute("SELECT estado FROM solicitudes").fetchone()[0] == "pendiente_compra"
    conn.close()


def test_notificar_responsable():
    assert notificar_responsable.invoke({"destino": "Tienda", "mensaje": "hola"})["ok"] is True
