# Herramientas del agente

## Las 7 tools (`agent/tools/`)

| Tool | Tipo | Entrada | Salida | Uso en el flujo |
|---|---|---|---|---|
| `consultar_stock` | Consulta | `consulta` o `local` | Bodegas y central, o resumen del local | Conocer la situación actual |
| `consultar_ventas` | Consulta | `local`, `codigo`, `limite` | Unidades y venta diaria | Conocer la demanda |
| `proyectar_demanda` | Razonamiento | `local`, `codigo`, `fecha` | Factor, venta del período y hasta fin de diciembre | Anticipar la temporada |
| `buscar_politicas` | Consulta semántica | `texto` | Políticas y casos parecidos | Justificar y responder |
| `registrar_solicitudes` | Escritura | `ciclo`, `local`, `tipo`, `items`, `fecha` | Registradas y ajustes | Reposiciones y devoluciones |
| `solicitar_compra` | Escritura | `ciclo`, `items`, `fecha` | Registradas y unidades | Compras pendientes |
| `notificar_responsable` | Escritura simulada | `destino`, `mensaje` | `{ok, canal}` | Avisar el resultado |

## Tools disponibles para el LLM (`agent/core.py`)

El LLM recibe las consultas y tres tools con control. No recibe `registrar_solicitudes` ni
`solicitar_compra`, de modo que todo pedido pasa por las reglas del planner.

| Tool | Qué hace |
|---|---|
| `consultar_stock`, `consultar_ventas`, `proyectar_demanda`, `buscar_politicas` | Consultar y razonar |
| `planificar_reposicion` | Ejecuta un ciclo completo aplicando las reglas |
| `evaluar_pedido_tienda` | Aprueba solo lo requerido |
| `estado_solicitudes` | Lista lo que sigue abierto |

## Secuencia del plan

`recordar_ciclo_anterior` → `consultar_stock` → `consultar_ventas` → `proyectar_demanda` →
`decidir_por_producto` → `secuenciar_por_prioridad` → `buscar_politicas` → `registrar_devoluciones` →
`registrar_reposiciones` → `solicitar_compra` → `notificar_responsable` → `guardar_memoria`

El plan se ajusta en dos momentos:

- **Antes de escribir:** quita los pasos sin trabajo (`ajustar_plan`).
- **Durante la escritura:** si la central cambió, ajusta la cantidad y agrega la compra (`replanificar`).
