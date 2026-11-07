"""Planifica todos los locales y guarda un Excel. Pensado para los datos reales.

Uso: python -m scripts.exportar_resultados C:/ruta/privada/sugeridos.xlsx [AAAA-MM-DD]
El archivo contiene cifras de la empresa: guárdalo fuera del repositorio.
"""
import sys
from pathlib import Path

import pandas as pd

from agent.core import planificar_todo
from agent.db import conectar
from agent.memory.semantic import borrar_casos_aprendidos
from config import settings
from scripts.seed_data import sembrar

COLUMNAS = ["prioridad", "codigo", "producto", "marca", "nicho", "venta_diaria", "stock_local",
            "en_transito", "central", "objetivo", "cantidad", "razon"]


def main(ruta: str, fecha: str | None = None) -> None:
    destino = Path(ruta).resolve()
    if settings.BASE_DIR in destino.parents:
        sys.exit("Guarda el archivo fuera del repositorio.")
    resumen = sembrar()
    borrar_casos_aprendidos()
    resultados = planificar_todo(fecha or settings.FECHA_PLAN)["resultados"]
    filas_resumen = []
    with pd.ExcelWriter(destino) as archivo:
        for local, resultado in resultados.items():
            tabla = pd.DataFrame(resultado["lineas"])
            nombre = settings.LOCALES[local]["nombre"]
            reponer = tabla[tabla["accion"].isin(["reponer", "reponer_parcial"])]
            devolver = tabla[tabla["accion"] == "devolver_central"]
            fuera = tabla[tabla["accion"] == "fuera_de_linea"]
            reponer[COLUMNAS].to_excel(archivo, sheet_name=f"Reponer {local}", index=False)
            if settings.LOCALES[local]["tipo"] == "tienda":
                devolver[COLUMNAS].to_excel(archivo, sheet_name=f"Devolver {local}", index=False)
                fuera[COLUMNAS].to_excel(archivo, sheet_name=f"Fuera de linea {local}", index=False)
            filas_resumen.append({
                "local": local, "nombre": nombre,
                "productos_a_reponer": len(reponer), "unidades_a_reponer": int(reponer["cantidad"].sum()),
                "productos_a_devolver": len(devolver), "unidades_a_devolver": int(devolver["cantidad"].sum()),
                "productos_cubiertos": int((tabla["accion"] == "cubierto").sum()),
                "productos_fuera_de_linea": len(fuera),
                "sin_stock_en_central": int((tabla["accion"] == "sin_stock_central").sum()),
                "unidades_a_comprar": resultado["compras"],
            })
        conn = conectar()
        compras = pd.read_sql(
            "SELECT s.codigo, p.producto, p.marca, p.nicho, s.cantidad, st.total AS stock_total, s.razon "
            "FROM solicitudes s JOIN productos p ON p.codigo = s.codigo "
            "JOIN stock st ON st.codigo = s.codigo WHERE s.tipo = 'compra' ORDER BY s.cantidad DESC", conn)
        sin_cruce = pd.read_sql("SELECT * FROM sin_cruce ORDER BY unidades DESC", conn)
        conn.close()
        compras.to_excel(archivo, sheet_name="Solicitar compra", index=False)
        sin_cruce.to_excel(archivo, sheet_name="Ventas sin cruce", index=False)
        pd.DataFrame(filas_resumen).to_excel(archivo, sheet_name="Resumen", index=False)
        pd.DataFrame([resumen]).T.reset_index().to_excel(archivo, sheet_name="Limpieza", index=False, header=False)
    print(pd.DataFrame(filas_resumen).to_string(index=False))
    print(f"Compra total: {int(compras['cantidad'].sum())} unidades en {len(compras)} productos")
    print(f"Guardado en {destino}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
