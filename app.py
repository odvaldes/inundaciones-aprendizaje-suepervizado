
"""
GeoRiskAI Sentinel
Dashboard comercial y profesional para visualización de proyectos y carta CITSU.
"""

import os
import zipfile
from pathlib import Path
import tempfile
import re
import unicodedata
import html
import textwrap
from io import BytesIO
from shapely.geometry import box

import pandas as pd
import geopandas as gpd
import folium
import streamlit as st
from streamlit_folium import st_folium


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="GeoRiskAI Sentinel",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR / "data"

ARCHIVO_PROYECTOS = BASE_DIR / "MDS_PROYECTOS 2024 2026.xlsx"
ARCHIVOS_CITSU = [
    BASE_DIR / "CITSU_Coquimbo_La_Serena_2da_Ed_2015.kmz",
    BASE_DIR / "shoa-cl_descargas_citsu_kmz_CITSU_Guanaqueros_1ra Ed. 2019.kmz",
    BASE_DIR / "shoa-cl_descargas_citsu_kmz_CITSU_Tongoy_1era_Ed_2019.kmz",
    BASE_DIR / "CITSU_Los_Vilos_2da_Ed_2017.kmz",
    BASE_DIR / "CITSU_Los_Molles-La_Ballena_1a_ed._2023.kmz",
    BASE_DIR / "CITSU_Pichicuy-Longotoma_1a_ed._2023.kmz",
    BASE_DIR / "CITSU_Papudo_2da_Ed_2017.kmz",
    BASE_DIR / "CITSU_Zapallar-Cachagua-La_Laguna-Maitencillo_2da_Ed_2015.kmz",
    BASE_DIR / "CITSU_Quintero-Ventana-Horcon_2da_Ed_2011.kmz",
    BASE_DIR / "concon_ritoque_1ra_ed_2012.kmz",
    BASE_DIR / "citsu_valparaiso_vinna.kmz",
    BASE_DIR / "CITSU_Laguna_Verde_1ra_Ed_2017.kmz",
    BASE_DIR / "CITSU_Quintay_1ra_Ed_2018.kmz",
    BASE_DIR / "CITSU_Bahia_Cumberland_1ra_Ed_2013.kmz",
    BASE_DIR / "Isla_de_Pascua_Hanga_Hotuiti_Ed_2006.kmz",
    BASE_DIR / "Isla_de_Pascua_Hanga_La_Perouse_Ed_2006.kmz",
    BASE_DIR / "CITSU_Algarrobo_3a_Ed_2023.kmz",
    BASE_DIR / "CITSU_ElQuisco-IslaNegra-ElTabo1aEd.2023.kmz",
    BASE_DIR / "CITSU_LasCruces-SanSebastián-Cartagena2aEd2023.kmz",
    BASE_DIR / "CITSU_San_Antonio_3a_ed_2025.kmz",
    BASE_DIR / "CITSU_Santo_Domingo_1a_ed_2025.kmz",
    BASE_DIR / "CITSU_Constitucion_2da_Ed_2016.kmz",
    BASE_DIR / "CITSU_Bahias_Concepcion_San Vicente_1ra_Ed2013.kmz",
    BASE_DIR / "CITSU_Bahias_Concepcion_San Vicente_1ra_Ed2013 (1).kmz",
    BASE_DIR / "San_Pedro_de_la_Paz.kmz",
]

# =========================================================
# IDENTIDAD VISUAL
# =========================================================

st.markdown(
    """
    <style>
    :root {
        --navy: #0A2F57;
        --blue: #155F98;
        --cyan: #2DA9D8;
        --light: #F5F9FD;
        --card: #FFFFFF;
        --border: #DCE6EF;
        --text: #17324D;
        --muted: #6B7F92;
        --danger: #D94841;
        --warning: #F39B36;
        --success: #2E9B6F;
        --shadow: 0 10px 30px rgba(22, 61, 93, 0.10);
    }

    html, body, [class*="css"] {
        font-family: "Segoe UI", Arial, sans-serif;
    }

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at top right, rgba(45,169,216,0.12), transparent 26%),
            linear-gradient(180deg, #F8FBFE 0%, #EEF5FA 100%);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stSidebar"] {
        background:
            linear-gradient(180deg, #F5F9FD 0%, #EAF2F8 100%);
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1500px;
    }

    .hero {
        position: relative;
        overflow: hidden;
        background:
            linear-gradient(100deg, rgba(7,42,80,0.98), rgba(20,99,155,0.94)),
            radial-gradient(circle at 80% 20%, rgba(255,255,255,0.20), transparent 25%);
        border-radius: 20px;
        padding: 26px 30px;
        color: white;
        box-shadow: 0 16px 40px rgba(10,47,87,0.22);
        margin-bottom: 18px;
    }

    .hero::after {
        content: "";
        position: absolute;
        width: 260px;
        height: 260px;
        border-radius: 50%;
        right: -60px;
        top: -120px;
        background: rgba(255,255,255,0.08);
    }

    .hero-brand {
        font-size: 13px;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        opacity: 0.82;
        margin-bottom: 6px;
    }

    .hero-title {
        font-size: 31px;
        font-weight: 800;
        line-height: 1.15;
        margin: 0;
    }

    .hero-subtitle {
        font-size: 15px;
        color: #D9ECFA;
        margin-top: 8px;
        max-width: 850px;
    }

    .status-pill {
        display: inline-block;
        margin-top: 14px;
        padding: 7px 12px;
        border-radius: 999px;
        background: rgba(255,255,255,0.14);
        border: 1px solid rgba(255,255,255,0.20);
        font-size: 12px;
        font-weight: 700;
    }

    .section-title {
        font-size: 18px;
        font-weight: 800;
        color: var(--navy);
        margin: 12px 0 10px 0;
    }

    .kpi-card {
        background: var(--card);
        border: 1px solid rgba(220,230,239,0.95);
        border-radius: 18px;
        padding: 17px 18px;
        min-height: 118px;
        box-shadow: var(--shadow);
        position: relative;
        overflow: hidden;
    }

    .kpi-card::after {
        content: "";
        position: absolute;
        width: 90px;
        height: 90px;
        border-radius: 50%;
        top: -38px;
        right: -28px;
        background: rgba(45,169,216,0.08);
    }

    .kpi-label {
        font-size: 12px;
        font-weight: 700;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .kpi-value {
        font-size: 28px;
        font-weight: 850;
        color: var(--navy);
        margin-top: 9px;
        line-height: 1;
    }

    .kpi-note {
        font-size: 12px;
        color: var(--muted);
        margin-top: 9px;
    }

    .risk-card {
        color: white;
        border: none;
        min-height: 118px;
    }

    .risk-value {
        font-size: 26px;
        font-weight: 850;
        margin-top: 10px;
        line-height: 1.1;
    }

    .panel {
        width:100%;
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 18px;
        box-shadow: var(--shadow);
    }

    .panel-title {
        font-size: 16px;
        font-weight: 800;
        color: var(--navy);
        margin-bottom: 12px;
    }

    .project-name {
        font-size: 16px;
        font-weight: 800;
        color: var(--navy);
        line-height: 1.3;
        margin-bottom: 10px;
    }

    .info-row {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        padding: 9px 0;
        border-bottom: 1px solid #EDF2F6;
        font-size: 13px;
    }

    .info-row:last-child {
        border-bottom: none;
    }

    .info-label {
        color: var(--muted);
        font-weight: 600;
    }

    .info-value {
        color: var(--text);
        font-weight: 800;
        text-align: right;
    }

    .badge {
        display: inline-block;
        padding: 7px 11px;
        border-radius: 999px;
        color: white;
        font-size: 12px;
        font-weight: 800;
        margin-top: 4px;
    }

    .recommendation {
        background:
            linear-gradient(180deg, #FFF8E7 0%, #FFF2CF 100%);
        border: 1px solid #F0D491;
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 10px 28px rgba(148, 105, 28, 0.10);
        margin-top: 14px;
    }

    .recommendation-title {
        color: #815A12;
        font-size: 16px;
        font-weight: 850;
        margin-bottom: 10px;
    }

    .recommendation ul {
        padding-left: 18px;
        margin-bottom: 0;
    }

    .recommendation li {
        margin-bottom: 8px;
        color: #604A22;
        font-size: 13px;
        line-height: 1.35;
    }

    .sidebar-brand {
        background: linear-gradient(120deg, #0A2F57, #155F98);
        color: white;
        padding: 16px;
        border-radius: 16px;
        margin-bottom: 14px;
        box-shadow: 0 10px 25px rgba(10,47,87,0.18);
    }

    .sidebar-brand-title {
        font-size: 18px;
        font-weight: 850;
        margin: 0;
    }

    .sidebar-brand-subtitle {
        font-size: 11px;
        color: #D8EAF7;
        margin-top: 5px;
    }

    .mini-note {
        background: #EDF5FB;
        color: #456075;
        border-radius: 12px;
        padding: 10px 12px;
        font-size: 11px;
        border: 1px solid #D9E6F0;
        margin-top: 12px;
    }

    div[data-testid="stDownloadButton"] > button {
        width: 100%;
        background: linear-gradient(90deg, #0A2F57, #155F98);
        color: white;
        border-radius: 12px;
        border: none;
        font-weight: 800;
        padding: 0.75rem 1rem;
        box-shadow: 0 8px 20px rgba(10,47,87,0.18);
    }

    div[data-testid="stDownloadButton"] > button:hover {
        color: white;
        border: none;
        transform: translateY(-1px);
    }

    div[data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
    }

    .stSelectbox label, .stTextInput label {
        font-size: 12px;
        color: var(--text);
        font-weight: 700;
    }

    .powerbi-shell {
        background: #FFFFFF;
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 14px;
        box-shadow: var(--shadow);
    }

    .powerbi-header {
        background: linear-gradient(105deg, #0A2F57, #155F98);
        border-radius: 14px;
        padding: 15px 17px;
        color: white;
        margin-bottom: 12px;
    }

    .powerbi-eyebrow {
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0.10em;
        text-transform: uppercase;
        color: #CDE7F7;
        margin-bottom: 5px;
    }

    .powerbi-project-title {
        font-size: 17px;
        line-height: 1.25;
        font-weight: 850;
    }

    .powerbi-badges {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-top: 9px;
    }

    .powerbi-badge {
        display: inline-block;
        padding: 5px 8px;
        border-radius: 999px;
        font-size: 10px;
        font-weight: 800;
        background: rgba(255,255,255,0.15);
        border: 1px solid rgba(255,255,255,0.20);
    }

    .powerbi-section {
        margin-top: 12px;
    }

    .powerbi-section-title {
        font-size: 11px;
        font-weight: 850;
        color: var(--navy);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 7px;
    }

    .powerbi-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 7px;
    }

    .powerbi-metric {
        background: #F7FAFD;
        border: 1px solid #E2EBF2;
        border-radius: 11px;
        padding: 9px 10px;
        min-height: 58px;
    }

    .powerbi-metric-label {
        font-size: 9px;
        color: var(--muted);
        font-weight: 750;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 4px;
    }

    .powerbi-metric-value {
        font-size: 12px;
        color: var(--text);
        font-weight: 850;
        line-height: 1.25;
        word-break: break-word;
    }

    .powerbi-financial {
        background: linear-gradient(180deg, #F7FBFF 0%, #EEF6FC 100%);
        border: 1px solid #D6E7F3;
        border-radius: 13px;
        padding: 10px;
    }

    .powerbi-note {
        font-size: 9px;
        color: var(--muted);
        margin-top: 7px;
        line-height: 1.4;
    }

    .powerbi-footer {
        margin-top: 11px;
        padding-top: 9px;
        border-top: 1px solid #E6EDF3;
        font-size: 9px;
        color: var(--muted);
        line-height: 1.4;
    }

    @media (max-width: 900px) {
        .powerbi-grid {
            grid-template-columns: 1fr;
        }

        .hero-title {
            font-size: 24px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)



# =========================================================
# FUNCIONES AUXILIARES PARA COLUMNAS Y PRESENTACIÓN
# =========================================================

def normalizar_nombre_columna(nombre):
    """
    Normaliza nombres de columnas para reconocer variantes como:
    REGION / REGIÓN, ETAPA POST / ETAPA POSTULA, CODIGO BIP / CÓDIGO BIP.
    """
    texto = unicodedata.normalize("NFKD", str(nombre))
    texto = "".join(
        caracter for caracter in texto
        if not unicodedata.combining(caracter)
    )
    texto = texto.upper().strip()
    texto = re.sub(r"[^A-Z0-9]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def buscar_columna(df_o_serie, candidatos):
    """
    Devuelve el nombre real de la primera columna que coincida
    con alguno de los candidatos normalizados.
    """
    columnas = list(
        df_o_serie.index
        if isinstance(df_o_serie, pd.Series)
        else df_o_serie.columns
    )

    mapa = {
        normalizar_nombre_columna(columna): columna
        for columna in columnas
    }

    # Coincidencia exacta normalizada
    for candidato in candidatos:
        clave = normalizar_nombre_columna(candidato)
        if clave in mapa:
            return mapa[clave]

    # Coincidencia parcial para columnas truncadas o con sufijos
    for candidato in candidatos:
        clave = normalizar_nombre_columna(candidato)
        for clave_real, columna_real in mapa.items():
            if clave in clave_real or clave_real in clave:
                return columna_real

    return None


def valor_proyecto(serie, candidatos, valor_defecto="Sin información"):
    """
    Obtiene de forma robusta un dato del proyecto seleccionado.
    """
    columna = buscar_columna(serie, candidatos)

    if columna is None:
        return valor_defecto

    valor = serie[columna]

    if pd.isna(valor):
        return valor_defecto

    texto = str(valor).strip()

    if texto == "" or texto.lower() in {"nan", "none", "<na>"}:
        return valor_defecto

    return texto


def texto_html_seguro(valor):
    return html.escape(str(valor), quote=True)


def formatear_costo(valor):
    """
    Formatea valores monetarios expresados en M$.
    """
    try:
        numero = float(
            str(valor)
            .replace(".", "")
            .replace(",", ".")
            .strip()
        )
        return f"{numero:,.0f} M$".replace(",", ".")
    except (TypeError, ValueError):
        return str(valor)


# =========================================================
# FUNCIONES DE DATOS
# =========================================================

@st.cache_data(show_spinner=False)
def cargar_excel_proyectos(ruta_excel):
    df = pd.read_excel(ruta_excel, sheet_name="APP")
    df.columns = df.columns.astype(str).str.strip()

    if "GEOLOCALIZACIÓN" not in df.columns:
        raise ValueError(
            "No se encontró la columna GEOLOCALIZACIÓN en la base de proyectos."
        )

    coords = df["GEOLOCALIZACIÓN"].astype(str).str.extract(
        r"(-?\d+\.\d+)[,\s]+(-?\d+\.\d+)"
    )

    df["latitud"] = pd.to_numeric(coords[0], errors="coerce")
    df["longitud"] = pd.to_numeric(coords[1], errors="coerce")

    mask_invertida = df["latitud"].abs() > 40

    df.loc[
        mask_invertida,
        ["latitud", "longitud"]
    ] = df.loc[
        mask_invertida,
        ["longitud", "latitud"]
    ].values

    df = df.dropna(
        subset=["latitud", "longitud"]
    ).copy()

    return gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(
            df["longitud"],
            df["latitud"]
        ),
        crs="EPSG:4326"
    )


@st.cache_data(show_spinner=False)
def cargar_kmz(ruta_kmz):
    if not Path(ruta_kmz).exists():
        return None

    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(str(ruta_kmz), "r") as archivo_zip:
            archivo_zip.extractall(tmpdir)

        archivos_kml = []

        for root, _, files in os.walk(tmpdir):
            for file in files:
                if file.lower().endswith(".kml"):
                    archivos_kml.append(
                        os.path.join(root, file)
                    )

        if not archivos_kml:
            return None

        gdf = gpd.read_file(
            archivos_kml[0],
            driver="KML"
        )

        if gdf.crs is None:
            gdf = gdf.set_crs("EPSG:4326")

        return gdf.to_crs("EPSG:4326")


def detectar_campo_categoria_citsu(gdf_citsu):
    candidatos = [
        "Name", "name", "NOMBRE", "Nombre",
        "description", "Description",
        "Altura", "ALTURA",
        "Categoria", "CATEGORIA",
        "Nivel", "NIVEL",
        "Riesgo", "RIESGO"
    ]

    for campo in candidatos:
        if campo in gdf_citsu.columns:
            return campo

    columnas = [
        columna
        for columna in gdf_citsu.columns
        if columna != "geometry"
    ]

    return columnas[0] if columnas else None


def clasificar_citsu(gdf_proyectos, gdf_citsu):
    resultado = gdf_proyectos.copy()

    if gdf_citsu is None:
        resultado["EN_CITSU"] = False
        resultado["CATEGORIA_CITSU"] = "FUERA CITSU"
        resultado["ARCHIVO_CITSU"] = None
        return resultado

    campo_categoria = detectar_campo_categoria_citsu(gdf_citsu)
    capa = gdf_citsu.copy()

    if campo_categoria is None:
        capa["CATEGORIA_TEMP"] = "ZONA CITSU"
        campo_categoria = "CATEGORIA_TEMP"

    columnas_cruce = [campo_categoria, "geometry"]
    if "ARCHIVO_CITSU" in capa.columns and campo_categoria != "ARCHIVO_CITSU":
        columnas_cruce.insert(1, "ARCHIVO_CITSU")

    cruce = gpd.sjoin(
        resultado,
        capa[columnas_cruce],
        how="left",
        predicate="intersects"
    )

    cruce["EN_CITSU"] = cruce["index_right"].notna()
    cruce["CATEGORIA_CITSU"] = (
        cruce[campo_categoria]
        .astype("string")
        .fillna("FUERA CITSU")
    )

    if "ARCHIVO_CITSU" not in cruce.columns:
        cruce["ARCHIVO_CITSU"] = None

    cruce = cruce.drop(
        columns=["index_right", campo_categoria],
        errors="ignore"
    )

    # Un proyecto puede tocar más de un polígono. Se conserva una sola fila.
    cruce = cruce[
        ~cruce.index.duplicated(keep="first")
    ].copy()

    return cruce


def preparar_citsu_para_mapa(gdf_citsu, proyecto, margen_grados=0.12):
    """
    Devuelve solo la cartografía CITSU necesaria para visualizar el proyecto.
    El GeoDataFrame completo se mantiene para el análisis espacial; esta
    reducción se usa exclusivamente para acelerar Folium.
    """
    if gdf_citsu is None or gdf_citsu.empty:
        return None

    # Si el proyecto intersecta una carta, mostrar únicamente esa carta.
    archivo_origen = proyecto.get("ARCHIVO_CITSU", None)
    if archivo_origen is not None and not pd.isna(archivo_origen):
        archivo_origen = str(archivo_origen).strip()
        if archivo_origen:
            local = gdf_citsu[
                gdf_citsu["ARCHIVO_CITSU"].astype(str) == archivo_origen
            ].copy()
            if not local.empty:
                local["geometry"] = local.geometry.simplify(
                    0.00008, preserve_topology=True
                )
                return local

    # Si está fuera de CITSU, buscar solo geometrías próximas al proyecto.
    x = float(proyecto.geometry.x)
    y = float(proyecto.geometry.y)
    ventana = box(
        x - margen_grados,
        y - margen_grados,
        x + margen_grados,
        y + margen_grados
    )

    try:
        indices = gdf_citsu.sindex.query(ventana, predicate="intersects")
        local = gdf_citsu.iloc[list(indices)].copy()
    except Exception:
        local = gdf_citsu[gdf_citsu.intersects(ventana)].copy()

    if local.empty:
        return local

    local["geometry"] = local.geometry.simplify(
        0.00008, preserve_topology=True
    )
    return local

def color_categoria(categoria):
    texto = str(categoria).lower()

    if "muy alto" in texto or ">6" in texto:
        return "#A92727"

    if "alto" in texto or "4" in texto or "5" in texto:
        return "#D94841"

    if "medio" in texto or "2" in texto or "3" in texto:
        return "#F39B36"

    if "bajo" in texto or "1" in texto:
        return "#2E9B6F"

    if "fuera" in texto:
        return "#2E9B6F"

    return "#667788"


def color_folium(categoria):
    texto = str(categoria).lower()

    if "muy alto" in texto:
        return "darkred"

    if "alto" in texto or "4" in texto or "5" in texto:
        return "red"

    if "medio" in texto or "2" in texto or "3" in texto:
        return "orange"

    if "bajo" in texto or "fuera" in texto or "1" in texto:
        return "green"

    return "blue"



# =========================================================
# MODELO MULTICRITERIO DEL ÍNDICE DE RIESGO
# =========================================================

CONFIG_IR = {
    "ponderaciones": {
        "amenaza": 0.667,
        "vulnerabilidad": 0.333,
        "materialidad": 0.75,
        "antiguedad": 0.25
    },
    "escalas_amenaza": {
        "Muy bajo": 0.00,
        "Bajo": 0.10,
        "Medio": 0.56,
        "Alto": 0.84,
        "Muy alto": 1.00
    },
    "escalas_materialidad": {
        "Alto": 1.00,
        "Medio": 0.53,
        "Bajo": 0.22
    },
    "escalas_normativa": {
        "Muy alto": 1.00,
        "Bajo": 0.22
    },
    "umbrales": {
        "Muy Alto": 0.74,
        "Alto": 0.63,
        "Medio": 0.40,
        "Bajo": 0.00,
        "Muy Bajo": 0.00
    },
    "perdida_esperada": {
        # Fuera de CITSU: amenaza tsunami nula en este modelo.
        "Muy Bajo": (0.00, 0.00),
        # Dentro de CITSU con IR < 0.30: existe exposición, por eso se distingue como Bajo.
        "Bajo": (0.00, 0.20),
        "Medio": (0.20, 0.40),
        "Alto": (0.40, 0.80),
        "Muy Alto": (0.80, 1.00)
    }
}


def normalizar_texto(valor):
    texto = unicodedata.normalize("NFKD", str(valor))
    texto = "".join(
        caracter for caracter in texto
        if not unicodedata.combining(caracter)
    )
    return texto.lower().strip()


def puntaje_amenaza_desde_citsu(categoria, en_citsu=None):
    """
    Convierte la categoría o descripción CITSU en puntaje de amenaza.

    Muy bajo:  altura 0    -> 0.00
    Bajo:      0 a 1 m     -> 0.10
    Medio:     1 a 2 m     -> 0.56
    Alto:      2 a 4 m     -> 0.84
    Muy alto:  más de 4 m  -> 1.00
    Fuera CITSU             -> 0.00

    Regla adicional:
    - Si el proyecto intersecta una geometría CITSU pero la etiqueta del KMZ
      no permite identificar una banda de altura, se asigna amenaza Bajo (0.10)
      como mínimo, para no confundir una ubicación dentro de CITSU con una
      ubicación fuera de CITSU.
    """
    texto = normalizar_texto(categoria)

    # La condición espacial manda: fuera de CITSU = amenaza 0.
    if en_citsu is False or "fuera citsu" in texto:
        return CONFIG_IR["escalas_amenaza"]["Muy bajo"], "Muy bajo"

    if (
        "sin informacion" in texto
        or "sin categoría" in texto
        or "sin categoria" in texto
        or texto in {"", "nan", "none", "<na>"}
    ):
        if en_citsu:
            return CONFIG_IR["escalas_amenaza"]["Bajo"], "Bajo"
        return CONFIG_IR["escalas_amenaza"]["Muy bajo"], "Muy bajo"

    if "muy alto" in texto or ">4" in texto or "mas de 4" in texto:
        return CONFIG_IR["escalas_amenaza"]["Muy alto"], "Muy alto"

    if "alto" in texto or "2 - 4" in texto or "2-4" in texto:
        return CONFIG_IR["escalas_amenaza"]["Alto"], "Alto"

    if "medio" in texto or "1 - 2" in texto or "1-2" in texto:
        return CONFIG_IR["escalas_amenaza"]["Medio"], "Medio"

    if "bajo" in texto or "0 - 1" in texto or "0-1" in texto:
        return CONFIG_IR["escalas_amenaza"]["Bajo"], "Bajo"

    if "muy bajo" in texto or texto in {"0", "0.0", "0,0"}:
        # Si está dentro de CITSU, 0 m explícito puede mantenerse en 0.
        return CONFIG_IR["escalas_amenaza"]["Muy bajo"], "Muy bajo"

    # Reconocimiento numérico restringido a expresiones de altura/rango.
    # Evita interpretar años de edición (2019, 2023, etc.) como altura de tsunami.
    patrones_altura = re.findall(
        r"(?:altura|m|metro|metros)?\s*(\d+(?:[.,]\d+)?)\s*(?:m|metro|metros)?",
        texto
    )
    numeros = [float(x.replace(",", ".")) for x in patrones_altura]
    numeros = [x for x in numeros if 0 <= x <= 20]

    if numeros:
        altura_maxima = max(numeros)
        if altura_maxima > 4:
            return CONFIG_IR["escalas_amenaza"]["Muy alto"], "Muy alto"
        if altura_maxima > 2:
            return CONFIG_IR["escalas_amenaza"]["Alto"], "Alto"
        if altura_maxima > 1:
            return CONFIG_IR["escalas_amenaza"]["Medio"], "Medio"
        if altura_maxima > 0:
            return CONFIG_IR["escalas_amenaza"]["Bajo"], "Bajo"

    # Si hay intersección con CITSU, nunca se trata como fuera de amenaza.
    if en_citsu:
        return CONFIG_IR["escalas_amenaza"]["Bajo"], "Bajo"

    return CONFIG_IR["escalas_amenaza"]["Muy bajo"], "Muy bajo"



def texto_descriptivo_proyecto(fila):
    """
    Une los campos descriptivos disponibles para inferir materialidad
    y antigüedad normativa del proyecto.
    """
    candidatos = [
        "NOMBRE INICIATIVA",
        "NOMBRE",
        "PROCESO",
        "ETAPA POST",
        "SECTOR",
        "SUBSECTOR",
        "DESCRIPCION",
        "DESCRIPCIÓN",
        "MATERIALIDAD",
        "SISTEMA ESTRUCTURAL"
    ]

    partes = []

    for candidato in candidatos:
        columna = buscar_columna(fila, [candidato])

        if columna is not None:
            valor = fila[columna]

            if not pd.isna(valor):
                partes.append(str(valor))

    return normalizar_texto(" ".join(partes))


def inferir_materialidad_proyecto(fila):
    """
    Regla automática solicitada:

    - Se supone hormigón armado para todos los proyectos.
    - Cuando el proyecto indica que es prefabricado, se asigna
      materialidad media (acero / estructura reforzada).
    - Si el texto indica explícitamente adobe, madera o albañilería
      no reforzada, se utiliza materialidad alta.
    """
    texto = texto_descriptivo_proyecto(fila)

    if any(
        termino in texto
        for termino in [
            "adobe",
            "albanileria no reforzada",
            "madera"
        ]
    ):
        return "Adobe, albañilería no reforzada o madera"

    if "prefabric" in texto:
        return "Acero / estructura reforzada (prefabricado)"

    return "Hormigón armado"


def inferir_antiguedad_proyecto(fila):
    """
    Regla automática solicitada:

    - Los proyectos se consideran posteriores a 2010.
    - Las ampliaciones se consideran potencialmente anteriores a 2010,
      aplicando un criterio conservador.
    """
    texto = texto_descriptivo_proyecto(fila)

    if "ampliacion" in texto:
        return 2009, "Pre 2010 (supuesto para ampliación)"

    return 2011, "Post 2010 (supuesto general)"


def incorporar_indice_riesgo_todos(gdf):
    """
    Calcula el Índice de Riesgo para todos los proyectos del GeoDataFrame.
    """
    resultado = gdf.copy()

    registros = []

    for _, fila in resultado.iterrows():
        materialidad = inferir_materialidad_proyecto(fila)
        anio_construccion, supuesto_antiguedad = (
            inferir_antiguedad_proyecto(fila)
        )

        calculo = calcular_indice_riesgo(
            fila.get("CATEGORIA_CITSU", "SIN INFORMACIÓN"),
            materialidad,
            anio_construccion,
            en_citsu=bool(fila.get("EN_CITSU", False))
        )

        registros.append(
            {
                "MATERIALIDAD_ANALISIS": materialidad,
                "AÑO_CONSTRUCCION_ANALISIS": anio_construccion,
                "SUPUESTO_ANTIGUEDAD": supuesto_antiguedad,
                "ESCALA_AMENAZA": calculo["escala_amenaza"],
                "PUNTAJE_AMENAZA": calculo["puntaje_amenaza"],
                "ESCALA_MATERIALIDAD": calculo["escala_materialidad"],
                "PUNTAJE_MATERIALIDAD": calculo["puntaje_materialidad"],
                "ESCALA_ANTIGUEDAD": calculo["escala_antiguedad"],
                "PUNTAJE_ANTIGUEDAD": calculo["puntaje_antiguedad"],
                "INDICE_VULNERABILIDAD": calculo[
                    "indice_vulnerabilidad"
                ],
                "INDICE_RIESGO": calculo["indice_riesgo"],
                "NIVEL_RIESGO": calculo["nivel_riesgo"]
            }
        )

    indicadores = pd.DataFrame(
        registros,
        index=resultado.index
    )

    for columna in indicadores.columns:
        resultado[columna] = indicadores[columna]

    columna_costo = buscar_columna(
        resultado,
        [
            "COSTO TOTAL M$",
            "COSTO TOTAL",
            "COSTO"
        ]
    )

    if columna_costo is not None:
        resultado["COSTO_TOTAL_NUMERICO_M$"] = resultado[
            columna_costo
        ].apply(convertir_costo_a_numero)

        resultado["PERDIDA_MIN_PCT"] = resultado[
            "NIVEL_RIESGO"
        ].map(
            lambda nivel: obtener_rango_perdida_esperada(nivel)[0]
        )

        resultado["PERDIDA_MAX_PCT"] = resultado[
            "NIVEL_RIESGO"
        ].map(
            lambda nivel: obtener_rango_perdida_esperada(nivel)[1]
        )

        resultado["PERDIDA_ESPERADA_MIN_M$"] = (
            resultado["COSTO_TOTAL_NUMERICO_M$"]
            * resultado["PERDIDA_MIN_PCT"]
        )

        resultado["PERDIDA_ESPERADA_MAX_M$"] = (
            resultado["COSTO_TOTAL_NUMERICO_M$"]
            * resultado["PERDIDA_MAX_PCT"]
        )
    else:
        resultado["COSTO_TOTAL_NUMERICO_M$"] = None
        resultado["PERDIDA_MIN_PCT"] = None
        resultado["PERDIDA_MAX_PCT"] = None
        resultado["PERDIDA_ESPERADA_MIN_M$"] = None
        resultado["PERDIDA_ESPERADA_MAX_M$"] = None

    return resultado


def puntaje_materialidad(materialidad):
    """
    Alto: adobe, albañilería no reforzada o madera -> 1.00
    Medio: acero o estructura reforzada            -> 0.53
    Bajo: albañilería reforzada u hormigón armado  -> 0.22
    """
    texto = normalizar_texto(materialidad)

    if any(
        termino in texto
        for termino in [
            "adobe",
            "albanileria no reforzada",
            "madera"
        ]
    ):
        return CONFIG_IR["escalas_materialidad"]["Alto"], "Alto"

    if any(
        termino in texto
        for termino in [
            "acero",
            "estructura reforzada"
        ]
    ):
        return CONFIG_IR["escalas_materialidad"]["Medio"], "Medio"

    if any(
        termino in texto
        for termino in [
            "albanileria reforzada",
            "hormigon armado",
            "hormigon"
        ]
    ):
        return CONFIG_IR["escalas_materialidad"]["Bajo"], "Bajo"

    return None, "Sin información"


def puntaje_antiguedad(anio_construccion):
    """
    Pre 2010  -> 1.00 (Muy alto)
    Post 2010 -> 0.22 (Bajo)

    Para el año 2010 se adopta el criterio conservador Pre 2010.
    """
    try:
        anio = int(float(str(anio_construccion).strip()))
    except (TypeError, ValueError):
        return None, "Sin información"

    if anio <= 2010:
        return CONFIG_IR["escalas_amenaza"]["Muy alto"], "Muy alto"

    return CONFIG_IR["escalas_materialidad"]["Bajo"], "Bajo"


def clasificar_indice_riesgo(indice, en_citsu=False):
    """
    Clasifica el Índice de Riesgo.

    Muy Alto : IR >= 0.74
    Alto     : 0.74 <= IR < 0.63
    Medio    : 0.40 <= IR < 0.63
    Bajo     : IR < 0.40, pero el proyecto está dentro de CITSU
    Muy Bajo : proyecto fuera de CITSU (IR = 0 en el modelo tsunami)
    """
    if indice is None or pd.isna(indice):
        return "Sin información"

    if not en_citsu:
        return "Muy Bajo"

    umbrales = CONFIG_IR["umbrales"]

    if indice >= umbrales["Muy Alto"]:
        return "Muy Alto"
    if indice >= umbrales["Alto"]:
        return "Alto"
    if indice >= umbrales["Medio"]:
        return "Medio"

    return "Bajo"



def obtener_rango_perdida_esperada(nivel_riesgo):
    """
    Devuelve el rango mínimo y máximo de pérdida esperada
    asociado directamente a la categoría resultante del IR.
    No recalcula ni renormaliza el índice.
    """
    return CONFIG_IR["perdida_esperada"].get(
        nivel_riesgo,
        (None, None)
    )


def convertir_costo_a_numero(valor):
    """
    Convierte el costo del proyecto a número.

    La base expresa el costo en M$ (miles de pesos), por lo que el
    resultado conserva esa misma unidad.
    """
    if valor is None or pd.isna(valor):
        return None

    texto = str(valor).strip()

    if texto == "" or texto.lower() in {"nan", "none", "<na>"}:
        return None

    texto = re.sub(r"[^0-9,.-]", "", texto)

    try:
        # Formato habitual chileno: 587.771 o 587.771,50
        if "." in texto and "," in texto:
            texto = texto.replace(".", "").replace(",", ".")
        elif texto.count(".") > 1:
            texto = texto.replace(".", "")
        elif "," in texto:
            texto = texto.replace(",", ".")
        elif "." in texto:
            parte_decimal = texto.rsplit(".", 1)[-1]
            if len(parte_decimal) == 3:
                texto = texto.replace(".", "")

        return float(texto)
    except (TypeError, ValueError):
        return None


def formatear_monto_miles(valor):
    """
    Formatea un monto expresado en M$.
    """
    if valor is None or pd.isna(valor):
        return "Sin información"

    return f"{float(valor):,.0f} M$".replace(",", ".")


def calcular_perdida_monetaria(costo, nivel_riesgo):
    """
    Calcula el rango monetario de pérdida esperada:

    pérdida mínima = costo × porcentaje mínimo
    pérdida máxima = costo × porcentaje máximo
    """
    costo_numerico = convertir_costo_a_numero(costo)
    perdida_min_pct, perdida_max_pct = obtener_rango_perdida_esperada(
        nivel_riesgo
    )

    if (
        costo_numerico is None
        or perdida_min_pct is None
        or perdida_max_pct is None
    ):
        return {
            "costo_numerico": costo_numerico,
            "perdida_min_pct": perdida_min_pct,
            "perdida_max_pct": perdida_max_pct,
            "perdida_min_monetaria": None,
            "perdida_max_monetaria": None
        }

    return {
        "costo_numerico": costo_numerico,
        "perdida_min_pct": perdida_min_pct,
        "perdida_max_pct": perdida_max_pct,
        "perdida_min_monetaria": costo_numerico * perdida_min_pct,
        "perdida_max_monetaria": costo_numerico * perdida_max_pct
    }


def calcular_indice_riesgo(
    categoria_citsu,
    materialidad,
    anio_construccion,
    en_citsu=False
):
    puntaje_amenaza, escala_amenaza = puntaje_amenaza_desde_citsu(
        categoria_citsu,
        en_citsu=en_citsu
    )

    puntaje_mat, escala_materialidad = puntaje_materialidad(materialidad)
    puntaje_ant, escala_antiguedad = puntaje_antiguedad(anio_construccion)

    if puntaje_mat is None or puntaje_ant is None:
        return {
            "puntaje_amenaza": puntaje_amenaza,
            "escala_amenaza": escala_amenaza,
            "puntaje_materialidad": puntaje_mat,
            "escala_materialidad": escala_materialidad,
            "puntaje_antiguedad": puntaje_ant,
            "escala_antiguedad": escala_antiguedad,
            "indice_vulnerabilidad": None,
            "indice_riesgo": None,
            "nivel_riesgo": "Sin información"
        }

    ponderaciones = CONFIG_IR["ponderaciones"]

    indice_vulnerabilidad = (
        puntaje_mat * ponderaciones["materialidad"]
        + puntaje_ant * ponderaciones["antiguedad"]
    )
    indice_vulnerabilidad = round(indice_vulnerabilidad, 3)

    # Regla de exposición: fuera de CITSU no existe riesgo tsunami en este modelo.
    if not en_citsu:
        indice_riesgo = 0.0
    else:
        indice_riesgo = (
            puntaje_amenaza * ponderaciones["amenaza"]
            + indice_vulnerabilidad * ponderaciones["vulnerabilidad"]
        )
        indice_riesgo = round(indice_riesgo, 3)

    return {
        "puntaje_amenaza": puntaje_amenaza,
        "escala_amenaza": escala_amenaza,
        "puntaje_materialidad": puntaje_mat,
        "escala_materialidad": escala_materialidad,
        "puntaje_antiguedad": puntaje_ant,
        "escala_antiguedad": escala_antiguedad,
        "indice_vulnerabilidad": indice_vulnerabilidad,
        "indice_riesgo": indice_riesgo,
        "nivel_riesgo": clasificar_indice_riesgo(
            indice_riesgo,
            en_citsu=en_citsu
        )
    }



def color_nivel_riesgo(nivel):
    texto = normalizar_texto(nivel)

    if texto == "muy alto":
        return "#A92727"

    if texto == "alto":
        return "#D94841"

    if texto == "medio":
        return "#F39B36"

    if texto == "bajo":
        return "#E7B84B"

    if texto == "muy bajo":
        return "#2E9B6F"

    return "#667788"


def exportar_excel(df):
    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="Indice_Riesgo"
        )

    return output.getvalue()


@st.cache_data(show_spinner=False)
def preparar_datos_aplicacion(ruta_excel_str, archivos_kmz_info):
    """
    Carga, consolida y cruza todos los datos una sola vez.
    archivos_kmz_info es una tupla de (ruta, fecha_modificacion) para que
    Streamlit invalide el caché si cambia algún archivo.
    """
    gdf_proyectos_local = cargar_excel_proyectos(Path(ruta_excel_str))

    capas_citsu_local = []
    no_encontrados = []
    con_error = []

    for ruta_str, _mtime in archivos_kmz_info:
        archivo = Path(ruta_str)
        if not archivo.exists():
            no_encontrados.append(archivo.name)
            continue

        try:
            gdf_temp = cargar_kmz(archivo)
            if gdf_temp is not None and not gdf_temp.empty:
                gdf_temp = gdf_temp.copy()
                gdf_temp["ARCHIVO_CITSU"] = archivo.name
                capas_citsu_local.append(gdf_temp)
            else:
                con_error.append(f"{archivo.name}: sin geometrías KML válidas")
        except Exception as exc:
            con_error.append(f"{archivo.name}: {exc}")

    if capas_citsu_local:
        gdf_citsu_local = gpd.GeoDataFrame(
            pd.concat(capas_citsu_local, ignore_index=True),
            geometry="geometry",
            crs="EPSG:4326"
        )
    else:
        gdf_citsu_local = None

    resultado_local = clasificar_citsu(
        gdf_proyectos_local,
        gdf_citsu_local
    )
    resultado_local = incorporar_indice_riesgo_todos(resultado_local)

    return (
        gdf_proyectos_local,
        gdf_citsu_local,
        resultado_local,
        no_encontrados,
        con_error,
        len(capas_citsu_local)
    )


# =========================================================
# CARGA PRINCIPAL
# =========================================================

if not ARCHIVO_PROYECTOS.exists():
    st.error(
        "No se encontró la base de proyectos. "
        "Agrega el archivo `MDS_PROYECTOS 2024 2026.xlsx` "
        "dentro de la carpeta `data` del repositorio."
    )
    st.stop()

with st.spinner("Procesando proyectos y cartas CITSU..."):
    try:
        archivos_kmz_info = tuple(
            (
                str(ruta),
                ruta.stat().st_mtime if ruta.exists() else None
            )
            for ruta in ARCHIVOS_CITSU
        )

        (
            gdf_proyectos,
            gdf_citsu,
            gdf_resultado,
            archivos_no_encontrados,
            archivos_con_error,
            cantidad_citsu_cargadas
        ) = preparar_datos_aplicacion(
            str(ARCHIVO_PROYECTOS),
            archivos_kmz_info
        )

    except Exception as error:
        st.error(f"Error al preparar los datos: {error}")
        st.stop()

if cantidad_citsu_cargadas > 0:
    st.caption(
        f"Cartas CITSU disponibles: {cantidad_citsu_cargadas} de {len(ARCHIVOS_CITSU)}"
    )
else:
    st.warning("No fue posible cargar ninguna carta CITSU.")

if archivos_no_encontrados:
    with st.expander(
        f"Archivos CITSU no encontrados ({len(archivos_no_encontrados)})"
    ):
        for nombre in archivos_no_encontrados:
            st.write(f"• {nombre}")

if archivos_con_error:
    with st.expander(
        f"Archivos CITSU con error ({len(archivos_con_error)})"
    ):
        for detalle in archivos_con_error:
            st.write(f"• {detalle}")

nombre_col = (
    "NOMBRE INICIATIVA"
    if "NOMBRE INICIATIVA" in gdf_resultado.columns
    else gdf_resultado.columns[0]
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown(
    """
    <div class="sidebar-brand">
        <div class="sidebar-brand-title">🌊 GeoRiskAI Sentinel</div>
        <div class="sidebar-brand-subtitle">
            Inteligencia territorial para decisiones de inversión resiliente
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown("### Filtros de análisis")

gdf_filtrado = gdf_resultado.copy()

if "REGION" in gdf_resultado.columns:
    regiones = sorted(
        gdf_resultado["REGION"]
        .dropna()
        .astype(str)
        .unique()
    )

    region_sel = st.sidebar.selectbox(
        "Región",
        ["Todas"] + regiones
    )

    if region_sel != "Todas":
        gdf_filtrado = gdf_filtrado[
            gdf_filtrado["REGION"].astype(str)
            == region_sel
        ]

if "COMUNA" in gdf_filtrado.columns:
    comunas = sorted(
        gdf_filtrado["COMUNA"]
        .dropna()
        .astype(str)
        .unique()
    )

    comuna_sel = st.sidebar.selectbox(
        "Comuna",
        ["Todas"] + comunas
    )

    if comuna_sel != "Todas":
        gdf_filtrado = gdf_filtrado[
            gdf_filtrado["COMUNA"].astype(str)
            == comuna_sel
        ]

categorias = sorted(
    gdf_filtrado["CATEGORIA_CITSU"]
    .dropna()
    .astype(str)
    .unique()
)

categoria_sel = st.sidebar.selectbox(
    "Categoría CITSU",
    ["Todas"] + categorias
)

if categoria_sel != "Todas":
    gdf_filtrado = gdf_filtrado[
        gdf_filtrado["CATEGORIA_CITSU"].astype(str)
        == categoria_sel
    ]

if gdf_filtrado.empty:
    st.warning(
        "No hay proyectos disponibles para los filtros seleccionados."
    )
    st.stop()

# Se construye un identificador único para evitar confundir proyectos
# con nombres repetidos.
columna_bip_selector = buscar_columna(
    gdf_filtrado,
    ["CODIGO BIP", "CÓDIGO BIP", "COD BIP"]
)

gdf_filtrado = gdf_filtrado.copy()

if columna_bip_selector is not None:
    gdf_filtrado["_ETIQUETA_PROYECTO"] = (
        gdf_filtrado[columna_bip_selector].astype(str)
        + " · "
        + gdf_filtrado[nombre_col].astype(str)
    )
else:
    gdf_filtrado["_ETIQUETA_PROYECTO"] = (
        gdf_filtrado[nombre_col].astype(str)
    )

opciones_proyecto = (
    gdf_filtrado["_ETIQUETA_PROYECTO"]
    .drop_duplicates()
    .tolist()
)

proyecto_desde_mapa = st.session_state.pop(
    "_proyecto_desde_mapa",
    None
)

if (
    proyecto_desde_mapa is not None
    and proyecto_desde_mapa in opciones_proyecto
):
    st.session_state["selector_proyecto"] = proyecto_desde_mapa

if (
    "selector_proyecto" not in st.session_state
    or st.session_state["selector_proyecto"] not in opciones_proyecto
):
    st.session_state["selector_proyecto"] = opciones_proyecto[0]

proyecto_sel = st.sidebar.selectbox(
    "Proyecto",
    opciones_proyecto,
    key="selector_proyecto"
)

gdf_seleccion = gdf_filtrado[
    gdf_filtrado["_ETIQUETA_PROYECTO"] == proyecto_sel
]

proyecto = gdf_seleccion.iloc[0]

# Estas variables deben definirse inmediatamente después de seleccionar
# el proyecto, porque se utilizan en el cálculo multicriterio y en la ficha.
categoria_actual = str(
    proyecto.get("CATEGORIA_CITSU", "SIN INFORMACIÓN")
)
color_actual = color_categoria(categoria_actual)

st.sidebar.markdown("### Ubicación seleccionada")

col_lat, col_lon = st.sidebar.columns(2)

with col_lat:
    st.text_input(
        "Latitud",
        value=f"{proyecto.geometry.y:.5f}",
        disabled=True
    )

with col_lon:
    st.text_input(
        "Longitud",
        value=f"{proyecto.geometry.x:.5f}",
        disabled=True
    )

if "CODIGO BIP" in proyecto.index:
    st.sidebar.text_input(
        "Código BIP",
        value=str(proyecto["CODIGO BIP"]),
        disabled=True
    )

st.sidebar.markdown("### Vulnerabilidad física")

materialidad_seleccionada = str(
    proyecto.get(
        "MATERIALIDAD_ANALISIS",
        "Hormigón armado"
    )
)

anio_construccion = int(
    proyecto.get(
        "AÑO_CONSTRUCCION_ANALISIS",
        2011
    )
)

supuesto_antiguedad = str(
    proyecto.get(
        "SUPUESTO_ANTIGUEDAD",
        "Post 2010 (supuesto general)"
    )
)

resultado_indice = {
    "puntaje_amenaza": float(
        proyecto.get("PUNTAJE_AMENAZA", 0)
    ),
    "escala_amenaza": str(
        proyecto.get("ESCALA_AMENAZA", "Muy bajo")
    ),
    "puntaje_materialidad": float(
        proyecto.get("PUNTAJE_MATERIALIDAD", 0.22)
    ),
    "escala_materialidad": str(
        proyecto.get("ESCALA_MATERIALIDAD", "Bajo")
    ),
    "puntaje_antiguedad": float(
        proyecto.get("PUNTAJE_ANTIGUEDAD", 0.22)
    ),
    "escala_antiguedad": str(
        proyecto.get("ESCALA_ANTIGUEDAD", "Bajo")
    ),
    "indice_vulnerabilidad": float(
        proyecto.get("INDICE_VULNERABILIDAD", 0.22)
    ),
    "indice_riesgo": float(
        proyecto.get("INDICE_RIESGO", 0)
    ),
    "nivel_riesgo": str(
        proyecto.get("NIVEL_RIESGO", "Bajo")
    )
}

st.sidebar.text_input(
    "Materialidad inferida",
    value=materialidad_seleccionada,
    disabled=True
)

st.sidebar.text_input(
    "Antigüedad normativa",
    value=supuesto_antiguedad,
    disabled=True
)

with st.sidebar.expander("Diagnóstico de columnas"):
    st.write("Columnas detectadas en la base:")
    st.write([str(columna) for columna in gdf_resultado.columns])

st.sidebar.markdown(
    """
    <div class="mini-note">
        El índice se calcula para todos los proyectos con amenaza CITSU 70% y vulnerabilidad física 30%. La materialidad se supone de hormigón armado, salvo proyectos prefabricados; las ampliaciones se consideran conservadoramente pre-2010.
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HERO
# =========================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-brand">Plataforma de inteligencia territorial</div>
        <h1 class="hero-title">Evaluación de exposición costera y riesgo de inversión</h1>
        <div class="hero-subtitle">
            Visualiza proyectos públicos, identifica su relación con la carta CITSU
            y genera información estratégica para decisiones más seguras, resilientes
            y trazables.
        </div>
        <div class="status-pill">● Sistema activo · Análisis geoespacial automatizado</div>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# KPIs
# =========================================================

total = len(gdf_resultado)

en_citsu = int(
    gdf_resultado["EN_CITSU"].fillna(False).sum()
)

fuera_citsu = total - en_citsu

porcentaje_citsu = (
    round(en_citsu / total * 100, 1)
    if total > 0
    else 0
)

c1, c2, c3, c4 = st.columns([1.25, 1, 1, 1])

with c1:
    st.markdown(
        f"""
        <div class="kpi-card risk-card"
             style="background:linear-gradient(135deg,{color_actual},#F7A34A);">
            <div class="kpi-label" style="color:rgba(255,255,255,0.82);">
                Categoría CITSU
            </div>
            <div class="risk-value">{categoria_actual}</div>
            <div class="kpi-note" style="color:rgba(255,255,255,0.80);">
                Proyecto seleccionado
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c2:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Proyectos analizados</div>
            <div class="kpi-value">{total:,}</div>
            <div class="kpi-note">Base georreferenciada MDSF</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c3:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">En zona CITSU</div>
            <div class="kpi-value" style="color:#D94841;">{en_citsu:,}</div>
            <div class="kpi-note">{porcentaje_citsu}% del total analizado</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c4:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Fuera de zona CITSU</div>
            <div class="kpi-value" style="color:#2E9B6F;">{fuera_citsu:,}</div>
            <div class="kpi-note">Sin intersección cartográfica</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown(
    '<div class="section-title">Índice de Riesgo Multicriterio</div>',
    unsafe_allow_html=True
)

ir1, ir2, ir3, ir4, ir5 = st.columns(5)

nivel_indice = resultado_indice["nivel_riesgo"]
color_indice = color_nivel_riesgo(nivel_indice)

perdida_min_pct, perdida_max_pct = obtener_rango_perdida_esperada(
    nivel_indice
)

rango_perdida_texto = (
    f"{perdida_min_pct:.0%} – {perdida_max_pct:.0%}"
    if perdida_min_pct is not None and perdida_max_pct is not None
    else "Sin información"
)

perdida_min_monetaria = proyecto.get(
    "PERDIDA_ESPERADA_MIN_M$",
    None
)
perdida_max_monetaria = proyecto.get(
    "PERDIDA_ESPERADA_MAX_M$",
    None
)
costo_total_numerico = proyecto.get(
    "COSTO_TOTAL_NUMERICO_M$",
    None
)

rango_perdida_monetaria_texto = (
    f"{formatear_monto_miles(perdida_min_monetaria)} – "
    f"{formatear_monto_miles(perdida_max_monetaria)}"
    if (
        perdida_min_monetaria is not None
        and perdida_max_monetaria is not None
        and not pd.isna(perdida_min_monetaria)
        and not pd.isna(perdida_max_monetaria)
    )
    else "Sin información"
)

valor_indice_texto = (
    f'{resultado_indice["indice_riesgo"]:.3f}'
    if resultado_indice["indice_riesgo"] is not None
    else "S/I"
)

valor_vulnerabilidad_texto = (
    f'{resultado_indice["indice_vulnerabilidad"]:.3f}'
    if resultado_indice["indice_vulnerabilidad"] is not None
    else "S/I"
)

with ir1:
    st.markdown(
        f"""
        <div class="kpi-card risk-card"
             style="background:linear-gradient(135deg,{color_indice},#F4A64D);">
            <div class="kpi-label" style="color:rgba(255,255,255,0.82);">
                Nivel de riesgo
            </div>
            <div class="risk-value">{nivel_indice}</div>
            <div class="kpi-note" style="color:rgba(255,255,255,0.82);">
                Índice normalizado: {valor_indice_texto}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with ir2:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Rango de pérdida esperada</div>
            <div class="kpi-value" style="font-size:24px;">
                {rango_perdida_texto}
            </div>
            <div class="kpi-note">
                Porcentaje estimado del costo del proyecto
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with ir3:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Costo total del proyecto</div>
            <div class="kpi-value" style="font-size:22px;">
                {formatear_monto_miles(costo_total_numerico)}
            </div>
            <div class="kpi-note">
                Monto informado en la base de proyectos
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with ir4:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Pérdida mínima estimada</div>
            <div class="kpi-value" style="font-size:22px;color:#2E9B6F;">
                {formatear_monto_miles(perdida_min_monetaria)}
            </div>
            <div class="kpi-note">
                Límite inferior · {perdida_min_pct:.0%} del costo
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with ir5:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Pérdida máxima estimada</div>
            <div class="kpi-value" style="font-size:22px;color:{color_indice};">
                {formatear_monto_miles(perdida_max_monetaria)}
            </div>
            <div class="kpi-note">
                Límite superior · {perdida_max_pct:.0%} del costo
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# MAPA Y PANEL EJECUTIVO
# =========================================================

st.markdown(
    '<div class="section-title">Análisis territorial del proyecto</div>',
    unsafe_allow_html=True
)

col_info, col_mapa = st.columns([1.35, 2.65])

with col_mapa:
    centro = [
        proyecto.geometry.y,
        proyecto.geometry.x
    ]

    mapa = folium.Map(
        location=centro,
        zoom_start=14,
        tiles=None,
        control_scale=True
    )

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        name="Satélite Esri",
        attr="Esri World Imagery",
        control=True,
        show=True
    ).add_to(mapa)

    folium.TileLayer(
        tiles="CartoDB positron",
        name="Mapa claro",
        control=True
    ).add_to(mapa)

    folium.TileLayer(
        tiles="OpenStreetMap",
        name="Mapa urbano",
        control=True
    ).add_to(mapa)

    gdf_citsu_mapa = preparar_citsu_para_mapa(
        gdf_citsu,
        proyecto
    )

    if gdf_citsu_mapa is not None and not gdf_citsu_mapa.empty:
        folium.GeoJson(
            gdf_citsu_mapa,
            name="Carta CITSU local",
            style_function=lambda feature: {
                "fillColor": "#F26A3D",
                "color": "#C53A32",
                "weight": 1.2,
                "fillOpacity": 0.30
            },
            highlight_function=lambda feature: {
                "weight": 2.5,
                "fillOpacity": 0.40
            }
        ).add_to(mapa)

    grupo_proyectos = folium.FeatureGroup(
        name="Proyectos",
        show=True
    )

    for _, row in gdf_filtrado.iterrows():
        categoria = row["CATEGORIA_CITSU"]
        color = color_folium(categoria)
        etiqueta_mapa = str(row["_ETIQUETA_PROYECTO"])

        popup_html = f"""
        <div style="width:270px;font-family:Segoe UI,Arial;">
            <div style="font-size:14px;font-weight:800;color:#0A2F57;
                        margin-bottom:8px;">
                {row.get(nombre_col, "Proyecto")}
            </div>
            <div style="font-size:12px;margin-bottom:4px;">
                <b>Categoría CITSU:</b> {categoria}
            </div>
            <div style="font-size:12px;margin-bottom:4px;">
                <b>Intersección:</b> {"Sí" if row["EN_CITSU"] else "No"}
            </div>
            <div style="font-size:11px;color:#6B7F92;">
                {row.geometry.y:.5f}, {row.geometry.x:.5f}
            </div>
        </div>
        """

        folium.CircleMarker(
            location=[
                row.geometry.y,
                row.geometry.x
            ],
            radius=7,
            color="white",
            weight=2,
            fill=True,
            fill_color=color,
            fill_opacity=0.95,
            popup=folium.Popup(
                popup_html,
                max_width=320
            ),
            tooltip=folium.Tooltip(
                etiqueta_mapa,
                sticky=True
            )
        ).add_to(grupo_proyectos)

    grupo_proyectos.add_to(mapa)

    folium.Marker(
        location=centro,
        popup=folium.Popup(
            f"<b>{proyecto.get(nombre_col, 'Proyecto seleccionado')}</b>",
            max_width=300
        ),
        tooltip="Proyecto seleccionado",
        icon=folium.Icon(
            color=color_folium(categoria_actual),
            icon="info-sign"
        )
    ).add_to(mapa)

    folium.LayerControl(
        collapsed=False
    ).add_to(mapa)

    datos_mapa = st_folium(
        mapa,
        width=None,
        height=660,
        use_container_width=True,
        key="mapa_analisis_territorial",
        returned_objects=[
            "last_object_clicked",
            "last_object_clicked_tooltip"
        ]
    )

    objeto_clic = (
        datos_mapa.get("last_object_clicked")
        if datos_mapa
        else None
    )

    tooltip_clic = (
        datos_mapa.get("last_object_clicked_tooltip")
        if datos_mapa
        else None
    )

    etiqueta_clic = None

    if tooltip_clic in opciones_proyecto:
        etiqueta_clic = tooltip_clic

    if etiqueta_clic is None and objeto_clic:
        lat_clic = objeto_clic.get("lat")
        lon_clic = objeto_clic.get("lng")

        if lat_clic is not None and lon_clic is not None:
            distancias = (
                (gdf_filtrado.geometry.y - float(lat_clic)) ** 2
                + (gdf_filtrado.geometry.x - float(lon_clic)) ** 2
            )

            indice_cercano = distancias.idxmin()

            if float(distancias.loc[indice_cercano]) <= 0.00000025:
                etiqueta_clic = str(
                    gdf_filtrado.loc[
                        indice_cercano,
                        "_ETIQUETA_PROYECTO"
                    ]
                )

    if (
        etiqueta_clic is not None
        and etiqueta_clic != proyecto_sel
    ):
        st.session_state["_proyecto_desde_mapa"] = etiqueta_clic
        st.rerun()

    st.caption(
        "Haz clic sobre un marcador para actualizar automáticamente "
        "la ficha ejecutiva y el Índice de Riesgo."
    )

    if bool(proyecto["EN_CITSU"]):
        recomendaciones_tsunami = (
            '<div class="recommendation">'
            '<div class="recommendation-title">Recomendaciones para riesgo por tsunami</div>'
            '<ul>'
            '<li>Validar la altura de inundación y la categoría CITSU con antecedentes oficiales del SHOA.</li>'
            '<li>Verificar rutas de evacuación señalizadas hacia zonas seguras y puntos de encuentro.</li>'
            '<li>Estimar los tiempos de evacuación peatonal y contrastarlos con los protocolos comunales.</li>'
            '<li>Incorporar medidas de diseño resiliente y protección de equipos e instalaciones críticas.</li>'
            '<li>Ubicar sistemas eléctricos, archivos y servicios esenciales sobre cotas de seguridad cuando corresponda.</li>'
            '<li>Coordinar el plan de emergencia con SENAPRED, el municipio y los organismos sectoriales competentes.</li>'
            '<li>Realizar simulacros periódicos y mantener actualizado el protocolo de continuidad operacional.</li>'
            '</ul>'
            '</div>'
        )
    else:
        recomendaciones_tsunami = (
            '<div class="recommendation">'
            '<div class="recommendation-title">Recomendaciones preventivas para riesgo por tsunami</div>'
            '<ul>'
            '<li>Confirmar que el emplazamiento se mantiene fuera de la zona de inundación de la carta CITSU vigente.</li>'
            '<li>Revisar la proximidad y accesibilidad a rutas de evacuación, zonas seguras y puntos de encuentro.</li>'
            '<li>Evaluar la continuidad operacional ante cortes de caminos, energía, comunicaciones y servicios básicos.</li>'
            '<li>Mantener señalización, protocolos de emergencia y coordinación con las autoridades locales.</li>'
            '<li>Actualizar el análisis si cambia la localización, el diseño del proyecto o la cartografía oficial.</li>'
            '</ul>'
            '</div>'
        )

    st.markdown(
        recomendaciones_tsunami,
        unsafe_allow_html=True
    )

with col_info:
    # Reconocimiento robusto de los nombres reales de las columnas del Excel
    nombre_proyecto = valor_proyecto(
        proyecto,
        [
            "NOMBRE INICIATIVA",
            "NOMBRE",
            "NOMBRE DEL PROYECTO",
            "INICIATIVA"
        ]
    )

    codigo_bip = valor_proyecto(
        proyecto,
        [
            "CODIGO BIP",
            "CÓDIGO BIP",
            "COD BIP"
        ]
    )

    region = valor_proyecto(
        proyecto,
        [
            "REGION",
            "REGIÓN"
        ]
    )

    provincia = valor_proyecto(
        proyecto,
        [
            "PROVINCIA",
            "PROVINCI",
            "NOMBRE PROVINCIA",
            "PROVINCIA INICIATIVA"
        ]
    )

    comuna = valor_proyecto(
        proyecto,
        [
            "COMUNA",
            "COMU",
            "NOMBRE COMUNA",
            "COMUNA INICIATIVA",
            "COMUNA POSTULACION",
            "COMUNA POSTULACIÓN"
        ]
    )

    proceso = valor_proyecto(
        proyecto,
        [
            "PROCESO",
            "PROCES"
        ]
    )

    etapa = valor_proyecto(
        proyecto,
        [
            "ETAPA POST",
            "ETAPA POSTULA",
            "ETAPA POSTULACION",
            "ETAPA POSTULACIÓN",
            "ETAPA"
        ]
    )

    anio_post = valor_proyecto(
        proyecto,
        [
            "AÑO POST",
            "ANO POST",
            "AÑO POSTULACION",
            "AÑO POSTULACIÓN"
        ]
    )

    rate = valor_proyecto(
        proyecto,
        [
            "RATE",
            "RESULTADO RATE"
        ]
    )

    costo_total = valor_proyecto(
        proyecto,
        [
            "COSTO TOTAL M$",
            "COSTO TOTAL",
            "COSTO"
        ]
    )

    sector = valor_proyecto(
        proyecto,
        [
            "SECTOR",
            "SECT"
        ]
    )

    institucion = valor_proyecto(
        proyecto,
        [
            "INSTITUCION",
            "INSTITUCIÓN",
            "INSTIT",
            "INSTITUTO"
        ]
    )

    interseccion = (
        "Sí"
        if bool(proyecto["EN_CITSU"])
        else "No"
    )

    # Protección frente a caracteres especiales que puedan romper el HTML
    nombre_html = texto_html_seguro(nombre_proyecto)
    codigo_html = texto_html_seguro(codigo_bip)
    region_html = texto_html_seguro(region)
    provincia_html = texto_html_seguro(provincia)
    comuna_html = texto_html_seguro(comuna)
    proceso_html = texto_html_seguro(proceso)
    etapa_html = texto_html_seguro(etapa)
    anio_html = texto_html_seguro(anio_post)
    rate_html = texto_html_seguro(rate)
    sector_html = texto_html_seguro(sector)
    institucion_html = texto_html_seguro(institucion)
    costo_html = texto_html_seguro(formatear_costo(costo_total))
    categoria_html = texto_html_seguro(categoria_actual)

    ficha_powerbi_html = (
        f'<div class="powerbi-shell">'
        f'<div class="powerbi-header">'
        f'<div class="powerbi-eyebrow">Ficha ejecutiva del proyecto</div>'
        f'<div class="powerbi-project-title">{nombre_html}</div>'
        f'<div class="powerbi-badges">'
        f'<span class="powerbi-badge">BIP {codigo_html}</span>'
        f'<span class="powerbi-badge">{categoria_html}</span>'
        f'<span class="powerbi-badge">{texto_html_seguro(nivel_indice)}</span>'
        f'</div>'
        f'</div>'

        f'<div class="powerbi-section">'
        f'<div class="powerbi-section-title">📌 Identificación</div>'
        f'<div class="powerbi-grid">'
        f'<div class="powerbi-metric"><div class="powerbi-metric-label">Proceso</div><div class="powerbi-metric-value">{proceso_html}</div></div>'
        f'<div class="powerbi-metric"><div class="powerbi-metric-label">Etapa</div><div class="powerbi-metric-value">{etapa_html}</div></div>'
        f'<div class="powerbi-metric"><div class="powerbi-metric-label">Año postulación</div><div class="powerbi-metric-value">{anio_html}</div></div>'
        f'<div class="powerbi-metric"><div class="powerbi-metric-label">RATE</div><div class="powerbi-metric-value">{rate_html}</div></div>'
        f'<div class="powerbi-metric"><div class="powerbi-metric-label">Sector</div><div class="powerbi-metric-value">{sector_html}</div></div>'
        f'<div class="powerbi-metric"><div class="powerbi-metric-label">Institución</div><div class="powerbi-metric-value">{institucion_html}</div></div>'
        f'</div>'
        f'</div>'

        f'<div class="powerbi-section">'
        f'<div class="powerbi-section-title">📍 Localización</div>'
        f'<div class="powerbi-grid">'
        f'<div class="powerbi-metric"><div class="powerbi-metric-label">Región</div><div class="powerbi-metric-value">{region_html}</div></div>'
        f'<div class="powerbi-metric"><div class="powerbi-metric-label">Provincia</div><div class="powerbi-metric-value">{provincia_html}</div></div>'
        f'<div class="powerbi-metric"><div class="powerbi-metric-label">Comuna</div><div class="powerbi-metric-value">{comuna_html}</div></div>'
        f'<div class="powerbi-metric"><div class="powerbi-metric-label">Coordenadas</div><div class="powerbi-metric-value">{proyecto.geometry.y:.5f}, {proyecto.geometry.x:.5f}</div></div>'
        f'</div>'
        f'</div>'

        f'<div class="powerbi-section">'
        f'<div class="powerbi-section-title">🏗️ Condición estructural</div>'
        f'<div class="powerbi-grid">'
        f'<div class="powerbi-metric"><div class="powerbi-metric-label">Materialidad</div><div class="powerbi-metric-value">{texto_html_seguro(materialidad_seleccionada)}</div></div>'
        f'<div class="powerbi-metric"><div class="powerbi-metric-label">Antigüedad normativa</div><div class="powerbi-metric-value">{texto_html_seguro(supuesto_antiguedad)}</div></div>'
        f'<div class="powerbi-metric"><div class="powerbi-metric-label">Índice vulnerabilidad</div><div class="powerbi-metric-value">{valor_vulnerabilidad_texto}</div></div>'
        f'<div class="powerbi-metric"><div class="powerbi-metric-label">Escala estructural</div><div class="powerbi-metric-value">{texto_html_seguro(resultado_indice["escala_materialidad"])}</div></div>'
        f'</div>'
        f'</div>'

        f'<div class="powerbi-footer">'
        f'Resultado preliminar basado en análisis multicriterio y cruce geoespacial. '
        f'No reemplaza validación técnica, inspección en terreno ni pronunciamiento de organismos competentes.'
        f'</div>'
        f'</div>'
    )

    st.markdown(
        ficha_powerbi_html,
        unsafe_allow_html=True
    )


# =========================================================
# DETALLE METODOLÓGICO DEL ÍNDICE
# =========================================================

with st.expander("Ver cálculo y ponderaciones del Índice de Riesgo"):
    detalle_indice = pd.DataFrame(
        [
            {
                "Factor": "Amenaza",
                "Subfactor": "Altura de inundación",
                "Ponderación factor": "66,7%",
                "Ponderación subfactor": "100%",
                "Escala": resultado_indice["escala_amenaza"],
                "Puntaje": resultado_indice["puntaje_amenaza"]
            },
            {
                "Factor": "Vulnerabilidad física",
                "Subfactor": "Materialidad",
                "Ponderación factor": "33,3%",
                "Ponderación subfactor": "75%",
                "Escala": resultado_indice["escala_materialidad"],
                "Puntaje": resultado_indice["puntaje_materialidad"]
            },
            {
                "Factor": "Vulnerabilidad física",
                "Subfactor": "Antigüedad normativa",
                "Ponderación factor": "33,3%",
                "Ponderación subfactor": "25%",
                "Escala": resultado_indice["escala_antiguedad"],
                "Puntaje": resultado_indice["puntaje_antiguedad"]
            }
        ]
    )

    st.dataframe(
        detalle_indice,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("**Configuración centralizada del modelo**")

    tabla_umbrales = pd.DataFrame(
        [
            {
                "Nivel": "Muy Alto",
                "Condición": (
                    f"IR ≥ {CONFIG_IR['umbrales']['Muy Alto']:.2f}"
                )
            },
            {
                "Nivel": "Alto",
                "Condición": (
                    f"{CONFIG_IR['umbrales']['Alto']:.2f} ≤ IR < "
                    f"{CONFIG_IR['umbrales']['Muy Alto']:.2f}"
                )
            },
            {
                "Nivel": "Medio",
                "Condición": (
                    f"{CONFIG_IR['umbrales']['Medio']:.2f} ≤ IR < "
                    f"{CONFIG_IR['umbrales']['Alto']:.2f}"
                )
            },
            {
                "Nivel": "Bajo",
                "Condición": (
                    f"IR < {CONFIG_IR['umbrales']['Medio']:.2f} y dentro de CITSU"
                )
            },
            {
                "Nivel": "Muy Bajo",
                "Condición": "Fuera de CITSU (IR = 0.00)"
            }
        ]
    )

    st.dataframe(
        tabla_umbrales,
        use_container_width=True,
        hide_index=True
    )

    st.latex(
        r"""
        IR =
        0.667 \times A
        +
        0.333 \times
        \left(
        0.75 \times M
        +
        0.25 \times N
        \right)
        """
    )

    st.write(
        "**Resultado:**",
        f"IR = {valor_indice_texto} · Nivel {nivel_indice} · "
        f"Pérdida esperada {rango_perdida_texto}"
    )

    st.caption(
        f"Umbrales implementados: Fuera de CITSU = Muy Bajo (IR 0.00); "
        f"dentro de CITSU con IR < {CONFIG_IR['umbrales']['Medio']:.2f} = Bajo; Medio ≥ "
        f"{CONFIG_IR['umbrales']['Medio']:.2f}; Alto ≥ "
        f"{CONFIG_IR['umbrales']['Alto']:.2f}; Muy Alto ≥ "
        f"{CONFIG_IR['umbrales']['Muy Alto']:.2f}."
    )


# =========================================================
# DISTRIBUCIÓN Y DESCARGA
# =========================================================

st.markdown(
    '<div class="section-title">Portafolio de proyectos</div>',
    unsafe_allow_html=True
)

col_resumen, col_descarga = st.columns([1.35, 1])

with col_resumen:
    resumen = (
        gdf_resultado["CATEGORIA_CITSU"]
        .value_counts()
        .rename_axis("Categoría CITSU")
        .reset_index(name="Cantidad")
    )

    st.markdown(
        '<div class="panel-title">Distribución según categoría CITSU</div>',
        unsafe_allow_html=True
    )

    st.bar_chart(
        resumen.set_index("Categoría CITSU"),
        use_container_width=True
    )

with col_descarga:
    st.markdown(
        '<div class="panel-title">Descarga ejecutiva</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="panel">
            <div style="font-size:14px;font-weight:800;color:#0A2F57;
                        margin-bottom:8px;">
                Base consolidada con clasificación CITSU
            </div>
            <div style="font-size:12px;color:#6B7F92;line-height:1.5;">
                Descarga la base con coordenadas, condición de intersección
                y categoría asociada a cada proyecto.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    columnas_descarga = [
        columna
        for columna in [
            "CODIGO BIP",
            "NOMBRE INICIATIVA",
            "REGION",
            "COMUNA",
            "ETAPA POST",
            "AÑO POST",
            "EN_CITSU",
            "CATEGORIA_CITSU",
            "latitud",
            "longitud"
        ]
        if columna in gdf_resultado.columns
    ]

    columnas_riesgo = [
        "MATERIALIDAD_ANALISIS",
        "AÑO_CONSTRUCCION_ANALISIS",
        "SUPUESTO_ANTIGUEDAD",
        "ESCALA_AMENAZA",
        "PUNTAJE_AMENAZA",
        "ESCALA_MATERIALIDAD",
        "PUNTAJE_MATERIALIDAD",
        "ESCALA_ANTIGUEDAD",
        "PUNTAJE_ANTIGUEDAD",
        "INDICE_VULNERABILIDAD",
        "INDICE_RIESGO",
        "NIVEL_RIESGO",
        "COSTO_TOTAL_NUMERICO_M$",
        "PERDIDA_MIN_PCT",
        "PERDIDA_MAX_PCT",
        "PERDIDA_ESPERADA_MIN_M$",
        "PERDIDA_ESPERADA_MAX_M$"
    ]

    columnas_descarga = list(
        dict.fromkeys(
            columnas_descarga + [
                columna
                for columna in columnas_riesgo
                if columna in gdf_resultado.columns
            ]
        )
    )

    df_descarga = pd.DataFrame(
        gdf_resultado[columnas_descarga]
    )

    excel_file = exportar_excel(
        df_descarga
    )

    st.download_button(
        label="Descargar base clasificada",
        data=excel_file,
        file_name="proyectos_indice_riesgo_multicriterio.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )


# =========================================================
# TABLA DETALLADA
# =========================================================

st.markdown(
    '<div class="section-title">Detalle de proyectos clasificados</div>',
    unsafe_allow_html=True
)

st.dataframe(
    df_descarga,
    use_container_width=True,
    hide_index=True
)

st.caption(
    "GeoRiskAI Sentinel · Resultado preliminar basado en cruce espacial. "
    "No reemplaza validación técnica, revisión de terreno ni pronunciamiento "
    "de organismos competentes."
)

st.markdown(
    """
    <hr style="margin-top: 2rem; margin-bottom: 0.75rem;">
    <div style="text-align:center; color:#6b7280; font-size:0.9rem;">
      © Elaborado por Orietta Valdés Rojas - Tesis UNAB
    </div>
    """,
    unsafe_allow_html=True
)
