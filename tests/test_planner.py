"""Tests del planner y de la proyección. No usan base de datos ni LLM."""
from datetime import date

from agent import demanda
from agent.planner import (
    PLAN_BASE, ajustar_plan, construir_estado, decidir_accion, decidir_compra, prioridad, replanificar,
)


def _estado(**cambios):
    base = dict(tipo_local="tienda", stock_local=0, en_transito=0, central=100,
                venta_diaria=1.0, objetivo=9, activo=True)
    return construir_estado(**{**base, **cambios})


def test_regla_1_devuelve_lo_que_no_se_mueve():
    a = decidir_accion(_estado(stock_local=5, activo=False, objetivo=0))
    assert (a.tipo, a.cantidad, a.regla) == ("devolver_central", 5, 1)


def test_online_no_devuelve_aunque_no_se_mueva():
    a = decidir_accion(_estado(tipo_local="online", stock_local=5, activo=False, objetivo=0))
    assert a.tipo == "sin_accion"


def test_venta_mayorista_reciente_evita_la_devolucion():
    estado = _estado(stock_local=5, activo=False, objetivo=0, con_movimiento=True)
    assert decidir_accion(estado).tipo == "sin_accion"


def test_regla_2_otra_linea_no_se_repone():
    a = decidir_accion(_estado(stock_local=2, en_linea=False))
    assert (a.tipo, a.cantidad, a.regla) == ("fuera_de_linea", 0, 2)


def test_otra_linea_sin_movimiento_se_devuelve():
    a = decidir_accion(_estado(stock_local=3, activo=False, objetivo=0, en_linea=False))
    assert (a.tipo, a.cantidad) == ("devolver_central", 3)


def test_regla_3_no_repone_lo_que_no_vende():
    assert decidir_accion(_estado(activo=False, objetivo=0)).tipo == "sin_accion"


def test_regla_4_no_pide_si_esta_cubierto():
    assert decidir_accion(_estado(stock_local=9)).tipo == "cubierto"


def test_regla_4_considera_lo_que_viene_en_camino():
    assert decidir_accion(_estado(stock_local=2, en_transito=7)).tipo == "cubierto"


def test_regla_5_repone_solo_la_diferencia():
    a = decidir_accion(_estado(stock_local=2))
    assert (a.tipo, a.cantidad) == ("reponer", 7)


def test_regla_6_repone_lo_que_alcanza():
    a = decidir_accion(_estado(central=3))
    assert (a.tipo, a.cantidad) == ("reponer_parcial", 3)


def test_regla_7_sin_central():
    a = decidir_accion(_estado(central=0))
    assert (a.tipo, a.cantidad) == ("sin_stock_central", 0)


def test_no_repite_devolucion_en_curso():
    a = decidir_accion(_estado(stock_local=5, activo=False, devolucion_abierta=True))
    assert a.tipo == "en_curso"


def test_prioridad_por_urgencia():
    assert prioridad(_estado()) == 1
    assert prioridad(_estado(stock_local=1)) == 2
    assert prioridad(_estado(stock_local=5)) == 3


def test_compra_descuenta_lo_ya_solicitado():
    assert decidir_compra(0, 100.0, 40, 0) == 60
    assert decidir_compra(0, 100.0, 40, 25) == 35
    assert decidir_compra(0, 100.0, 200, 0) == 0
    assert decidir_compra(5, 10.0, 10, 0) == 5


def test_temporada_alta_solo_en_las_fechas_acordadas():
    assert demanda.factor_temporada(date(2026, 11, 15)) == 1.0
    assert demanda.factor_temporada(date(2026, 11, 16)) == 1.5
    assert demanda.factor_temporada(date(2026, 12, 21)) == 1.5
    assert demanda.factor_temporada(date(2026, 12, 22)) == 1.0


def test_objetivo_tienda_cubre_siete_dias_mas_dos_de_demora():
    assert demanda.objetivo_tienda(1.0, date(2026, 11, 3)) == 9
    assert demanda.objetivo_tienda(1.0, date(2026, 11, 20)) == 14


def test_objetivo_online_cubre_hasta_fin_de_quincena():
    assert demanda.objetivo_online(1.0, date(2026, 11, 3)) == 13
    assert demanda.fin_de_quincena(date(2026, 11, 16)) == date(2026, 11, 30)


def test_objetivo_online_mantiene_surtido_minimo():
    assert demanda.objetivo_online(0.001, date(2026, 11, 3)) == 1


def test_plan_omite_pasos_sin_trabajo():
    plan = ajustar_plan(PLAN_BASE, hay_devoluciones=False, hay_reposiciones=True, hay_compras=False)
    assert "registrar_devoluciones" not in plan
    assert "solicitar_compra" not in plan
    assert "registrar_reposiciones" in plan


def test_replanificar_agrega_compra_antes_de_notificar():
    nuevo = replanificar(["notificar_responsable", "guardar_memoria"], "central_insuficiente")
    assert nuevo == ["solicitar_compra", "notificar_responsable", "guardar_memoria"]
