"""Visor experimental multiamenaza; complemento, no reemplazo, de app.py."""
from __future__ import annotations
import io
import json
from pathlib import Path
import numpy as np
import pandas as pd
import folium
import streamlit as st
from folium.plugins import Draw
from streamlit_folium import st_folium
from shapely.geometry import shape, Point, mapping
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.io import MemoryFile
from rasterio.vrt import WarpedVRT
from rasterio.transform import array_bounds
from inundaciones_geo import (grid_from_polygon,load_dem_and_cover,terrain_features,
    historical_sentinel,features_for_ml,train_supervised,score_depth_tsunami,WORLDCOVER_NAMES)

st.set_page_config(page_title='Visor de inundaciones por tsunami, pluviales y fluviales',page_icon='🌊',layout='wide')
st.title('Visor de inundaciones por tsunami, pluviales y fluviales')
st.page_link('app.py', label='← Volver al visor de tsunami y catastro')
st.success('Para seleccionar un polígono: elige «Polígono dibujado», usa la herramienta de dibujo del mapa y pulsa «Analizar territorio».')
st.caption('Piloto Coquimbo–La Serena · GeoRiskAI Sentinel · complemento del visor de inversiones y cartas CITSU')
st.info('Las escenas Landsat y Sentinel-2 permiten detectar agua superficial histórica, no determinar por sí solas el máximo flujo ni la profundidad de una crecida. Los drenajes y abanicos son indicativos; los modelos supervisados requieren etiquetas observadas.')

DATA=Path(__file__).resolve().parents[1]/'data'/'MDS_PROYECTOS 2024 2026.xlsx'
@st.cache_data(show_spinner=False)
def load_projects(path):
    df=pd.read_excel(path,sheet_name='APP');df.columns=df.columns.str.strip()
    if 'GEOLOCALIZACIÓN' not in df:raise ValueError('No hay columna GEOLOCALIZACIÓN')
    coords=df['GEOLOCALIZACIÓN'].astype(str).str.extract(r'(-?\d+\.\d+)[,\s]+(-?\d+\.\d+)').astype(float)
    df['lat']=coords[0];df['lon']=coords[1]
    swap=df.lat.abs()>40;df.loc[swap,['lat','lon']]=df.loc[swap,['lon','lat']].to_numpy()
    return df[df.lat.between(-31.8,-29.1)&df.lon.between(-72.4,-70.0)].dropna(subset=['lat','lon']).copy()

try: projects=load_projects(str(DATA))
except Exception as exc:projects=pd.DataFrame();st.warning(f'Catastro no disponible: {exc}')

left,right=st.columns([1,2.3])
with left:
    st.subheader('Área de evaluación')
    mode=st.radio('Seleccionar', ['Polígono dibujado','Proyecto de inversión'],horizontal=False)
    chosen=None
    if mode=='Proyecto de inversión' and not projects.empty:
        label_col='NOMBRE INICIATIVA' if 'NOMBRE INICIATIVA' in projects else projects.columns[0]
        bip_col=next((x for x in ['CODIGO BIP','CÓDIGO BIP','CODIGO_BIP'] if x in projects),None)
        options=[f'{str(row.get(bip_col,""))} | {str(row[label_col])[:65]}' for _,row in projects.iterrows()]
        idx=st.selectbox('Proyecto del catastro',range(len(options)),format_func=lambda i:options[i]);chosen=projects.iloc[idx]
        st.caption(f'Coordenadas: {chosen.lat:.5f}, {chosen.lon:.5f}')
    st.subheader('Imágenes multitemporales')
    years=st.multiselect('Años a consultar',list(range(2000,2027)),default=[2000,2005,2010,2015,2020,2025])
    months=st.multiselect('Meses (invierno/verano)',list(range(1,13)),default=[1,2,6,7,8,9])
    resolution=st.selectbox('Resolución de análisis (m)',[30,60,90],index=0)
    buffer_m=st.slider('Entorno de cerros y cuencas (km)',1,8,3)*1000
    channel_ha=st.slider('Área aportante mínima para drenaje (ha)',2,100,15)
    slope_limit=st.slider('Pendiente de detección de talud (°)',15,45,25)
    st.caption('2000–2016: Landsat (NASA/USGS, 30 m). 2017–2026: Sentinel-2 (Copernicus, 10–20 m). El análisis raster utiliza la resolución seleccionada. No todas las fechas tienen escenas válidas.')
    st.subheader('Aprendizaje supervisado')
    event_type=st.selectbox('Amenaza a entrenar', ['fluvial','pluvial','tsunami'])
    training=st.file_uploader('Muestras etiquetadas (CSV opcional)',type='csv',help='Columnas lon,lat,inundado,tipo; profundidad_m opcional. Cada tipo se entrena por separado.')
    depth_upload=st.file_uploader('Raster de profundidad de inundación validado (GeoTIFF opcional)',type=['tif','tiff'])
    st.subheader('Vulnerabilidad del elemento seleccionado')
    material=st.selectbox('Materialidad', ['Sin información','Alta (madera/adobe)','Media (acero/reforzada)','Baja (hormigón/albañilería reforzada)'])
    normative=st.selectbox('Normativa', ['Sin información','Hasta 2010','Posterior a 2010'])
    run=st.button('Analizar territorio',type='primary',use_container_width=True)

with right:
    center=[float(chosen.lat),float(chosen.lon)] if chosen is not None else [-29.96,-71.30]
    m=folium.Map(location=center,zoom_start=13,tiles=None,control_scale=True)
    folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',name='Satélite Esri',attr='Esri',show=True).add_to(m)
    folium.TileLayer('OpenStreetMap',name='Calles').add_to(m)
    if not projects.empty:
        layer=folium.FeatureGroup(name='Catastro de inversiones',show=True)
        for _,r in projects.head(1800).iterrows():
            folium.CircleMarker([r.lat,r.lon],radius=3,fill=True,color='#F1BD4A',fill_opacity=.8,tooltip=str(r.get('NOMBRE INICIATIVA','Proyecto'))[:90]).add_to(layer)
        layer.add_to(m)
    if chosen is not None:folium.Marker(center,tooltip='Proyecto seleccionado').add_to(m)
    Draw(export=False,draw_options={'polyline':False,'rectangle':True,'circle':False,'circlemarker':False,'marker':False,'polygon':True},edit_options={'edit':False}).add_to(m)
    folium.LayerControl().add_to(m)
    map_state=st_folium(m,height=590,use_container_width=True,returned_objects=['last_active_drawing','all_drawings'],key='mapa_inundaciones')
    st.caption('Dibuja un polígono sobre el mapa satelital. En modo proyecto se analiza un entorno de 250 m alrededor de su ubicación.')

geom=None
if mode=='Proyecto de inversión' and chosen is not None:
    # Buffer en UTM, no grados.
    from shapely.ops import transform as sh_transform
    fwd=Transformer.from_crs('EPSG:4326','EPSG:32719',always_xy=True).transform
    back=Transformer.from_crs('EPSG:32719','EPSG:4326',always_xy=True).transform
    geom=sh_transform(back,sh_transform(fwd,Point(float(chosen.lon),float(chosen.lat))).buffer(250))
elif map_state and map_state.get('last_active_drawing'):
    geom=shape(map_state['last_active_drawing']['geometry'])

@st.cache_data(show_spinner='Consultando Copernicus DEM y WorldCover...',ttl=86400,max_entries=12)
def fetch_terrain(bounds_json,resolution,buffer_m,channel_ha,slope_limit):
    geom=shape(json.loads(bounds_json));grid=grid_from_polygon(geom,resolution,buffer_m)
    dem,cover,meta=load_dem_and_cover(grid)
    terr=terrain_features(dem,cover,grid,channel_ha,slope_limit)
    return grid,terr,meta

@st.cache_data(show_spinner='Procesando imágenes Landsat y Sentinel-2 históricas...',ttl=86400,max_entries=10)
def fetch_history(bounds_json,resolution,buffer_m,years,months):
    grid=grid_from_polygon(shape(json.loads(bounds_json)),resolution,buffer_m)
    return historical_sentinel(grid,years,months,max_scenes=24)


def overlay(map_obj,mask,grid,color,name,alpha=0.60):
    from folium.raster_layers import ImageOverlay
    a=np.zeros((*mask.shape,4),dtype=np.uint8)
    a[mask,:3]=color;a[mask,3]=int(alpha*255)
    tr=grid['transform'];h,w=grid['shape'];west,south,east,north=array_bounds(h,w,tr)
    convert=Transformer.from_crs(grid['crs'],'EPSG:4326',always_xy=True)
    sw=convert.transform(west,south);ne=convert.transform(east,north)
    ImageOverlay(image=a,bounds=[[sw[1],sw[0]],[ne[1],ne[0]]],name=name,interactive=False).add_to(map_obj)

if run:
    if geom is None:st.error('Primero dibuja un polígono o selecciona un proyecto.');st.stop()
    if not years or not months:st.error('Selecciona al menos un año y un mes.');st.stop()
    # Guardar geometría para evitar que un rerun por mapa la borre.
    st.session_state['inund_geom']=mapping(geom)
    st.session_state['inund_settings']=(resolution,buffer_m,channel_ha,slope_limit,tuple(years),tuple(months),event_type)

if 'inund_geom' in st.session_state:
    selected=shape(st.session_state['inund_geom'])
    resolution,buffer_m,channel_ha,slope_limit,years,months,event_type=st.session_state['inund_settings']
    with st.spinner('Calculando relieve, drenajes y escenas históricas...'):
        try:
            geo_json=json.dumps(mapping(selected),sort_keys=True)
            grid,terrain,metadata=fetch_terrain(geo_json,resolution,buffer_m,channel_ha,slope_limit)
            freq,observations,valid_count=fetch_history(geo_json,resolution,buffer_m,years,months)
        except Exception as exc:
            st.error(f'No se completó la consulta geoespacial: {exc}')
            st.info('La fuente STAC requiere conectividad y puede limitar consultas. Prueba un polígono menor o menos años.')
            st.stop()
    inside=grid['mask'];slope=terrain['slope'];cover=terrain['cover']
    st.subheader('Resultados del territorio seleccionado')
    c1,c2,c3,c4=st.columns(4)
    c1.metric('Elevación mediana (m)',f"{np.nanmedian(terrain['dem'][inside]):.1f}")
    c2.metric('Pendiente máxima (°)',f"{np.nanmax(slope[inside]):.1f}")
    c3.metric('Distancia mínima a drenaje (m)',f"{np.nanmin(terrain['dist_channel'][inside]):.0f}" if np.isfinite(terrain['dist_channel'][inside]).any() else 'Sin detectar')
    c4.metric('Distancia mínima a talud (m)',f"{np.nanmin(terrain['dist_talud'][inside]):.0f}" if np.isfinite(terrain['dist_talud'][inside]).any() else 'Sin detectar')
    st.caption('Los drenajes se estiman desde el relieve con D8 aproximado; la distancia se calcula respecto a elementos detectados, no respecto a un catastro oficial exhaustivo.')
    m2=folium.Map(location=[selected.centroid.y,selected.centroid.x],zoom_start=12,tiles=None)
    folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',name='Satélite',attr='Esri',show=True).add_to(m2)
    folium.GeoJson(mapping(selected),name='Área evaluada',style_function=lambda _: {'color':'#ffcc00','fillOpacity':.04,'weight':3}).add_to(m2)
    overlay(m2,terrain['channels'],grid,(30,115,240),'Drenajes potenciales',.9)
    overlay(m2,terrain['taludes'],grid,(225,55,50),'Taludes potenciales',.55)
    overlay(m2,terrain['fan_candidate'],grid,(240,175,30),'Posibles abanicos (no validados)',.45)
    overlay(m2,(freq>=.3)&np.isfinite(freq),grid,(25,220,230),'Agua recurrente observada (NDWI)',.65)
    overlay(m2,cover==50,grid,(175,100,195),'Suelo construido (WorldCover)',.4)
    overlay(m2,cover==10,grid,(30,160,70),'Cobertura arbórea (WorldCover)',.3)
    folium.LayerControl(collapsed=False).add_to(m2)
    st_folium(m2,height=560,use_container_width=True,key='mapa_resultados_inundaciones',returned_objects=[])
    st.markdown('**Cobertura del suelo en el polígono**')
    categories,counts=np.unique(cover[inside&np.isfinite(cover)].astype(int),return_counts=True)
    st.dataframe(pd.DataFrame({'Clase WorldCover':[WORLDCOVER_NAMES.get(int(k),str(k)) for k in categories],'% área':[round(float(v)*100/counts.sum(),1) for v in counts]}),hide_index=True)
    st.warning('WorldCover distingue construido, vegetación y árboles; no determina pavimento impermeable exacto ni materialidad estructural de viviendas. Estas requieren otras fuentes y validación.')
    st.markdown('**Imágenes históricas consultadas (Landsat / Sentinel-2)**')
    st.dataframe(pd.DataFrame(observations),use_container_width=True,hide_index=True)
    st.caption('La frecuencia NDWI representa agua superficial observada en escenas disponibles sin nubes. No identifica automáticamente crecidas máximas históricas ni su caudal.')
    st.markdown('**Análisis supervisado y profundidades**')
    features=features_for_ml(terrain,freq)
    ml=None
    if training is not None:
        try:
            ml=train_supervised(features,grid,io.BytesIO(training.getvalue()),event_type)
            st.success(f"Modelo {event_type} entrenado con {ml['muestras']} muestras. Exactitud equilibrada en reserva aleatoria: {ml['precision_equilibrada_reserva']:.2f} (exploratoria; requiere validación espacial/temporal independiente).")
            st.metric('Probabilidad máxima estimada en polígono',f"{100*np.nanmax(ml['probabilidad'][inside]):.1f}%")
        except Exception as exc:st.error(f'Entrenamiento no realizado: {exc}')
    else:st.info('No se entrenó ningún clasificador. Para entrenar, carga CSV con puntos históricos inundados y no inundados, por tipo de amenaza.')
    depth=None;source=None
    if depth_upload is not None:
        try:
            with MemoryFile(depth_upload.getvalue()) as mem:
                with mem.open() as src:
                    if src.crs is None:raise ValueError('GeoTIFF sin sistema de coordenadas')
                    with WarpedVRT(src,crs=grid['crs'],transform=grid['transform'],width=grid['shape'][1],height=grid['shape'][0],resampling=Resampling.bilinear) as vrt:
                        depth=vrt.read(1,masked=True).astype('float32').filled(np.nan)
                        depth=np.where(depth>=0,depth,np.nan)
            source='Raster de profundidad aportado por el usuario'
        except Exception as exc:st.error(f'No se pudo leer raster de profundidad: {exc}')
    elif ml and 'profundidad_estimada_m' in ml:
        depth=ml['profundidad_estimada_m'];source='Predicción estadística de profundidad (no hidráulica)'
    if depth is not None and np.isfinite(depth[inside]).any():
        max_depth=float(np.nanmax(depth[inside]));st.metric('Profundidad máxima en polígono (m)',f'{max_depth:.2f}')
        st.caption('Fuente: '+source+'; la altura es profundidad sobre el terreno, no cota absoluta.')
        if event_type=='tsunami':
            threat=float(score_depth_tsunami(np.array([max_depth]))[0]);st.metric('Puntaje de amenaza por altura (escala tsunami)',f'{threat:.2f}')
            if material!='Sin información' and normative!='Sin información':
                m_score={'Alta (madera/adobe)':1.,'Media (acero/reforzada)':.53,'Baja (hormigón/albañilería reforzada)':.22}[material]
                n_score=1. if normative=='Hasta 2010' else .22
                ir=.667*threat+.333*(.75*m_score+.25*n_score)
                st.metric('Índice multicriterio del área evaluada',f'{ir:.3f}')
                st.caption('Ponderaciones solicitadas: amenaza 66,7%; vulnerabilidad 33,3%; materialidad 75%; normativa 25%. No reemplaza el índice CITSU original de los proyectos.')
        else:st.warning('La escala de alturas tsunami NO se aplica automáticamente a inundación fluvial o pluvial sin una justificación/validación específica.')
    else:st.warning('Sin profundidades validadas: no es posible informar altura máxima de inundación ni puntaje de amenaza por altura.')
    report={'visor':'Visor de inundaciones por tsunami, pluviales y fluviales','zona':'Coquimbo','polygon':mapping(selected),'years':years,'months':months,'scenes':observations,'terrain':{'max_slope_deg':float(np.nanmax(slope[inside])),'median_elevation_m':float(np.nanmedian(terrain['dem'][inside]))},'ml_trained':ml is not None,'depth_source':source,'limitations':'No es simulación hidráulica. Drenajes y abanicos indicativos.'}
    st.download_button('Descargar ficha JSON',data=json.dumps(report,ensure_ascii=False,indent=2),file_name='inundaciones_coquimbo.json',mime='application/json')
