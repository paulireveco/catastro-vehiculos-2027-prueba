
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Catastro Vehiculos 2027",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 Catastro Nacional de Vehiculos Institucionales 2027")
st.caption("Aplicacion para revisar, filtrar y analizar la priorizacion de vehiculos institucionales.")

ARCHIVO_DEFECTO = "catastro_vehiculos_ajustado_3.xlsx"


def cargar_excel(archivo):
    """Carga las hojas principales del archivo Excel."""
    xls = pd.ExcelFile(archivo, engine="openpyxl")
    hojas = xls.sheet_names

    df_catastro = pd.read_excel(xls, sheet_name="Catastro ajustado") if "Catastro ajustado" in hojas else pd.DataFrame()
    df_resumen = pd.read_excel(xls, sheet_name="Resumen criterios") if "Resumen criterios" in hojas else pd.DataFrame()
    df_plan = pd.read_excel(xls, sheet_name="Plan aplicado") if "Plan aplicado" in hojas else pd.DataFrame()

    return df_catastro, df_resumen, df_plan


@st.cache_data(show_spinner=False)
def preparar_datos(df):
    """Asegura tipos numericos y campos necesarios para graficos."""
    if df.empty:
        return df

    columnas_numericas = [
        "Año Vehículo ajustado",
        "Kilometraje ajustado",
        "Gasto mantención ajustado",
        "Rendimiento Km/L",
        "Total criterios cumplidos",
    ]

    for col in columnas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["Servicio", "Tipo vehículo ajustado", "Estado", "Priorización"]:
        if col in df.columns:
            df[col] = df[col].fillna("No indica").astype(str)

    return df


st.sidebar.header("Carga de archivo")
archivo = st.sidebar.file_uploader(
    "Sube el archivo Excel ajustado",
    type=["xlsx"],
    help="Debe contener la hoja 'Catastro ajustado'."
)

if archivo is None:
    st.info("Sube el archivo Excel para iniciar el analisis. Si el archivo esta en la misma carpeta que app.py, tambien se intentara cargar automaticamente.")
    try:
        df_catastro, df_resumen, df_plan = cargar_excel(ARCHIVO_DEFECTO)
        st.success(f"Archivo cargado automaticamente: {ARCHIVO_DEFECTO}")
    except Exception:
        st.stop()
else:
    try:
        df_catastro, df_resumen, df_plan = cargar_excel(archivo)
        st.success("Archivo cargado correctamente.")
    except Exception as e:
        st.error(f"No fue posible cargar el archivo: {e}")
        st.stop()


df_catastro = preparar_datos(df_catastro)

if df_catastro.empty:
    st.warning("No se encontro informacion en la hoja 'Catastro ajustado'.")
    st.stop()

# Filtros
st.sidebar.header("Filtros")

servicios = sorted(df_catastro["Servicio"].dropna().unique()) if "Servicio" in df_catastro.columns else []
servicio_sel = st.sidebar.multiselect("Servicio", servicios, default=servicios)

priorizaciones = sorted(df_catastro["Priorización"].dropna().unique()) if "Priorización" in df_catastro.columns else []
priorizacion_sel = st.sidebar.multiselect("Priorizacion", priorizaciones, default=priorizaciones)

estados = sorted(df_catastro["Estado"].dropna().unique()) if "Estado" in df_catastro.columns else []
estado_sel = st.sidebar.multiselect("Estado", estados, default=estados)

min_criterios = 0
max_criterios = int(df_catastro["Total criterios cumplidos"].max()) if "Total criterios cumplidos" in df_catastro.columns and df_catastro["Total criterios cumplidos"].notna().any() else 4
rango_criterios = st.sidebar.slider("Total criterios cumplidos", min_value=0, max_value=max_criterios, value=(0, max_criterios))


df_filtrado = df_catastro.copy()
if servicio_sel and "Servicio" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["Servicio"].isin(servicio_sel)]
if priorizacion_sel and "Priorización" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["Priorización"].isin(priorizacion_sel)]
if estado_sel and "Estado" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["Estado"].isin(estado_sel)]
if "Total criterios cumplidos" in df_filtrado.columns:
    df_filtrado = df_filtrado[
        df_filtrado["Total criterios cumplidos"].between(rango_criterios[0], rango_criterios[1], inclusive="both")
    ]

# Indicadores
st.subheader("Indicadores principales")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Vehiculos filtrados", f"{len(df_filtrado):,}".replace(",", "."))

if "Total criterios cumplidos" in df_filtrado.columns:
    alta_carga = int((df_filtrado["Total criterios cumplidos"] >= 3).sum())
    promedio = df_filtrado["Total criterios cumplidos"].mean()
else:
    alta_carga = 0
    promedio = 0

col2.metric("Con 3 o mas criterios", f"{alta_carga:,}".replace(",", "."))
col3.metric("Promedio criterios", f"{promedio:.2f}")

if "Gasto mantención ajustado" in df_filtrado.columns:
    gasto_total = df_filtrado["Gasto mantención ajustado"].fillna(0).sum()
else:
    gasto_total = 0
col4.metric("Gasto mantencion total", f"${gasto_total:,.0f}".replace(",", "."))

# Graficos
st.subheader("Visualizaciones")
g1, g2 = st.columns(2)

with g1:
    if "Priorización" in df_filtrado.columns:
        conteo_prioridad = df_filtrado["Priorización"].value_counts().reset_index()
        conteo_prioridad.columns = ["Priorización", "Cantidad"]
        fig = px.bar(conteo_prioridad, x="Priorización", y="Cantidad", title="Vehiculos por priorizacion")
        st.plotly_chart(fig, use_container_width=True)

with g2:
    if "Total criterios cumplidos" in df_filtrado.columns:
        conteo_criterios = df_filtrado["Total criterios cumplidos"].value_counts().sort_index().reset_index()
        conteo_criterios.columns = ["Total criterios cumplidos", "Cantidad"]
        fig = px.bar(conteo_criterios, x="Total criterios cumplidos", y="Cantidad", title="Distribucion de criterios cumplidos")
        st.plotly_chart(fig, use_container_width=True)

if "Servicio" in df_filtrado.columns:
    conteo_servicio = df_filtrado["Servicio"].value_counts().reset_index()
    conteo_servicio.columns = ["Servicio", "Cantidad"]
    fig = px.bar(conteo_servicio.head(20), x="Cantidad", y="Servicio", orientation="h", title="Vehiculos por servicio")
    st.plotly_chart(fig, use_container_width=True)

# Tabla principal
st.subheader("Detalle del catastro")
columnas_preferidas = [
    "Servicio",
    "I.R.N.V.M. ajustado",
    "Tipo vehículo ajustado",
    "Año Vehículo ajustado",
    "Kilometraje ajustado",
    "Gasto mantención ajustado",
    "Estado",
    "Priorización",
    "Total criterios cumplidos",
    "Observaciones",
]
columnas_mostrar = [c for c in columnas_preferidas if c in df_filtrado.columns]
st.dataframe(df_filtrado[columnas_mostrar] if columnas_mostrar else df_filtrado, use_container_width=True)

# Descarga de datos filtrados
csv = df_filtrado.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="Descargar datos filtrados en CSV",
    data=csv,
    file_name="catastro_vehiculos_filtrado.csv",
    mime="text/csv"
)

# Secciones informativas
with st.expander("Resumen criterios del archivo"):
    if not df_resumen.empty:
        st.dataframe(df_resumen, use_container_width=True)
    else:
        st.info("No se encontro la hoja 'Resumen criterios'.")

with st.expander("Plan aplicado"):
    if not df_plan.empty:
        st.dataframe(df_plan, use_container_width=True)
    else:
        st.info("No se encontro la hoja 'Plan aplicado'.")
