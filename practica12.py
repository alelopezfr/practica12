import os
import json
import requests
import pandas as pd

# ==========================================================
# REQUISITO 1: El token vive fuera del código y se valida
# ==========================================================
TOKEN_FILE = "token.txt"

if not os.path.exists(TOKEN_FILE):
    print(f"Error: No se encontró el archivo '{TOKEN_FILE}'. Asegúrate de crearlo en la misma carpeta.")
    raise SystemExit(1)

with open(TOKEN_FILE, "r", encoding="utf-8") as f:
    API_KEY = f.read().strip()

if not API_KEY:
    print("Error: El archivo 'token.txt' está vacío. Copia y pega tu API Key dentro del archivo.")
    raise SystemExit(1)

print("✓ Token leído y validado correctamente.")

# ==========================================================
# REQUISITO 4: Caché local (guarda respuesta.json para no gastar peticiones)
# ==========================================================
CACHE_FILE = "respuesta.json"
URL = "https://api.coingecko.com/api/v3/coins/markets"

# Parámetros para obtener 250 registros (Cumple Requisito 3 de la Fase 1)
params = {
    "vs_currency": "usd",
    "per_page": 250,
    "page": 1,
    "sparkline": "false"
}

# Envío del token en el encabezado exacto de CoinGecko Demo API
headers = {
    "accept": "application/json",
    "x-cg-demo-api-key": API_KEY
}

if os.path.exists(CACHE_FILE):
    print(f"✓ Cargando datos desde el archivo local '{CACHE_FILE}'...")
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    print("Consultando la API de CoinGecko...")
    try:
        response = requests.get(URL, headers=headers, params=params, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión con la red: {e}")
        raise SystemExit(1)

    # ==========================================================
    # REQUISITO 2: Revisar código de estado antes de continuar
    # ==========================================================
    if response.status_code == 401:
        print("Error 401: El token proporcionado no sirve o no está autorizado.")
        raise SystemExit(1)
    elif response.status_code == 400:
        print("Error 400: Solicitud incorrecta (Bad Request). Revisa los parámetros del endpoint.")
        raise SystemExit(1)
    elif response.status_code == 429:
        print("Error 429: Has superado el límite de peticiones permitido por minuto/día.")
        raise SystemExit(1)
    elif response.status_code != 200:
        print(f"Error HTTP {response.status_code}: No se pudo obtener respuesta de la API.")
        raise SystemExit(1)

    # ==========================================================
    # REQUISITO 3: Revisar que la respuesta sea un JSON válido
    # ==========================================================
    content_type = response.headers.get("Content-Type") or ""
    if "json" not in content_type:
        print("La respuesta del servidor no es un JSON válido:")
        print(response.text[:300])
        raise SystemExit(1)

    data = response.json()

    # Guardar en respuesta.json
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"✓ Datos obtenidos con éxito y guardados en '{CACHE_FILE}'.")

# ==========================================================
# REQUISITO 5: La limpieza queda documentada en la salida
# ==========================================================
df = pd.DataFrame(data)

print("\n" + "=" * 50)
print("  DOCUMENTACIÓN DEL PROCESO DE LIMPIEZA DE DATOS")
print("=" * 50)

print(f"\n1. Registros iniciales cargados: {len(df)}")

print("\n2. Tipos de datos iniciales:")
print(df[["id", "name", "current_price", "market_cap", "total_volume", "price_change_percentage_24h"]].dtypes)

print("\n3. Valores faltantes por columna:")
print(df[["current_price", "market_cap", "total_volume", "price_change_percentage_24h"]].isnull().sum())

# Conversión explícita a tipo numérico
columnas_numericas = ["current_price", "market_cap", "total_volume", "price_change_percentage_24h"]
registros_antes = len(df)

for col in columnas_numericas:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Eliminación de nulos en columnas clave para graficar
df_limpio = df.dropna(subset=columnas_numericas).copy()
registros_perdidos = registros_antes - len(df_limpio)

print(f"\n4. Conversión numérica completada.")
print(f"   - Registros descartados por valores nulos o inválidos: {registros_perdidos}")
print(f"   - Registros finales utilizables: {len(df_limpio)}")
print("=" * 50 + "\n")
import matplotlib.pyplot as plt

# ==========================================================
# FASE 4: Las cuatro gráficas (Paleta del curso y reglas)
# ==========================================================
# Colores del curso: Gris contexto (#B9C3D1), Azul principal (#1C4C9A)
# Cualitativos: #E69F00, #56B4E9, #009E73, #0072B2
COLOR_CONTEXTO = "#B9C3D1"
COLOR_DESTACADO = "#1C4C9A"
COLORES_CUALITATIVOS = ["#E69F00", "#56B4E9", "#009E73", "#0072B2"]

# ----------------------------------------------------------
# Gráfica 1: Distribución (¿Cómo se reparten los valores?)
# ----------------------------------------------------------
plt.figure(figsize=(8, 5))
plt.hist(df_limpio['current_price'], bins=20, color=COLOR_CONTEXTO, edgecolor='white')

# Destacamos las de menor precio (< $10 USD) para el hallazgo
precios_bajos = df_limpio[df_limpio['current_price'] < 10]['current_price']
plt.hist(precios_bajos, bins=20, color=COLOR_DESTACADO, edgecolor='white', label='Precio < $10 USD')

plt.title("La gran mayoría de las criptomonedas cotizan por debajo de los 10 dólares")
plt.xlabel("Precio actual (USD)")
plt.ylabel("Número de criptomonedas")
plt.legend()
plt.tight_layout()
plt.savefig("grafica_distribucion.png")
plt.show()

# ----------------------------------------------------------
# Gráfica 2: Comparación (¿Qué grupo tiene más?)
# ----------------------------------------------------------
# Comparamos el volumen de comercio de las 5 criptomonedas con mayor capitalización
top_5 = df_limpio.nlargest(5, 'market_cap')

plt.figure(figsize=(8, 5))
plt.bar(top_5['symbol'].str.upper(), top_5['total_volume'] / 1e9, color=COLORES_CUALITATIVOS[:5])

plt.title("Bitcoin y Ethereum concentran drásticamente el volumen comercial diario")
plt.xlabel("Criptomoneda")
plt.ylabel("Volumen total (Miles de millones USD)")
plt.tight_layout()
plt.savefig("grafica_comparacion.png")
plt.show()

# ----------------------------------------------------------
# Gráfica 3: Relación (¿Estas dos variables se mueven juntas?)
# ----------------------------------------------------------
plt.figure(figsize=(8, 5))
plt.scatter(df_limpio['market_cap'] / 1e9, df_limpio['total_volume'] / 1e9, 
            color=COLOR_CONTEXTO, alpha=0.7, label='Resto del mercado')

# Destacamos Bitcoin y Ethereum
bt_eth = df_limpio[df_limpio['symbol'].isin(['btc', 'eth'])]
plt.scatter(bt_eth['market_cap'] / 1e9, bt_eth['total_volume'] / 1e9, 
            color=COLOR_DESTACADO, s=100, label='Bitcoin y Ethereum')

plt.title("A mayor capitalización de mercado, mayor volumen de operaciones")
plt.xlabel("Capitalización de mercado (Miles de millones USD)")
plt.ylabel("Volumen total (Miles de millones USD)")
plt.legend()
plt.tight_layout()
plt.savefig("grafica_relacion.png")
plt.show()

# ----------------------------------------------------------
# Gráfica 4: Evolución (¿Cómo cambió esto? / Cambio 24h)
# ----------------------------------------------------------
# Ordenamos por el cambio porcentual en 24h de mayor a menor para ver ganadores y perdedores
df_ordenado = df_limpio.sort_values(by='price_change_percentage_24h', ascending=False)
muestra_cambio = pd.concat([df_ordenado.head(5), df_ordenado.tail(5)])

colores_barras = [COLORES_CUALITATIVOS[2] if x > 0 else COLORES_CUALITATIVOS[0] for x in muestra_cambio['price_change_percentage_24h']]

plt.figure(figsize=(10, 5))
plt.barh(muestra_cambio['symbol'].str.upper(), muestra_cambio['price_change_percentage_24h'], color=colores_barras)

plt.title("Altas volatilidades extremas: mayores ganancias y pérdidas en las últimas 24h")
plt.xlabel("Cambio porcentual en 24 horas (%)")
plt.ylabel("Criptomoneda")
plt.axvline(0, color='black', linewidth=0.8, linestyle='--')
plt.tight_layout()
plt.savefig("grafica_evolucion.png")
plt.show()