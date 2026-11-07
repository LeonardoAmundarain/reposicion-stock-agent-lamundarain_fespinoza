# Escenarios de demostración

Cómo reproducir cada decisión del agente en la interfaz. Usa los datos simulados de `data/muestra`
(`FUENTE_DATOS=simulado`); con los datos reales, las cifras y los códigos son otros. Antes de cada escenario, pulsa
**Reiniciar demo** en la barra lateral, salvo donde se indica seguir sin reiniciar.

Los mismos casos se ejecutan sin interfaz con `python -m scripts.demo_escenarios`, que deja el resultado en
`evidence/escenarios.json`.

## 1. Ciclo normal en una tienda (IE1, IE5)

Local 15, fecha 2026-11-03, **Planificar reposición**.

- `QUIEBRE15`: sin stock, prioridad 1, repone 9 (7 días de venta más 2 de demora).
- `LENTO15`: sin ventas en 60 días, se devuelve a la central.
- `AGOTADO15`: la central no tiene, se solicita comprar.

En **Plan y razonamiento** y **Políticas recuperadas** se ve la razón de cada acción y la política que la respalda.

## 2. Memoria (IE3, IE4)

Sin reiniciar, cambia la fecha a 2026-11-04 y planifica de nuevo el local 15.

- `QUIEBRE15` queda cubierto: el agente recuerda las 9 unidades en camino.
- No repite compras ni devoluciones.

En **Conversar**, escribe «planifica la tienda de árabes» y luego «cuál es el estado de las solicitudes». El segundo
mensaje no menciona el local y el agente lo recuerda.

## 3. Condiciones cambiantes (IE5, IE7)

- **Temporada alta:** local 15, fecha 2026-11-20. `QUIEBRE15` pasa de 9 a 14 unidades.
- **Cambio durante la ejecución:** local 14, simular `MERMA14:8`. El agente repone 4 y solicita comprar lo que falta.
  El plan cambia mientras se ejecuta, no solo al comienzo.

## 4. Pedidos de tienda y tareas pendientes (IE7)

- **Pedido de tienda:** pide 50 de `QUIEBRE15` en el local 15. Se aprueba solo lo requerido, 9 unidades. Si lo pides
  otra vez, se rechaza porque ya viene en camino.
- **Retomar una tarea:** planifica el local 15 y, en **Solicitudes**, pulsa **Confirmar recepción** en la compra de
  `AGOTADO15`. El agente
  retoma la reposición de ese producto por su cuenta.

## 5. Si el LLM no responde

- **Gemini:** si el modelo elegido está saturado o sin cuota, el agente prueba los siguientes de la lista y avisa cuál
  respondió. Si ninguno responde, sigue con el modo de reglas.
- **Claude:** si falla, el agente pasa al modo de reglas; no envía los datos a Gemini.
- **Sin internet:** el modo de reglas sigue funcionando. Abre la aplicación con la variable `HF_HUB_OFFLINE=1` para
  usar el modelo de embeddings ya descargado.
