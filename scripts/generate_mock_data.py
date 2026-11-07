"""Genera datos ficticios con las mismas columnas que los archivos de la empresa.

Marcas, productos y cifras son inventados: este es el conjunto que se publica en GitHub.
"""
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

random.seed(42)

INICIO, FIN = date(2026, 6, 1), date(2026, 10, 30)
DIAS = (FIN - INICIO).days + 1
SALIDA = Path("data/muestra")
SUCURSALES = {14: "14 TIENDA DISEÑADOR", 15: "15 TIENDA ARABES", 37: "16 ONLINE"}
MARCAS = {
    "ARABES / DUPES": ["AL NOOR", "DUNA REAL", "OASIS", "SAFAR"],
    "DISEÑADOR": ["AURUM", "MAISON LUNE", "VERDANT", "CASA NOVA"],
    "NICHO": ["ATELIER NORTE", "BOTANICA"],
}
NOMBRES = ["NOCHE", "BRISA", "CEDRO", "VAINILLA", "AMBAR", "ORQUIDEA", "MIRRA", "CITRICO",
           "ROSA", "INCIENSO", "JAZMIN", "SANDALO", "MUSGO", "PIMIENTA", "COCO"]

# Productos fijos para demostrar cada regla. Rangos en días: (primero, último).
# ventas = {caja: cada cuántos días vende, primer día, último día}
ESCENARIOS = [
    # (código, nicho, b14, b15, b16, central, ventas)
    ("QUIEBRE15", "ARABES / DUPES", 0, 0, 0, 200, {15: (1, 0, DIAS)}),
    ("CUBIERTO14", "DISEÑADOR", 30, 0, 0, 100, {14: (5, 0, DIAS)}),
    ("LENTO15", "ARABES / DUPES", 0, 5, 0, 50, {15: (10, 0, 30)}),
    ("NOVENDE14", "DISEÑADOR", 4, 0, 0, 20, {}),
    ("ESCASO", "ARABES / DUPES", 0, 0, 0, 6, {15: (2, 0, DIAS), 14: (3, 0, DIAS), 37: (2, 0, DIAS)}),
    ("AGOTADO15", "ARABES / DUPES", 0, 1, 0, 0, {15: (2, 0, DIAS)}),
    ("ONLINE1", "DISEÑADOR", 0, 0, 2, 500, {37: (1, 0, DIAS)}),
    ("MERMA14", "DISEÑADOR", 0, 0, 0, 12, {14: (1, 0, DIAS)}),
]


def producto_fila(codigo, ean, nombre, marca, nicho, b14, b15, b16, total):
    return {"FAMILIA": "PERFUMERIA Y BELLEZA", "CATEGORIA": marca, "SUBFAMILIA": "PERFUMES",
            "CODIGO": codigo, "CODIGO BARRA": ean, "PRODUCTO": nombre,
            "B14": b14, "B15": b15, "B16": b16, "STOCK": total, "NICHO": nicho}


def linea_venta(caja, dia, folio, codigo, ean, nombre, marca, cantidad, precio, modulo="GUIA DESPACHO", signo=1):
    costo = round(precio * 0.6)
    return {"MODULO": modulo, "FECHA": INICIO + timedelta(days=dia), "FOLIO": folio,
            "SUCURSAL": SUCURSALES[caja], "CAJA": caja, "CODIGO": codigo, "COD ALT": ean,
            "DESCRIPCION": nombre, "MARCA": marca, "CANT": cantidad,
            "COSTO": signo * costo * cantidad, "VENTA": signo * precio * cantidad,
            "UTILIDAD": signo * (precio - costo) * cantidad}


stock, ventas = [], []
folio = 1000

for i, (codigo, nicho, b14, b15, b16, central, patron) in enumerate(ESCENARIOS):
    ean = str(7800000000000 + i)
    marca = random.choice(MARCAS[nicho])
    nombre = f"PERFUME {marca} {codigo} UNISEX EDP 100 ML"
    stock.append(producto_fila(codigo, ean, nombre, marca, nicho, b14, b15, b16, b14 + b15 + b16 + central))
    for caja, (cada, desde, hasta) in patron.items():
        for dia in range(desde, hasta, cada):
            folio += 1
            ventas.append(linea_venta(caja, dia, folio, codigo, ean, nombre, marca, 1, 25000))

for i in range(120):
    nicho = random.choices(list(MARCAS), weights=[5, 4, 1])[0]
    marca = random.choice(MARCAS[nicho])
    nombre_corto = f"{random.choice(NOMBRES)} {random.choice(NOMBRES)}"
    codigo = f"SKU{i:03d}"
    ean = str(7801000000000 + i)
    nombre = f"PERFUME {marca} {nombre_corto} {random.choice(['HOMBRE', 'MUJER', 'UNISEX'])} EDP 100 ML"
    precio = random.choice([15000, 19000, 25000, 32000, 45000, 69000])
    caja_principal = {"ARABES / DUPES": 15, "DISEÑADOR": 14, "NICHO": 14}[nicho]
    ritmos = {caja_principal: random.uniform(0.02, 0.5), 37: random.uniform(0.02, 0.6)}
    b14 = random.randint(0, 6) if caja_principal == 14 else 0
    b15 = random.randint(0, 8) if caja_principal == 15 else 0
    b16 = random.choice([0, 0, 0, 1, 2])
    central = random.randint(0, 120)
    stock.append(producto_fila(codigo, ean, nombre, marca, nicho, b14, b15, b16, b14 + b15 + b16 + central))
    for caja, ritmo in ritmos.items():
        for dia in range(DIAS):
            if random.random() < ritmo:
                folio += 1
                ventas.append(linea_venta(caja, dia, folio, codigo, ean, nombre, marca,
                                          random.choice([1, 1, 1, 2]), precio))

# Casos que la limpieza debe resolver, igual que en los datos de la empresa.
base = stock[10]
datos = (base["CODIGO"], base["CODIGO BARRA"], base["PRODUCTO"], base["CATEGORIA"])
ventas.append(linea_venta(14, 50, 90001, *datos, 40, 20000, modulo="COTIZACION"))
ventas.append(linea_venta(15, 60, 90002, *datos, 30, 15000))
ventas.append(linea_venta(37, 70, 90003, *datos, 1, 20000, signo=-1))
ventas.append(linea_venta(37, 71, 90004, "PRUEBA", None, "PRUEBA TIENDA ONLINE", "OTROS", 1, 1000))
ventas.append(linea_venta(37, 72, 90005, "NO_EXISTE", None, "PERFUME DESCONTINUADO", "OTROS", 3, 9000))

SALIDA.mkdir(parents=True, exist_ok=True)
pd.DataFrame(stock).to_excel(SALIDA / "stock_simulado.xlsx", index=False, sheet_name="STOCK")
tabla = pd.DataFrame(ventas)
with pd.ExcelWriter(SALIDA / "ventas_simuladas.xlsx") as archivo:
    for caja in (14, 15, 37):
        tabla[tabla["CAJA"] == caja].to_excel(archivo, sheet_name=f"CAJA {caja}", index=False)

print(f"Generados {len(stock)} productos y {len(ventas)} líneas de venta en {SALIDA}/")
