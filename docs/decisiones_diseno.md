# Decisiones de diseño

La pauta prohíbe usar IA para redactar justificaciones técnicas. Esta tabla reúne solo hechos y evidencia.
**La última sección la deben escribir Leonardo y Francisco con sus propias palabras.**

## Hechos para respaldar cada decisión

| Decisión | Alternativa | Hecho o evidencia |
|---|---|---|
| LangChain `AgentExecutor` | Otros frameworks; Francisco usó LangGraph | Es lo que indica la guía; ver `requirements.txt` |
| LangChain 1.x con `langchain-classic` y `langchain-google-genai` 4 | LangChain menor a 1.0 (guía) | Con la versión de la guía, los modelos Gemini 3 probados con tools fallan con error 400 por falta de `thought_signature` |
| Gemini Flash | Modelo local con Ollama (trabajo de Francisco) | Gemini: nivel gratuito sin descargar modelos. Ollama: varios GB, pero los datos no salen del equipo |
| `gemini-3.6-flash` con respaldo `gemini-3.5-flash-lite` | `gemini-3.8-flash` (guía) | Al probar, `gemini-3.8-flash` respondió 503 o agotó el tiempo; test `test_si_el_modelo_principal_falla_usa_el_respaldo` |
| Elegir entre Gemini y Claude en el panel | Un solo proveedor | `crear_llm` en `agent/core.py`; el resto del agente no cambia. Test `test_el_panel_puede_elegir_claude`; comparar `evidence/conversacion_gemini.json` y `evidence/conversacion_claude.json` |
| Panel con 4 modelos de Claude y 7 de Gemini | Un modelo fijo por proveedor | `config/settings.py`; los 11 respondieron una prueba directa el 6-nov-2026, salvo 3.7 Flash y 3.8 Flash, saturados en ese momento |
| Gemini prueba el siguiente modelo si uno falla; Claude no | El mismo comportamiento en ambos | Gemini es gratis y se satura; Claude es de pago. Test `test_si_gemini_se_queda_sin_cuota_usa_el_siguiente` |
| Iniciador que instala, pide las keys y abre el agente | Instrucciones manuales | `iniciar.bat` y `scripts/iniciar.py`; tests en `tests/test_iniciar.py` |
| Si un proveedor falla, pasar a reglas y no al otro | Probar con el otro proveedor | Los proveedores tienen condiciones de datos distintas. Test `test_si_claude_falla_no_envia_los_datos_a_gemini` |
| Decisión con reglas; LLM solo para conversar | Dejar que el LLM decida los pedidos | Tests `test_el_llm_no_tiene_tools_de_escritura_directa` y `test_pedido_del_llm_pasa_por_las_reglas` |
| Modo de reglas si falla Gemini | Mostrar un error | Test `test_si_el_llm_falla_sigue_con_reglas` |
| Modelo de embeddings multilingüe | `all-MiniLM-L6-v2` (guía) | `evidence/eval_embeddings.md` |
| Un fragmento por regla | Un fragmento por sección (guía) | `evidence/eval_embeddings.md` |
| Venta diaria con el promedio del período | Últimos 60 días, o el mayor de ambos | Comparación contra octubre con datos de la empresa, no publicada |
| Excluir líneas de 10 o más unidades de la demanda | Contarlas | Confirmado por el negocio: son ventas mayoristas esporádicas |
| Cada tienda repone solo su línea; lo demás se vende hasta agotarse | Devolver de inmediato lo de otra línea | Confirmado por el negocio: la venta migra de a poco a la tienda de su línea |
| Bodega central calculada como total − B14 − B15 − B16 | Usar `STOCK` directo | En los datos, `STOCK` casi siempre es mayor o igual a la suma de bodegas |
| SQLite y Chroma locales | Servicios en la nube | No requieren instalación aparte ni enviar datos |
| Publicar los datos reales en `data/reales` | Solo datos simulados | La empresa autorizó su uso; cualquiera que descargue el proyecto puede probarlo con datos reales. Las pruebas usan los simulados |
| Con datos reales, LLM apagado salvo autorización expresa | Enviarlos siempre a Gemini | En el nivel gratuito, Google indica que el contenido se usa para mejorar sus productos; las tools no entregan costos ni montos |

## Diferencias con la guía

| Guía TechStore | Este proyecto |
|---|---|
| Devoluciones de clientes | Reposición de stock |
| 40 pedidos ficticios | Ventas y stock reales de la empresa, más datos simulados para las pruebas |
| 6 reglas de devolución | 7 reglas de reposición |
| `buscar_casos_similares` no se usa en el flujo principal | `buscar_politicas` se usa para citar la fuente |
| La memoria de corto plazo no se conecta al flujo | Se usa en la conversación |
| La memoria semántica es estática | El agente agrega cada ciclo como un caso |
| Sin idempotencia | Recuerda lo que viene en camino y no lo pide de nuevo |
| LangChain menor a 1.0 | LangChain 1.x, porque la versión de la guía falla con Gemini 3 y tools |

## Justificación del equipo (redactar sin IA)

Expliquen con sus palabras por qué eligieron cada componente y cómo responde al flujo de trabajo:

- Framework y LLM:
- Separación entre reglas y LLM:
- Memoria (corto plazo, largo plazo, semántica):
- Planificación y prioridades:
- Almacenamiento:
- Interfaz:
