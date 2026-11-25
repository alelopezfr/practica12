import os
import json
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Dashboard CoinGecko - Práctica 12", layout="wide")
st.title("🪙 Dashboard de Mercado Cripto (CoinGecko API)")

# ==============================================================================
# REQUISITO 1: Validación de token externo (token.txt)
# ==============================================================================
TOKEN_FILE = "token.txt"

if not os.path.exists(TOKEN_FILE):
    st.error(f"Error: No se encontró el archivo '{TOKEN_FILE}'.")
    st.stop()

with open(TOKEN_FILE, "r", encoding="utf-8") as f:
    API_KEY = f.read().strip()

if not API_KEY:
    st.error("Error: El archivo 'token.txt' está vacío.")
    st.stop()

# ==============================================================================
# REQUISITO 4: Caché y conexión a CoinGecko Demo API
# ==============================================================================
CACHE_FILE = "respuesta.json"
URL = "https://api.coingecko.com/api/v3/coins/markets"

@st.cache_data(ttl=600)
def obtener_datos_coingecko(api_key, vs_currency="usd", per_page=250, page=1):
    params = {
        "vs_currency": vs_currency,
        "per_page": per_page,
        "page": page,
        "sparkline": "false",
    }
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": api_key,
    }
    response = requests.get(URL, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()

# Barra lateral con controles interactivos
st.sidebar.header("⚙️ Configuración")
fuente = st.sidebar.radio(
    "Fuente de datos:",
    ["Consultar API en vivo", "Usar respaldo local (respuesta.json)"]
)

moneda = st.sidebar.selectbox("Moneda de referencia (vs_currency):", ["usd", "mxn", "eur"], index=0)
cantidad = st.sidebar.slider("Registros por página (per_page):", min_value=10, max_value=250, value=250, step=10)

datos_json = None

if fuente == "Consultar API en vivo":
    if st.sidebar.button("🔄 Actualizar desde CoinGecko"):
        st.cache_data.clear()
    try:
        with st.spinner("Consultando CoinGecko API..."):
            datos_json = obtener_datos_coingecko(API_KEY, vs_currency=moneda, per_page=cantidad, page=1)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(datos_json, f, indent=4, ensure_ascii=False)
        st.sidebar.success("Datos actualizados y guardados en respuesta.json")
    except Exception as e:
        st.error(f"Error al consultar la API: {e}")
        st.info("Puedes cambiar a 'Usar respaldo local (respuesta.json)' en el menú izquierdo.")
        st.stop()
else:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            datos_json = json.load(f)
        st.sidebar.info(f"Cargado desde {CACHE_FILE}")
    else:
        st.error(f"No se encontró '{CACHE_FILE}'.")
        st.stop()

# ==============================================================================
# TRANSFORMACIÓN A DATAFRAME
# ==============================================================================
if isinstance(datos_json, list):
    df = pd.json_normalize(datos_json)
elif isinstance(datos_json, dict):
    # Por si el JSON envuelve la lista en alguna clave
    lista = datos_json.get("data") or datos_json.get("results") or [datos_json]
    df = pd.json_normalize(lista)
else:
    st.error("Formato de respuesta JSON no esperado.")
    st.stop()

# Métricas generales
c1, c2, c3 = st.columns(3)
c1.metric("Criptomonedas / Registros", len(df))
c2.metric("Columnas", len(df.columns))
c3.metric("Fuente activa", "API en vivo" if fuente == "Consultar API en vivo" else CACHE_FILE)

st.divider()

# Pestañas del dashboard
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Gráficas Interactivas",
    "🖼️ Gráficas Guardadas (.png)",
    "📋 Tabla y Filtros",
    "🔍 JSON"
])

with tab1:
    st.subheader("Exploración Interactiva desde el DataFrame")
    if not df.empty:
        etiqueta_col = "name" if "name" in df.columns else df.columns[0]
        num_cols = df.select_dtypes(include="number").columns.tolist()

        if num_cols:
            col_eje = st.selectbox("Elige una métrica numérica:", num_cols, index=0)
            top_n = st.slider("Top N a mostrar:", min_value=5, max_value=min(50, len(df)), value=min(15, len(df)))
            df_top = df.sort_values(by=col_eje, ascending=False).head(top_n).set_index(etiqueta_col)
            st.bar_chart(df_top[col_eje])
        else:
            st.warning("No se detectaron columnas numéricas en los datos.")

with tab2:
    st.subheader("Imágenes Generadas en tu Práctica")
    g1, g2 = st.columns(2)
    with g1:
        if os.path.exists("grafica_comparacion.png"):
            st.image("grafica_comparacion.png", caption="Comparación", use_container_width=True)
        if os.path.exists("grafica_evolucion.png"):
            st.image("grafica_evolucion.png", caption="Evolución", use_container_width=True)
    with g2:
        if os.path.exists("grafica_distribucion.png"):
            st.image("grafica_distribucion.png", caption="Distribución", use_container_width=True)
        if os.path.exists("grafica_relacion.png"):
            st.image("grafica_relacion.png", caption="Relación", use_container_width=True)

with tab3:
    st.subheader("Tabla de Datos")
    buscar = st.text_input("Buscar por texto (ej. bitcoin, btc, eth):")
    df_filtrado = df.copy()
    if buscar:
        mask = df_filtrado.astype(str).apply(lambda row: row.str.contains(buscar, case=False, na=False)).any(axis=1)
        df_filtrado = df_filtrado[mask]

    cols_sel = st.multiselect("Columnas a mostrar:", df_filtrado.columns.tolist(), default=df_filtrado.columns.tolist()[:8])
    if cols_sel:
        st.dataframe(df_filtrado[cols_sel], use_container_width=True)
        csv = df_filtrado[cols_sel].to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Descargar CSV filtrado", data=csv, file_name="coingecko_filtrado.csv", mime="text/csv")

with tab4:
    st.json(datos_json)