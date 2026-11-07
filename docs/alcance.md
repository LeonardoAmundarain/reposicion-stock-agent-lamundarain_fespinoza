# Alcance del agente de reposición

## Requerimiento organizacional

Una perfumería con dos tiendas y un canal online abastece sus locales desde una bodega central.
Decidir a mano qué pedir, qué devolver y qué comprar exige cruzar miles de productos. El agente
automatiza ese flujo de cara a la temporada alta de noviembre y diciembre.

Este proyecto continúa la EP1, donde un agente solo consultaba información de ventas ya calculada y la
explicaba en lenguaje natural. Ahora el agente también razona con reglas, planifica y registra acciones.

## Locales

| Local | Línea | Vende por | Bodega | Cómo se repone |
|---|---|---|---|---|
| 14 | Tienda diseñador | Caja 14 | B14 | 1 o 2 veces por semana, 2 días de demora |
| 15 | Tienda árabes | Caja 15 | B15 | 1 o 2 veces por semana, 2 días de demora |
| 16 | Online, todos los productos | Caja 37 | B16 | 2 veces al mes |

La bodega central tiene el stock total (columna `STOCK`) menos lo que hay en B14, B15 y B16.

## Lo que SÍ hace

- Limpia las ventas y las cruza con el stock por código o EAN.
- Proyecta la demanda considerando la temporada alta (1,5 veces entre el 16 de noviembre y el 21 de diciembre).
- Sugiere reposiciones solo de lo que cada local vende y, en las tiendas, solo de su línea.
- Propone devolver a la central lo que no tiene movimiento en 60 días.
- Solicita comprar lo que la central no alcanza a cubrir hasta fin de diciembre.
- Evalúa pedidos puntuales de una tienda, sin monto tope, pero solo si son requeridos.
- Recuerda ciclos y solicitudes entre sesiones, y retoma lo pendiente cuando llega una compra.
- Conversa en lenguaje natural y explica sus decisiones citando la política.

## Lo que NO hace

- No mueve mercadería ni emite órdenes de compra reales: todo queda como solicitud simulada.
- No se conecta al sistema de la empresa: trabaja con archivos exportados.
- No detecta productos descontinuados: una persona debe revisar la lista de compra.
- No sugiere productos nuevos que un local nunca ha vendido.
- No aplica la cobertura según el tamaño físico de cada tienda.
- No reemplaza a la persona responsable: la compra siempre espera su confirmación.

## Limitaciones conocidas

- Una venta en cero por falta de stock parece falta de demanda, porque no hay historial de quiebres.
- El factor de temporada y sus fechas son una estimación del negocio, no se calcularon con datos de años anteriores.
- La venta de un producto que migra de tienda no se suma aún al objetivo de la tienda que lo recibirá.
- La venta de un producto puntual es difícil de predecir; el total de cada local es más confiable.
- La búsqueda semántica no siempre acierta (ver `evidence/eval_embeddings.md`); por eso las reglas no dependen de ella.

## Métricas de éxito de la demo

- Un ciclo de reposición de un local termina en menos de 30 segundos.
- Al menos 4 escenarios de decisión distintos se muestran en 10 minutos.
