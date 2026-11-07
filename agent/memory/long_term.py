"""Memoria de largo plazo: persistencia en SQLite, sobrevive entre sesiones."""
import json
from datetime import date, timedelta

from agent import demanda
from agent.db import conectar
from config import settings


def guardar_ciclo(ciclo: str, local: int, fecha: date, resumen: dict,
                  con_pedido: bool) -> None:
    """Guarda qué decidió el agente en un ciclo de planificación."""
    conn = conectar()
    conn.execute(
        "INSERT INTO ciclos (ciclo, local, fecha, con_pedido, resumen) VALUES (?, ?, ?, ?, ?)",
        (ciclo, local, fecha.isoformat(), int(con_pedido),
         json.dumps(resumen, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


def ultimo_ciclo(local: int) -> dict | None:
    """Recupera el ciclo anterior del local, aunque se haya reiniciado la aplicación."""
    conn = conectar()
    fila = conn.execute(
        "SELECT * FROM ciclos WHERE local = ? ORDER BY id DESC LIMIT 1", (local,)
    ).fetchone()
    conn.close()
    if not fila:
        return None
    return {**dict(fila), "resumen": json.loads(fila["resumen"])}


def frecuencia_cumplida(local: int, fecha: date) -> str | None:
    """Revisa si el local ya hizo los pedidos que le corresponden en este período."""
    conn = conectar()
    if settings.LOCALES[local]["tipo"] == "online":
        inicio = demanda.inicio_de_quincena(fecha)
        limite, periodo = 1, f"esta quincena (próxima: {demanda.fin_de_quincena(fecha) + timedelta(days=1)})"
    else:
        inicio = fecha - timedelta(days=6)
        limite, periodo = 2, "los últimos 7 días"
    hechos = conn.execute(
        "SELECT COUNT(*) FROM ciclos WHERE local = ? AND con_pedido = 1 AND fecha >= ? AND fecha <= ?",
        (local, inicio.isoformat(), fecha.isoformat()),
    ).fetchone()[0]
    conn.close()
    if hechos >= limite:
        return f"Ya se hicieron {hechos} pedido(s) en {periodo}"
    return None


def solicitudes(estados: tuple[str, ...] = ("en_transito", "pendiente_compra"),
                local: int | None = None) -> list[dict]:
    """Lista las solicitudes con el nombre del producto."""
    marcas = ",".join("?" for _ in estados)
    sql = (
        "SELECT s.id, s.ciclo, s.tipo, s.local, s.codigo, p.producto, s.cantidad, "
        "s.estado, s.razon, s.fecha FROM solicitudes s "
        f"JOIN productos p ON p.codigo = s.codigo WHERE s.estado IN ({marcas})"
    )
    parametros = list(estados)
    if local is not None:
        sql += " AND s.local = ?"
        parametros.append(local)
    conn = conectar()
    filas = conn.execute(sql + " ORDER BY s.id", parametros).fetchall()
    conn.close()
    return [dict(f) for f in filas]
