"""Tests de punta a punta: datos, planner, tools y memoria juntos."""
from agent.core import confirmar_recepcion, evaluar_solicitud_tienda, planificar_local, planificar_todo
from agent.db import conectar
from agent.memory import long_term
from scripts.seed_data import ArchivoOcupado, reiniciar_demo, sembrar
from config import settings
from tests.conftest import FECHA


def _linea(resultado, codigo):
    return next(l for l in resultado["lineas"] if l["codigo"] == codigo)


def test_repone_producto_en_quiebre_con_prioridad_maxima():
    r = planificar_local(15, FECHA)
    linea = _linea(r, "QUIEBRE15")
    assert (linea["accion"], linea["cantidad"], linea["prioridad"]) == ("reponer", 9, 1)
    assert r["lineas"][0]["prioridad"] == 1


def test_no_pide_lo_que_ya_esta_cubierto():
    assert _linea(planificar_local(14, FECHA), "CUBIERTO14")["accion"] == "cubierto"


def test_devuelve_lo_que_no_se_mueve():
    assert _linea(planificar_local(15, FECHA), "LENTO15")["accion"] == "devolver_central"
    assert _linea(planificar_local(14, FECHA), "NOVENDE14")["cantidad"] == 4


def test_compra_si_la_central_no_tiene():
    linea = _linea(planificar_local(15, FECHA), "AGOTADO15")
    assert linea["accion"] == "sin_stock_central"
    assert linea["compra"] > 0


def test_online_cubre_hasta_fin_de_quincena():
    linea = _linea(planificar_local(16, FECHA), "ONLINE1")
    assert (linea["objetivo"], linea["cantidad"]) == (13, 11)


def test_cita_la_politica_recuperada():
    r = planificar_local(15, FECHA)
    secciones = {f["accion"]: f["seccion"] for f in r["fuentes"]}
    assert secciones["devolver_central"] == "Devoluciones a bodega central"
    assert secciones["reponer"] == "Reposición de tiendas"
    assert secciones["sin_stock_central"] == "Compras"


def test_decision_cambia_con_la_temporada():
    normal = _linea(planificar_local(15, "2026-11-03"), "QUIEBRE15")["objetivo"]
    alta = _linea(planificar_local(15, "2026-11-20"), "QUIEBRE15")["objetivo"]
    assert (normal, alta) == (9, 14)


def test_stock_central_compartido_se_reparte_por_orden():
    r = planificar_todo(FECHA)["resultados"]
    assert _linea(r[15], "ESCASO")["cantidad"] == 5
    assert _linea(r[16], "ESCASO")["cantidad"] == 1


def test_tienda_no_repone_ni_compra_para_otra_linea():
    linea = _linea(planificar_local(14, FECHA), "ESCASO")
    assert (linea["accion"], linea["cantidad"], linea["compra"]) == ("fuera_de_linea", 0, 0)


def test_online_repone_todas_las_lineas():
    assert _linea(planificar_local(16, FECHA), "ESCASO")["accion"] != "fuera_de_linea"


def test_pedido_manual_de_otra_linea_se_rechaza():
    r = evaluar_solicitud_tienda(14, "ESCASO", 2, FECHA)
    assert (r["decision"], r["aprobado"]) == ("rechazada", 0)
    assert "línea" in r["razon"]


def test_memoria_evita_pedir_dos_veces_lo_que_viene_en_camino():
    planificar_local(15, FECHA)
    segundo = planificar_local(15, "2026-11-04")
    assert "reponer" not in segundo["conteo"]
    assert _linea(segundo, "QUIEBRE15")["en_transito"] == 9


def test_memoria_no_repite_compras_ni_devoluciones():
    planificar_local(15, FECHA)
    segundo = planificar_local(15, "2026-11-04")
    assert segundo["compras"] == 0
    assert _linea(segundo, "LENTO15")["accion"] == "en_curso"


def test_tienda_maximo_dos_pedidos_por_semana():
    planificar_local(15, "2026-11-03")
    assert planificar_local(15, "2026-11-08")["accion"] == "planificado"
    assert planificar_local(15, "2026-11-09")["accion"] == "frecuencia_cumplida"


def test_online_un_pedido_por_quincena():
    planificar_local(16, "2026-11-03")
    assert planificar_local(16, "2026-11-05")["accion"] == "frecuencia_cumplida"
    assert planificar_local(16, "2026-11-16")["accion"] == "planificado"


def test_recuerda_el_ciclo_anterior_tras_reiniciar():
    primero = planificar_local(14, FECHA)
    recordado = long_term.ultimo_ciclo(14)
    assert recordado["ciclo"] == primero["ciclo"]
    segundo = planificar_local(14, "2026-11-04")
    assert segundo["traza"][0]["salida"]["ciclo"] == primero["ciclo"]


def test_replanifica_si_la_central_cambia_durante_la_ejecucion():
    r = planificar_local(14, FECHA, simular_merma={"MERMA14": 8})
    linea = _linea(r, "MERMA14")
    assert (linea["accion"], linea["cantidad"]) == ("reponer_parcial", 4)
    assert linea["compra"] == 73  # Venta proyectada 77 menos las 4 unidades que quedaron.
    assert r["replanificaciones"]
    assert "replanificar" in [t["paso"] for t in r["traza"]]


def test_pedido_manual_se_aprueba_solo_lo_requerido():
    r = evaluar_solicitud_tienda(15, "QUIEBRE15", 50, FECHA)
    assert (r["decision"], r["aprobado"]) == ("ajustada", 9)


def test_pedido_manual_no_requerido_se_rechaza():
    assert evaluar_solicitud_tienda(14, "CUBIERTO14", 5, FECHA)["decision"] == "rechazada"


def test_pedido_manual_sin_monto_tope_si_es_requerido():
    r = evaluar_solicitud_tienda(15, "QUIEBRE15", 9, FECHA)
    assert (r["decision"], r["aprobado"]) == ("aprobada", 9)


def test_recibir_reposicion_mueve_el_stock():
    planificar_local(15, FECHA)
    abierta = next(s for s in long_term.solicitudes(local=15)
                   if s["codigo"] == "QUIEBRE15" and s["tipo"] == "reposicion")
    confirmar_recepcion(abierta["id"], FECHA)
    conn = conectar()
    assert conn.execute("SELECT b15 FROM stock WHERE codigo = 'QUIEBRE15'").fetchone()[0] == 9
    conn.close()


def test_recibir_compra_retoma_el_producto_pendiente():
    planificar_local(15, FECHA)
    compra = next(s for s in long_term.solicitudes()
                  if s["codigo"] == "AGOTADO15" and s["tipo"] == "compra")
    r = confirmar_recepcion(compra["id"], FECHA)
    assert r["retomados"][15] == 4
    reposicion = [s for s in long_term.solicitudes(local=15)
                  if s["codigo"] == "AGOTADO15" and s["tipo"] == "reposicion"]
    assert reposicion[0]["cantidad"] == 4


def test_reiniciar_demo_restaura_todo_sin_leer_los_archivos(monkeypatch):
    planificar_local(14, FECHA, simular_merma={"MERMA14": 8})
    compra = next(s for s in long_term.solicitudes() if s["tipo"] == "compra")
    confirmar_recepcion(compra["id"], FECHA)
    monkeypatch.setattr(settings, "RUTA_STOCK", settings.DATA_DIR / "no_existe.xlsx")
    monkeypatch.setattr(settings, "RUTA_VENTAS", settings.DATA_DIR / "no_existe.xlsx")

    reiniciar_demo()

    conn = conectar()
    assert conn.execute("SELECT COUNT(*) FROM solicitudes").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM ciclos").fetchone()[0] == 0
    assert conn.execute("SELECT total FROM stock WHERE codigo = 'MERMA14'").fetchone()[0] == 12
    conn.close()


def test_archivo_abierto_en_excel_da_un_aviso_claro(monkeypatch):
    def bloqueado(ruta):
        raise PermissionError(13, "Permission denied", str(ruta))

    monkeypatch.setattr("scripts.seed_data.leer_stock", bloqueado)
    try:
        sembrar()
    except ArchivoOcupado as error:
        assert "Cierra el archivo en Excel" in str(error)
    else:
        raise AssertionError("Debía avisar que el archivo está ocupado")
    assert conectar().execute("SELECT COUNT(*) FROM stock").fetchone()[0] > 0


def test_local_inexistente():
    assert planificar_local(99, FECHA)["ok"] is False
