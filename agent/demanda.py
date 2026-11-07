"""Proyección de demanda. Son funciones puras: mismos datos, mismo resultado."""
import calendar
import math
from datetime import date, timedelta

from config import settings


def factor_temporada(dia: date) -> float:
    """Devuelve 1,5 en temporada alta y 1,0 el resto del tiempo."""
    return settings.FACTOR_PICO if settings.PICO_INICIO <= dia <= settings.PICO_FIN else 1.0


def dias_equivalentes(inicio: date, dias: int) -> float:
    """Suma los factores de cada día: un día de temporada alta vale 1,5 días normales."""
    return sum(factor_temporada(inicio + timedelta(days=i)) for i in range(dias))


def fin_de_quincena(dia: date) -> date:
    """Último día de la quincena: la bodega online se repone dos veces al mes."""
    if dia.day <= 15:
        return dia.replace(day=15)
    return dia.replace(day=calendar.monthrange(dia.year, dia.month)[1])


def inicio_de_quincena(dia: date) -> date:
    return dia.replace(day=1 if dia.day <= 15 else 16)


def objetivo_tienda(venta_diaria: float, fecha: date) -> int:
    """Stock para 7 días de venta más los 2 días que demora la reposición."""
    dias = settings.DIAS_COBERTURA_TIENDA + settings.DIAS_REPOSICION
    return math.ceil(venta_diaria * dias_equivalentes(fecha, dias))


def objetivo_online(venta_diaria: float, fecha: date) -> int:
    """Stock para vender hasta fin de quincena, con mínimo de una unidad de surtido."""
    dias = (fin_de_quincena(fecha) - fecha).days + 1
    return max(round(venta_diaria * dias_equivalentes(fecha, dias)), 1)


def objetivo(tipo: str, venta_diaria: float, fecha: date) -> int:
    if tipo == "online":
        return objetivo_online(venta_diaria, fecha)
    return objetivo_tienda(venta_diaria, fecha)


def proyeccion_hasta_fin(venta_diaria: float, fecha: date) -> float:
    """Unidades que se espera vender desde la fecha hasta el fin del horizonte."""
    dias = (settings.FIN_HORIZONTE - fecha).days + 1
    return venta_diaria * dias_equivalentes(fecha, max(dias, 0))
