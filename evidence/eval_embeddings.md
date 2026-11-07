# Evaluación de embeddings

17 preguntas en español, redactadas sin copiar las palabras de `data/politicas.md`.
Se mide si la sección esperada aparece en el primer resultado o entre los dos primeros.

| Modelo | Fragmentos | 1.er lugar | Entre los 2 primeros |
|---|---|---|---|
| `all-MiniLM-L6-v2` | por sección (9) | 6/17 | 10/17 |
| `all-MiniLM-L6-v2` | por regla (28) | 9/17 | 11/17 |
| `paraphrase-multilingual-MiniLM-L12-v2` | por sección (9) | 11/17 | 13/17 |
| `paraphrase-multilingual-MiniLM-L12-v2` | por regla (28) | 12/17 | 14/17 |

## Errores: `all-MiniLM-L6-v2`, por sección

- "en cuánto tiempo llega lo que pide un local": devolvió "Cálculo de la demanda", se esperaba "Reposición de tiendas"
- "cada cuánto puede pedir productos un local físico": devolvió "Cálculo de la demanda", se esperaba "Reposición de tiendas"
- "hay un límite de dinero para autorizar un pedido": devolvió "Cálculo de la demanda", se esperaba "Aprobación de solicitudes"
- "un local pidió más unidades de las que necesita": devolvió "Cálculo de la demanda", se esperaba "Aprobación de solicitudes"
- "qué hago con un perfume que nadie compra hace dos meses": devolvió "Compras", se esperaba "Devoluciones a bodega central"
- "cómo libero espacio en el local": devolvió "Prioridades cuando la bodega central no alcanza", se esperaba "Devoluciones a bodega central"
- "cuántas veces al mes se abastece la bodega de internet": devolvió "Prioridades cuando la bodega central no alcanza", se esperaba "Bodega online"
- "en qué fechas sube la venta por navidad": devolvió "Bodega online", se esperaba "Temporada alta"
- "cuánto más se vende en fin de año": devolvió "Cálculo de la demanda", se esperaba "Temporada alta"
- "no queda mercadería suficiente en la central para lo proyectado": devolvió "Reposición de tiendas", se esperaba "Compras"
- "cuándo se avisa a adquisiciones que falta producto": devolvió "Prioridades cuando la bodega central no alcanza", se esperaba "Compras"

## Errores: `all-MiniLM-L6-v2`, por regla

- "cada cuánto puede pedir productos un local físico": devolvió "Bodega online", se esperaba "Reposición de tiendas"
- "qué hago con un perfume que nadie compra hace dos meses": devolvió "Compras", se esperaba "Devoluciones a bodega central"
- "cómo libero espacio en el local": devolvió "Compras", se esperaba "Devoluciones a bodega central"
- "cuántas veces al mes se abastece la bodega de internet": devolvió "Prioridades cuando la bodega central no alcanza", se esperaba "Bodega online"
- "en qué fechas sube la venta por navidad": devolvió "Bodega online", se esperaba "Temporada alta"
- "no queda mercadería suficiente en la central para lo proyectado": devolvió "Reposición de tiendas", se esperaba "Compras"
- "qué producto tiene preferencia cuando hay poco": devolvió "Bodega online", se esperaba "Prioridades cuando la bodega central no alcanza"
- "se cuentan las ventas al por mayor para calcular cuánto pedir": devolvió "Compras", se esperaba "Cálculo de la demanda"

## Errores: `paraphrase-multilingual-MiniLM-L12-v2`, por sección

- "cada cuánto puede pedir productos un local físico": devolvió "Prioridades cuando la bodega central no alcanza", se esperaba "Reposición de tiendas"
- "un local pidió más unidades de las que necesita": devolvió "Cálculo de la demanda", se esperaba "Aprobación de solicitudes"
- "qué hago con un perfume que nadie compra hace dos meses": devolvió "Reposición de tiendas", se esperaba "Devoluciones a bodega central"
- "qué surtido mínimo debe tener la venta por internet": devolvió "Prioridades cuando la bodega central no alcanza", se esperaba "Bodega online"
- "no queda mercadería suficiente en la central para lo proyectado": devolvió "Devoluciones a bodega central", se esperaba "Compras"
- "cuándo se avisa a adquisiciones que falta producto": devolvió "Prioridades cuando la bodega central no alcanza", se esperaba "Compras"

## Errores: `paraphrase-multilingual-MiniLM-L12-v2`, por regla

- "cada cuánto puede pedir productos un local físico": devolvió "Prioridades cuando la bodega central no alcanza", se esperaba "Reposición de tiendas"
- "un local pidió más unidades de las que necesita": devolvió "Cálculo de la demanda", se esperaba "Aprobación de solicitudes"
- "no queda mercadería suficiente en la central para lo proyectado": devolvió "Prioridades cuando la bodega central no alcanza", se esperaba "Compras"
- "cuándo se avisa a adquisiciones que falta producto": devolvió "Prioridades cuando la bodega central no alcanza", se esperaba "Compras"
- "se cuentan las ventas al por mayor para calcular cuánto pedir": devolvió "Bodega online", se esperaba "Cálculo de la demanda"
