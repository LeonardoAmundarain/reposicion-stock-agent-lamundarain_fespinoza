"""Interfaz Streamlit del agente de reposición de stock."""
import pandas as pd
import streamlit as st

from agent.core import confirmar_recepcion, conversar, evaluar_solicitud_tienda, planificar_local
from agent.memory import long_term
from agent.modelos import listar_modelos
from agent.memory.semantic import borrar_casos_aprendidos, obtener_embeddings
from agent.memory.short_term import crear_memoria_corto_plazo
from config import settings
from scripts.seed_data import ArchivoOcupado, reiniciar_demo

LOGO = settings.BASE_DIR / "assets" / "logo.png"
ICONO = settings.BASE_DIR / "assets" / "icono.png"

st.set_page_config(page_title="Agente de reposición", page_icon=str(ICONO), layout="wide")

# Carga el modelo al abrir la aplicación para que la primera planificación no demore.
with st.spinner("Preparando la memoria semántica..."):
    obtener_embeddings()

if "memoria" not in st.session_state:
    st.session_state.memoria = crear_memoria_corto_plazo()
if "chat" not in st.session_state:
    st.session_state.chat = []
if "resultado" not in st.session_state:
    st.session_state.resultado = None

NOMBRES = {local: f"{local} · {datos['nombre']}" for local, datos in settings.LOCALES.items()}
COLUMNAS = {
    "prioridad": "Prioridad", "codigo": "Código", "producto": "Producto", "nicho": "Nicho",
    "stock_local": "Stock local", "en_transito": "En camino", "central": "Central",
    "objetivo": "Objetivo", "cantidad": "Cantidad", "compra": "Comprar", "razon": "Razón",
}


def tabla(lineas: list[dict]) -> None:
    if lineas:
        df = pd.DataFrame(lineas)[list(COLUMNAS)].rename(columns=COLUMNAS)
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.caption("Sin productos en esta categoría.")


with st.sidebar:
    st.image(str(LOGO), width=220)
    st.title("Agente de reposición")
    st.caption("Perfumería · EP2 ISY0101")
    origen = "Datos reales (solo local)" if settings.FUENTE_DATOS == "real" else "Datos simulados"
    st.caption(f"Fuente: {origen}")
    fecha = st.date_input("Fecha del plan", value=settings.fecha_plan(),
                          min_value=settings.fecha_plan("2026-11-01"), max_value=settings.FIN_HORIZONTE)
    if settings.PICO_INICIO <= fecha <= settings.PICO_FIN:
        st.warning("Temporada alta: venta 1,5 veces lo normal")
    proveedores = {"gemini": "Gemini", "claude": "Claude"}
    proveedor = st.selectbox(
        "Modelo de IA para conversar", list(proveedores), format_func=proveedores.get,
        index=list(proveedores).index(settings.LLM_PROVEEDOR),
    )
    modelo = None
    if settings.llm_habilitado(proveedor):
        opciones = listar_modelos(proveedor)
        defecto = settings.CLAUDE_MODEL if proveedor == "claude" else settings.LLM_MODEL
        modelo = st.selectbox("Modelo", opciones,
                              index=opciones.index(defecto) if defecto in opciones else 0)
        if proveedor == "claude":
            st.caption("Claude es de pago: se usa solo el modelo elegido.")
        else:
            st.caption("Gemini es gratis: si el modelo se queda sin cuota o no responde, "
                       "el agente prueba con el siguiente.")
    else:
        st.warning(settings.motivo_llm_apagado(proveedor))
    if st.button("Reiniciar demo", icon=":material/restart_alt:"):
        try:
            reiniciar_demo()
        except ArchivoOcupado as error:
            st.error(str(error))
        else:
            borrar_casos_aprendidos()
            st.session_state.memoria = crear_memoria_corto_plazo()
            st.session_state.chat = []
            st.session_state.resultado = None
            st.rerun()

st.title("Reposición de tiendas y bodega online")
tab_plan, tab_chat, tab_solicitudes, tab_pedido = st.tabs(
    [":material/inventory_2: Planificar", ":material/forum: Conversar con el agente",
     ":material/assignment: Solicitudes abiertas", ":material/storefront: Pedido de tienda"]
)

with tab_plan:
    col_local, col_merma = st.columns([1, 2])
    local = col_local.selectbox("Local", list(NOMBRES), format_func=NOMBRES.get)
    merma = col_merma.text_input(
        "Simular cambio durante la ejecución (código:unidades que salen de la central)",
        placeholder="CODIGO:8",
    )
    if st.button("Planificar reposición", type="primary", icon=":material/play_arrow:"):
        simular = None
        if ":" in merma:
            codigo, unidades = merma.split(":", 1)
            simular = {codigo.strip(): int(unidades)}
        with st.spinner("El agente está ejecutando el plan..."):
            st.session_state.resultado = planificar_local(local, fecha, simular_merma=simular)

    r = st.session_state.resultado
    if r:
        if not r["ok"]:
            st.error(r["error"])
        elif r["accion"] == "frecuencia_cumplida":
            st.info(r["respuesta"])
        else:
            st.success(r["respuesta"])
            for aviso in r["replanificaciones"]:
                st.warning(f"Replanificación: {aviso}")
            lineas = r["lineas"]
            reponer = [l for l in lineas if l["accion"] in ("reponer", "reponer_parcial")]
            devolver = [l for l in lineas if l["accion"] == "devolver_central"]
            comprar = [l for l in lineas if l["compra"] > 0]
            cubiertos = [l for l in lineas if l["accion"] == "cubierto"]
            fuera_de_linea = [l for l in lineas if l["accion"] == "fuera_de_linea"]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Unidades a reponer", sum(l["cantidad"] for l in reponer))
            m2.metric("Unidades a devolver", sum(l["cantidad"] for l in devolver))
            m3.metric("Unidades a comprar", r["compras"])
            m4.metric("Productos cubiertos", len(cubiertos))
            t1, t2, t3, t4 = st.tabs([":material/local_shipping: Reponer", ":material/undo: Devolver a central",
                                      ":material/shopping_cart: Solicitar compra", ":material/block: Fuera de línea"])
            with t1:
                tabla(reponer)
            with t2:
                tabla(devolver)
            with t3:
                tabla(comprar)
            with t4:
                st.caption("Con venta reciente, pero de la línea de otra tienda: se venden hasta agotarse y no se reponen.")
                tabla(fuera_de_linea)
            with st.expander("Plan y razonamiento del agente"):
                st.dataframe(pd.DataFrame(
                    [{"Paso": t["paso"], "Entrada": str(t["entrada"]), "Salida": str(t["salida"])[:300]}
                     for t in r["traza"]]
                ), width="stretch", hide_index=True)
            with st.expander("Políticas recuperadas por significado"):
                for fuente in r["fuentes"]:
                    st.markdown(f"**{fuente['accion']} → {fuente['seccion']}**")
                    st.caption(fuente["texto"])

with tab_chat:
    st.caption("Prueba: «¿Cuánto stock hay de» más un código o nombre, «planifica la tienda de árabes», "
               "«cómo libero espacio en el local»")
    for rol, texto, nota in st.session_state.chat:
        with st.chat_message(rol, avatar=str(ICONO) if rol == "assistant" else ":material/person:"):
            # Dos espacios antes del salto: así Streamlit respeta cada línea.
            st.write(texto.replace("\n", "  \n"))
            if nota:
                st.caption(nota)
    mensaje = st.chat_input("Escribe al agente")
    if mensaje:
        with st.spinner("Pensando..."):
            salida = conversar(mensaje, st.session_state.memoria, fecha, proveedor=proveedor, modelo=modelo)
        herramientas = ", ".join(p["herramienta"] for p in salida["pasos"]) or "ninguna"
        nota = f"Motor: {salida['motor']} · Herramientas: {herramientas}"
        if salida["aviso"]:
            nota = f"{salida['aviso']} {nota}"
        st.session_state.chat += [("user", mensaje, None), ("assistant", salida["respuesta"], nota)]
        st.rerun()

with tab_solicitudes:
    abiertas = long_term.solicitudes()
    if not abiertas:
        st.caption("No hay solicitudes abiertas.")
    else:
        st.dataframe(pd.DataFrame(abiertas)[["id", "tipo", "local", "codigo", "producto", "cantidad", "estado", "razon"]],
                     width="stretch", hide_index=True)
        identificador = st.selectbox(
            "Confirmar recepción", [s["id"] for s in abiertas],
            format_func=lambda i: next(f"#{s['id']} {s['tipo']} {s['codigo']} ({s['cantidad']})"
                                       for s in abiertas if s["id"] == i),
        )
        if st.button("Confirmar recepción", icon=":material/check_circle:"):
            resultado = confirmar_recepcion(identificador, fecha)
            if resultado["ok"] and resultado["retomados"]:
                st.success(f"Compra recibida. El agente retomó la reposición: {resultado['retomados']}")
            elif resultado["ok"]:
                st.success("Recepción confirmada; el stock quedó actualizado.")
            else:
                st.error(resultado["error"])

with tab_pedido:
    st.caption("Sin monto tope: se aprueba lo requerido para cubrir la venta de la semana.")
    c1, c2, c3 = st.columns(3)
    local_pedido = c1.selectbox("Tienda", [14, 15], index=1, format_func=NOMBRES.get)
    ejemplo = "QUIEBRE15" if settings.FUENTE_DATOS == "simulado" else ""
    codigo_pedido = c2.text_input("Código del producto", value=ejemplo)
    cantidad_pedido = c3.number_input("Cantidad pedida", min_value=1, value=50)
    if st.button("Evaluar pedido", type="primary", icon=":material/fact_check:"):
        st.json(evaluar_solicitud_tienda(local_pedido, codigo_pedido.strip(), int(cantidad_pedido), fecha))
