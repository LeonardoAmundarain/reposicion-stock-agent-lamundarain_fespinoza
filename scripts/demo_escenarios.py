"""Ejecuta los escenarios de la demo con datos simulados y guarda la evidencia."""
import json
import sys

from agent.core import confirmar_recepcion, evaluar_solicitud_tienda, planificar_local
from agent.memory import long_term
from agent.memory.semantic import borrar_casos_aprendidos
from config import settings
from scripts.seed_data import sembrar


def linea(resultado: dict, codigo: str) -> dict:
    fila = next(l for l in resultado["lineas"] if l["codigo"] == codigo)
    return {c: fila[c] for c in ("accion", "cantidad", "compra", "objetivo", "stock_local",
                                 "en_transito", "central", "prioridad", "razon")}


def reiniciar() -> None:
    sembrar()
    borrar_casos_aprendidos()


def main() -> None:
    if settings.FUENTE_DATOS != "simulado":
        sys.exit("Este script publica evidencia: ejecútalo solo con FUENTE_DATOS=simulado.")
    casos = []

    def registrar(escenario: str, condicion: str, resultado: dict) -> None:
        casos.append({"escenario": escenario, "condicion": condicion, "resultado": resultado})

    reiniciar()
    r = planificar_local(15, "2026-11-03")
    registrar("1. Quiebre en tienda", "QUIEBRE15 sin stock y con venta diaria de 1", linea(r, "QUIEBRE15"))
    registrar("2. Sin movimiento", "LENTO15 con stock y sin ventas en 60 días", linea(r, "LENTO15"))
    registrar("3. Central sin unidades", "AGOTADO15 sin stock en la central", linea(r, "AGOTADO15"))

    r2 = planificar_local(15, "2026-11-04")
    registrar("4. Memoria: pedido en camino", "Mismo local al día siguiente", linea(r2, "QUIEBRE15"))

    alta = planificar_local(15, "2026-11-20")
    registrar("5. Temporada alta", "Misma tienda y producto el 20 de noviembre", linea(alta, "QUIEBRE15"))

    reiniciar()
    r = planificar_local(14, "2026-11-03", simular_merma={"MERMA14": 8})
    registrar("6. Replanificación", "La central pierde 8 unidades durante la ejecución",
              {**linea(r, "MERMA14"), "replanificaciones": r["replanificaciones"]})

    reiniciar()
    registrar("7. Pedido excedido", "La tienda pide 50 y requiere 9",
              evaluar_solicitud_tienda(15, "QUIEBRE15", 50, "2026-11-03"))
    registrar("8. Pedido no requerido", "La tienda pide 5 de un producto cubierto",
              evaluar_solicitud_tienda(14, "CUBIERTO14", 5, "2026-11-03"))

    reiniciar()
    planificar_local(15, "2026-11-03")
    compra = next(s for s in long_term.solicitudes() if s["codigo"] == "AGOTADO15" and s["tipo"] == "compra")
    registrar("9. Retomar tarea", "Llega la compra de AGOTADO15", confirmar_recepcion(compra["id"], "2026-11-05"))

    reiniciar()
    r = planificar_local(16, "2026-11-03")
    registrar("10. Online por quincena", "Primer pedido de la quincena", linea(r, "ONLINE1"))
    registrar("11. Frecuencia online", "Segundo intento en la misma quincena",
              {"accion": planificar_local(16, "2026-11-05")["accion"]})

    reiniciar()
    with open("evidence/escenarios.json", "w", encoding="utf-8") as archivo:
        json.dump(casos, archivo, ensure_ascii=False, indent=2, default=str)
    for caso in casos:
        print(f"{caso['escenario']}: {caso['resultado'].get('accion', caso['resultado'].get('decision', caso['resultado'].get('retomados')))}")


if __name__ == "__main__":
    main()
