"""Planner: decide qué hacer con cada producto y en qué orden ejecutar el trabajo.

decidir_accion es una función pura: no toca la base de datos ni llama al LLM.
"""
import math
from dataclasses import dataclass

from config import settings

PLAN_BASE = [
    "recordar_ciclo_anterior",
    "consultar_stock",
    "consultar_ventas",
    "proyectar_demanda",
    "decidir_por_producto",
    "secuenciar_por_prioridad",
    "buscar_politicas",
    "registrar_devoluciones",
    "registrar_reposiciones",
    "solicitar_compra",
    "notificar_responsable",
    "guardar_memoria",
]


@dataclass
class Accion:
    tipo: str
    cantidad: int
    razon: str
    regla: int | None = None


def construir_estado(tipo_local: str, stock_local: int, en_transito: int, central: int,
                     venta_diaria: float, objetivo: int, activo: bool,
                     devolucion_abierta: bool = False,
                     con_movimiento: bool | None = None,
                     en_linea: bool = True) -> dict:
    """Arma el estado que consume decidir_accion."""
    return {
        "tipo_local": tipo_local,
        "stock_local": stock_local,
        "en_transito": en_transito,
        "central": central,
        "venta_diaria": venta_diaria,
        "objetivo": objetivo,
        "activo": activo,
        "con_movimiento": activo if con_movimiento is None else con_movimiento,
        "devolucion_abierta": devolucion_abierta,
        "en_linea": en_linea,
    }


def decidir_accion(estado: dict) -> Accion:
    """Aplica las reglas en orden de prioridad; la primera que se cumple decide."""
    stock = estado["stock_local"]
    # Evita repetir un trabajo que ya está en curso.
    if estado.get("devolucion_abierta"):
        return Accion("en_curso", 0, "Ya hay una devolución en camino")

    # Regla 1: lo que no se mueve vuelve a la central para hacer espacio.
    # Una venta mayorista reciente también es movimiento, aunque no cuente como demanda.
    if estado["tipo_local"] == "tienda" and stock > 0 and not estado["con_movimiento"]:
        return Accion("devolver_central", stock,
                      f"Sin ventas en {settings.DIAS_SIN_MOVIMIENTO} días", 1)
    # Regla 2: la venta migra de a poco; lo de otra línea se vende hasta agotarse.
    if not estado.get("en_linea", True):
        return Accion("fuera_de_linea", 0, "Pertenece a la línea de otra tienda: no se repone", 2)
    # Regla 3: solo se repone lo que el local vende.
    if not estado["activo"]:
        return Accion("sin_accion", 0, "El local no lo vende", 3)
    # Regla 4: una solicitud solo se aprueba si es requerida.
    disponible = stock + estado["en_transito"]
    necesidad = estado["objetivo"] - disponible
    if necesidad <= 0:
        return Accion("cubierto", 0,
                      f"Tiene {disponible} y necesita {estado['objetivo']}", 4)
    # Regla 5: la central alcanza para toda la necesidad.
    if estado["central"] >= necesidad:
        return Accion("reponer", necesidad,
                      f"Necesita {estado['objetivo']} y tiene {disponible}", 5)
    # Regla 6: la central alcanza solo para una parte.
    if estado["central"] > 0:
        return Accion("reponer_parcial", estado["central"],
                      f"Necesita {necesidad} y la central solo tiene {estado['central']}", 6)
    # Regla 7: la central no tiene unidades.
    return Accion("sin_stock_central", 0, f"Necesita {necesidad} y la central no tiene", 7)


def prioridad(estado: dict) -> int:
    """1 = sin stock; 2 = quiebra antes de que llegue la reposición; 3 = el resto."""
    disponible = estado["stock_local"] + estado["en_transito"]
    if disponible <= 0:
        return 1
    if estado["venta_diaria"] > 0 and disponible / estado["venta_diaria"] < settings.DIAS_REPOSICION:
        return 2
    return 3


def decidir_compra(faltante_inmediato: int, proyeccion_total: float, stock_total: int,
                   compra_abierta: int) -> int:
    """Cantidad a comprar para cumplir la semana y la venta hasta fin de diciembre."""
    faltante_horizonte = math.ceil(proyeccion_total - stock_total)
    return max(faltante_inmediato, faltante_horizonte, compra_abierta) - compra_abierta


def ajustar_plan(plan: list[str], hay_devoluciones: bool, hay_reposiciones: bool,
                 hay_compras: bool) -> list[str]:
    """Quita del plan los pasos que no tienen trabajo en este ciclo."""
    omitir = set()
    if not hay_devoluciones:
        omitir.add("registrar_devoluciones")
    if not hay_reposiciones:
        omitir.add("registrar_reposiciones")
    if not hay_compras:
        omitir.add("solicitar_compra")
    return [paso for paso in plan if paso not in omitir]


def replanificar(pendientes: list[str], evento: str) -> list[str]:
    """Cambia los pasos pendientes cuando el entorno cambió durante la ejecución."""
    if evento == "central_insuficiente" and "solicitar_compra" not in pendientes:
        indice = pendientes.index("notificar_responsable")
        return pendientes[:indice] + ["solicitar_compra"] + pendientes[indice:]
    return pendientes
