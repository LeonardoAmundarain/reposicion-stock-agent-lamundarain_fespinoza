# Reglas de decisión

## Decisión por producto (`agent/planner.py`)

Las reglas se evalúan en orden y la primera que se cumple decide.

| # | Condición | Acción | Razón |
|---|---|---|---|
| Previa | Ya hay una devolución en camino | `en_curso` | No repetir trabajo |
| 1 | Tienda con stock y sin movimiento en 60 días | `devolver_central` | Liberar espacio |
| 2 | Tienda y producto de otra línea | `fuera_de_linea` | La venta migra de a poco: se vende hasta agotarse |
| 3 | El local no vende el producto | `sin_accion` | Solo se repone lo que se vende |
| 4 | Stock + en camino cubre el objetivo | `cubierto` | La solicitud no es requerida |
| 5 | La central cubre toda la necesidad | `reponer` | Flujo normal |
| 6 | La central cubre una parte | `reponer_parcial` | Enviar lo que hay y comprar el resto |
| 7 | La central no tiene unidades | `sin_stock_central` | Solicitar compra |

La línea sale de la columna `NICHO`: la tienda 14 repone `DISEÑADOR`, la 15 `ARABES / DUPES` y online todas.

## Objetivos de stock (`agent/demanda.py`)

- **Venta diaria:** unidades normales del período ÷ días del período.
- **Tienda:** venta diaria × días equivalentes de los próximos 9 días (7 de cobertura + 2 de demora).
- **Online:** venta diaria × días equivalentes hasta fin de quincena, con mínimo de 1 unidad.
- **Días equivalentes:** cada día de temporada alta vale 1,5.

## Compra

`max(faltante inmediato, venta proyectada hasta fin de diciembre − stock total, compra abierta) − compra abierta`

## Prioridad de atención

| Prioridad | Condición |
|---|---|
| 1 | Sin stock ni unidades en camino |
| 2 | El stock se acaba antes de que llegue la reposición |
| 3 | El resto |

Dentro de una misma prioridad se atiende primero el producto de mayor venta diaria.
Las tiendas se planifican antes que online porque su necesidad es de la semana.

## Frecuencia

- **Tiendas:** máximo 2 pedidos cada 7 días.
- **Online:** 1 pedido por quincena.
- La recepción de una compra permite un pedido extra de ese producto, sin consumir la frecuencia.

## Pedido manual de una tienda

| Caso | Resultado |
|---|---|
| No vende ni tiene el producto, o ya está cubierto | Rechazado: no es requerido |
| El producto es de otra línea | Rechazado: esa tienda ya no lo repone |
| Pide lo requerido o menos | Aprobado, sin monto tope |
| Pide más de lo requerido | Se aprueba solo lo requerido |
| La central no alcanza | Se aprueba lo disponible y el resto pasa a compra |

## Limpieza de ventas

| Registro | Tratamiento |
|---|---|
| Módulo `COTIZACION` | Se excluye |
| Descripción que parte con `PRUEBA` | Se excluye |
| Fecha anterior al período | Se excluye |
| Venta en cero | Se excluye |
| Venta negativa | Resta unidades: es una devolución de cliente |
| Línea de 10 o más unidades | No cuenta como demanda, pero sí como movimiento |
| Código sin cruce con el stock | Se busca por EAN; si no calza, queda en un reporte |
