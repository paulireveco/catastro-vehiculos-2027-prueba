
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

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
def generar_minuta(df):
    fecha_actual = datetime.now().strftime("%d-%m-%Y %H:%M")

    total_registros = len(df)

    if total_registros == 0:
        minuta = f"""
MINUTA EJECUTIVA
Catastro Nacional de Vehículos Institucionales 2027

Fecha de generación: {fecha_actual}

No existen registros para los filtros aplicados.

Se recomienda modificar los filtros seleccionados para generar un análisis con información disponible.
"""
        return minuta

    total_3_mas = 0
    promedio_criterios = 0
    gasto_total = 0

    if "Total criterios cumplidos" in df.columns:
        total_3_mas = int((df["Total criterios cumplidos"] >= 3).sum())
        promedio_criterios = df["Total criterios cumplidos"].mean()

    if "Gasto mantención ajustado" in df.columns:
        gasto_total = df["Gasto mantención ajustado"].fillna(0).sum()

    servicios_texto = "No disponible"
    if "Servicio" in df.columns:
        servicios = sorted(df["Servicio"].dropna().astype(str).unique())
        servicios_texto = ", ".join(servicios[:10])
        if len(servicios) > 10:
            servicios_texto += f", entre otros. Total servicios: {len(servicios)}"

    priorizacion_texto = "No disponible"
    if "Priorización" in df.columns:
        conteo_priorizacion = df["Priorización"].value_counts()
        priorizacion_texto = ""
        for prioridad, cantidad in conteo_priorizacion.items():
            priorizacion_texto += f"- {prioridad}: {cantidad}\n"

    top_servicios_texto = "No disponible"
    if "Servicio" in df.columns and "Total criterios cumplidos" in df.columns:
        df_criticos = df[df["Total criterios cumplidos"] >= 3]
        if not df_criticos.empty:
            top_servicios = df_criticos["Servicio"].value_counts().head(5)
            top_servicios_texto = ""
            for servicio, cantidad in top_servicios.items():
                top_servicios_texto += f"- {servicio}: {cantidad} vehículos\n"
        else:
            top_servicios_texto = "No se identifican vehículos con 3 o más criterios cumplidos."

    gasto_total_fmt = f"${gasto_total:,.0f}".replace(",", ".")
    promedio_fmt = f"{promedio_criterios:.2f}".replace(".", ",")

    minuta = f"""
MINUTA EJECUTIVA
Catastro Nacional de Vehículos Institucionales 2027

Fecha de generación: {fecha_actual}

1. Antecedentes

La presente minuta se genera automáticamente a partir del dashboard del Catastro Nacional de Vehículos Institucionales 2027, considerando los filtros aplicados por el usuario al momento de emitir el reporte.

2. Universo analizado

- Total de vehículos considerados en el filtro: {total_registros}
- Servicios incluidos: {servicios_texto}
- Vehículos con 3 o más criterios cumplidos: {total_3_mas}
- Promedio de criterios cumplidos: {promedio_fmt}
- Gasto total de mantención asociado al filtro: {gasto_total_fmt}

3. Distribución por priorización

{priorizacion_texto}

4. Servicios con mayor concentración de vehículos críticos

{top_servicios_texto}

5. Observación técnica

Los vehículos con mayor cantidad de criterios cumplidos concentran condiciones relevantes para evaluación institucional, especialmente cuando presentan antigüedad elevada, alto kilometraje, mayores gastos de mantención o priorización alta informada por la unidad correspondiente.

6. Recomendación

Se recomienda revisar los vehículos que cumplen 3 o más criterios, a fin de evaluar su incorporación en procesos de planificación presupuestaria, renovación, reposición o análisis técnico de continuidad operativa.

Esta minuta constituye un insumo preliminar para apoyar la toma de decisiones y debe ser complementada con antecedentes administrativos, presupuestarios y técnicos de cada servicio.
"""

    return minuta

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
st.subheader("Generación de reporte")

minuta_texto = generar_minuta(df_filtrado)

st.download_button(
    label="📄 Descargar minuta del análisis filtrado",
    data=minuta_texto,
    file_name="minuta_catastro_vehiculos_2027.txt",
    mime="text/plain"
)

with st.expander("Vista previa de la minuta"):
    st.text(minuta_texto)
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

Agrega generación de minuta automática
Corrige generación de minuta
