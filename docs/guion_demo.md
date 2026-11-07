# Guion de demostración: 10 minutos

Antes de partir, pulsa **Reiniciar demo** en la barra lateral. Este guion usa los datos simulados de `data/muestra`
(`FUENTE_DATOS=simulado`); con los datos reales, las cifras y los códigos son otros.

Los roles y tiempos son una propuesta: ajústenlos al ensayar.

## 0:00 a 1:00. Contexto (Leonardo)

- El problema: reponer miles de productos para noviembre y diciembre.
- La continuidad con la EP1: de un agente que solo consultaba a uno que decide y registra.

## 1:00 a 3:30. Ciclo normal en una tienda (Leonardo). IE1, IE5

Local 15, fecha 2026-11-03, **Planificar reposición**.

- `QUIEBRE15`: sin stock, prioridad 1, repone 9 (7 días + 2 de demora).
- `LENTO15`: sin ventas en 60 días, se devuelve a la central.
- `AGOTADO15`: la central no tiene, se solicita comprar.
- Abrir **Plan y razonamiento** y **Políticas recuperadas**.

**Punto clave:** cada acción muestra su razón y la política que la respalda.

## 3:30 a 5:00. Memoria (Francisco). IE3, IE4

Cambiar la fecha a 2026-11-04 y planificar de nuevo el local 15.

- `QUIEBRE15` queda cubierto: el agente recuerda las 9 unidades en camino.
- No repite compras ni devoluciones.
- En **Conversar**: «planifica la tienda de árabes» y luego «cuál es el estado de las solicitudes».

**Punto clave:** el segundo mensaje no menciona el local, y el agente lo recuerda.

## 5:00 a 6:30. Condiciones cambiantes (Francisco). IE5, IE7

1. **Temporada alta:** reiniciar, fecha 2026-11-20, local 15. `QUIEBRE15` pasa de 9 a 14 unidades.
2. **Durante la ejecución:** reiniciar, local 14, simular `MERMA14:8`. El agente repone 4 y compra lo que falta.

**Punto clave:** el plan cambia mientras se ejecuta, no solo al comienzo.

## 6:30 a 8:00. Decisiones sin monto tope y retomar tareas (Leonardo). IE7

1. **Pedido de tienda:** reiniciar y pedir 50 de `QUIEBRE15` en el local 15. Se aprueba solo lo requerido. Pedir otra vez: se rechaza.
2. **Solicitudes abiertas:** planificar el local 15 y confirmar la compra de `AGOTADO15`. El agente retoma la reposición por su cuenta.

## 8:00 a 10:00. Arquitectura y evidencia (ambos). IE8, IE9, IE10

- Diagrama de orquestación.
- `pytest` en verde y `evidence/eval_embeddings.md`.
- Por qué el LLM no tiene acceso directo a las tools de escritura.
- Qué hace el agente si Gemini falla.

## Plan B

- Si Gemini está saturado: el agente pasa solo a su modelo de respaldo y, si también falla, al modo de reglas.
- Si Claude falla: el agente pasa al modo de reglas; también puedes elegir el otro proveedor en el panel.
- Sin internet: el modo de reglas sigue funcionando. Abre la aplicación con la variable `HF_HUB_OFFLINE=1`.
- Si falla la aplicación: video de respaldo y `evidence/escenarios.json`.
