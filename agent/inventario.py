"""Consultas a la base de datos para conocer stock, ventas y solicitudes abiertas."""
from datetime import date, timedelta

from agent import demanda
from agent.db import conectar
from config import settings


def periodo_ventas(conn) -> tuple[date, int]:
    """Devuelve la última fecha con ventas y los días que cubre el período."""
    ultima = conn.execute("SELECT MAX(fecha) FROM ventas").fetchone()[0]
    corte = date.fromisoformat(ultima)
    inicio = date.fromisoformat(settings.INICIO_VENTAS)
    return corte, (corte - inicio).days + 1


def ventas_por_producto(conn, local: int) -> dict[str, dict]:
    """Calcula por producto la venta diaria normal y si tuvo movimiento reciente."""
    corte, dias = periodo_ventas(conn)
    desde = (corte - timedelta(days=settings.DIAS_SIN_MOVIMIENTO - 1)).isoformat()
    filas = conn.execute(
        "SELECT codigo, "
        "SUM(CASE WHEN mayorista = 0 THEN unidades ELSE 0 END) AS normales, "
        "SUM(CASE WHEN fecha >= ? THEN unidades ELSE 0 END) AS recientes, "
        "SUM(unidades) AS totales "
        "FROM ventas WHERE local = ? GROUP BY codigo",
        (desde, local),
    ).fetchall()
    return {
        f["codigo"]: {
            "venta_diaria": max(f["normales"], 0) / dias,
            "unidades": f["totales"],
            "activo": f["recientes"] > 0,
        }
        for f in filas
    }


def solicitudes_en_curso(conn) -> dict[tuple, int]:
    """Suma lo abierto por (tipo, local, código): lo que aún no se ha recibido."""
    filas = conn.execute(
        "SELECT tipo, local, codigo, SUM(cantidad) AS cantidad FROM solicitudes "
        "WHERE estado IN ('en_transito', 'pendiente_compra') "
        "GROUP BY tipo, local, codigo"
    ).fetchall()
    return {(f["tipo"], f["local"], f["codigo"]): f["cantidad"] for f in filas}


def central_disponible(conn, codigo: str) -> int:
    """Stock de la central: total menos bodegas de tienda menos lo ya comprometido."""
    fila = conn.execute(
        "SELECT total - b14 - b15 - b16 AS central FROM stock WHERE codigo = ?", (codigo,)
    ).fetchone()
    if not fila:
        return 0
    comprometido = conn.execute(
        "SELECT COALESCE(SUM(cantidad), 0) FROM solicitudes "
        "WHERE tipo = 'reposicion' AND estado = 'en_transito' AND codigo = ?",
        (codigo,),
    ).fetchone()[0]
    return max(fila["central"] - comprometido, 0)


def estados_local(local: int, fecha: date, solo_codigos: list[str] | None = None) -> list[dict]:
    """Reúne lo que el planner necesita saber de cada producto del local."""
    datos_local = settings.LOCALES[local]
    bodega, tipo, lineas = datos_local["bodega"], datos_local["tipo"], datos_local["lineas"]
    conn = conectar()
    ventas = {otro: ventas_por_producto(conn, otro) for otro in settings.LOCALES}
    en_curso = solicitudes_en_curso(conn)
    comprometido = {}
    for (tipo_sol, _, codigo), cantidad in en_curso.items():
        if tipo_sol == "reposicion":
            comprometido[codigo] = comprometido.get(codigo, 0) + cantidad
    filas = conn.execute(
        f"SELECT p.codigo, p.producto, p.marca, p.nicho, s.{bodega} AS stock_local, "
        "s.total, MAX(s.total - s.b14 - s.b15 - s.b16, 0) AS central "
        "FROM stock s JOIN productos p ON p.codigo = s.codigo"
    ).fetchall()
    conn.close()

    estados = []
    for fila in filas:
        codigo = fila["codigo"]
        venta = ventas[local].get(codigo)
        if solo_codigos is not None and codigo not in solo_codigos:
            continue
        if venta is None and fila["stock_local"] <= 0:
            continue
        venta_diaria = venta["venta_diaria"] if venta else 0.0
        activo = bool(venta and venta["activo"] and venta_diaria > 0)
        en_linea = lineas is None or fila["nicho"] in lineas
        proyeccion_total = sum(
            demanda.proyeccion_hasta_fin(v[codigo]["venta_diaria"], fecha)
            for v in ventas.values()
            if codigo in v and v[codigo]["activo"]
        )
        estados.append({
            "codigo": codigo,
            "producto": fila["producto"],
            "marca": fila["marca"],
            "nicho": fila["nicho"],
            "stock_local": fila["stock_local"],
            "stock_total": fila["total"],
            "central": max(fila["central"] - comprometido.get(codigo, 0), 0),
            "en_transito": en_curso.get(("reposicion", local, codigo), 0),
            "devolucion_abierta": ("devolucion", local, codigo) in en_curso,
            "compra_abierta": en_curso.get(("compra", 0, codigo), 0),
            "venta_diaria": venta_diaria,
            "unidades_periodo": venta["unidades"] if venta else 0,
            "activo": activo,
            "con_movimiento": bool(venta and venta["activo"]),
            "en_linea": en_linea,
            "tipo_local": tipo,
            "objetivo": demanda.objetivo(tipo, venta_diaria, fecha) if activo and en_linea else 0,
            "proyeccion_total": proyeccion_total,
        })
    return estados


def resumen_stock_local(local: int) -> dict:
    """Totales de la bodega de un local."""
    bodega = settings.LOCALES[local]["bodega"]
    conn = conectar()
    fila = conn.execute(
        f"SELECT COUNT(CASE WHEN {bodega} > 0 THEN 1 END) AS productos, "
        f"COALESCE(SUM({bodega}), 0) AS unidades, "
        "COALESCE(SUM(MAX(total - b14 - b15 - b16, 0)), 0) AS central FROM stock"
    ).fetchone()
    conn.close()
    return dict(fila)


def buscar_productos(consulta: str, limite: int = 5) -> list[dict]:
    """Busca por código exacto, EAN exacto o palabras del nombre."""
    consulta = consulta.strip()
    conn = conectar()
    base = (
        "SELECT p.codigo, p.ean, p.producto, p.nicho, s.b14, s.b15, s.b16, s.total, "
        "MAX(s.total - s.b14 - s.b15 - s.b16, 0) AS central "
        "FROM productos p JOIN stock s ON s.codigo = p.codigo "
    )
    filas = conn.execute(
        base + "WHERE UPPER(p.codigo) = UPPER(?) OR p.ean = ?", (consulta, consulta)
    ).fetchall()
    if not filas:
        palabras = [p for p in consulta.split() if p]
        condicion = " AND ".join(["p.producto LIKE ?"] * len(palabras)) or "1 = 0"
        filas = conn.execute(
            base + f"WHERE {condicion} ORDER BY s.total DESC LIMIT ?",
            [f"%{p}%" for p in palabras] + [limite],
        ).fetchall()
    conn.close()
    return [dict(f) for f in filas]
