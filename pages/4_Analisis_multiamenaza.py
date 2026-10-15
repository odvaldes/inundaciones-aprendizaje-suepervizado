"""Evaluación territorial integrada: no combina amenazas heterogéneas en un IRD no validado."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import folium
from folium.plugins import Draw
from shapely.geometry import shape, Point, mapping
from shapely.ops import transform as geom_transform
from pyproj import Transformer
from streamlit_folium import st_folium
import streamlit as st
from inundaciones_geo import (grid_from_polygon,load_dem_and_cover,terrain_features,
    historical_sentinel,score_depth_tsunami,WORLDCOVER_NAMES)
from analisis_multiamenaza import wildfire_index,tailings_exposure,summarize

st.set_page_config(page_title='GeoRiskAI · Evaluación multiamenaza',page_icon='🗺️',layout='wide')
st.title('Visor multiamenaza · GeoRiskAI Sentinel')
st.caption('Tsunami · inundación fluvial · inundación pluvial · incendios forestales · relaves mineros')
st.page_link('app.py',label='← Volver al visor de proyectos tsunami')
st.info('Una evaluación territorial conjunta NO equivale a un riesgo validado para cada amenaza. Las profundidades de inundación y la estabilidad de relaves requieren datos independientes.')

DATA=Path(__file__).resolve().parents[1]/'data'/'MDS_PROYECTOS 2024 2026.xlsx'
@st.cache_data(show_spinner=False)
def projects_from_excel(path):
    df=pd.read_excel(path,sheet_name='APP');df.columns=df.columns.str.strip()
    xy=df['GEOLOCALIZACIÓN'].astype(str).str.extract(r'(-?\d+\.\d+)[,\s]+(-?\d+\.\d+)').astype(float)
    df['lat']=xy[0];df['lon']=xy[1]
    swap=df.lat.abs()>40
    df.loc[swap,['lat','lon']]=df.loc[swap,['lon','lat']].to_numpy()
    return df[df.lat.between(-32,-28.5)&df.lon.between(-73,-69.5)].dropna(subset=['lat','lon']).copy()
try:
    projects=projects_from_excel(str(DATA))
except Exception as exc:
    projects=pd.DataFrame();st.warning(f'Catastro no disponible: {exc}')

controls,view=st.columns([1,2.1])
with controls:
    mode=st.radio('Área de evaluación',['Polígono dibujado','Proyecto de inversión'])
    selected=None
    if mode=='Proyecto de inversión' and not projects.empty:
        name_col='NOMBRE INICIATIVA' if 'NOMBRE INICIATIVA' in projects else projects.columns[0]
        i=st.selectbox('Proyecto',range(len(projects)),format_func=lambda j:str(projects.iloc[j][name_col])[:90])
        selected=projects.iloc[i]
    elif mode=='Proyecto de inversión':
        st.warning('Carga el catastro en data/ para seleccionar proyectos.')
    resolution=st.selectbox('Resolución DEM (m)',[30,60,90],index=1)
    buffer_km=st.slider('Entorno para analizar cerros y quebradas (km)',1,8,3)
    channel_ha=st.slider('Área aportante mínima de drenaje (ha)',2,100,15)
    st.markdown('**Incendios: condiciones meteorológicas del escenario**')
    temp=st.number_input('Temperatura (°C)',-10.,55.,33.)
    humidity=st.slider('Humedad relativa (%)',0,100,25)
    wind=st.slider('Viento (km/h)',0,150,35)
    rain=st.number_input('Lluvia reciente (mm)',0.,500.,0.)
    st.caption('Estos valores son escenarios ingresados por el usuario, no meteorología histórica automática.')
    st.markdown('**Profundidad de inundación validada (opcional)**')
    depth=st.number_input('Profundidad máxima observada o modelada (m)',min_value=0.,max_value=30.,value=0.,step=.1)
    known_depth=st.checkbox('La profundidad anterior proviene de una fuente validada',value=False)
    st.caption('Sin profundidad validada no se estima altura máxima ni se asigna puntaje de tsunami.')
    historical=st.checkbox('Consultar agua superficial histórica (Landsat/Sentinel)',value=False)
    if historical:
        years=st.multiselect('Años',list(range(2000,2027)),default=[2015,2017,2023])
        months=st.multiselect('Meses',list(range(1,13)),default=[1,2,6,7,8])
    else:
        years=[];months=[]
    go=st.button('Analizar todas las amenazas',type='primary',use_container_width=True)
with view:
    center=[float(selected.lat),float(selected.lon)] if selected is not None else [-29.96,-71.30]
    m=folium.Map(location=center,zoom_start=11,tiles=None,control_scale=True)
    folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',name='Satélite Esri',attr='Esri').add_to(m)
    folium.TileLayer('OpenStreetMap',name='Calles').add_to(m)
    if not projects.empty:
        group=folium.FeatureGroup(name='Proyectos de inversión')
        for _,r in projects.head(1600).iterrows():
            folium.CircleMarker([r.lat,r.lon],radius=3,tooltip=str(r.get('NOMBRE INICIATIVA','Proyecto'))[:80],color='#f5b642',fill=True).add_to(group)
        group.add_to(m)
    if selected is not None:folium.Marker(center,tooltip='Proyecto seleccionado').add_to(m)
    Draw(export=False,draw_options={'polygon':True,'rectangle':True,'marker':False,'circle':False,'circlemarker':False,'polyline':False}).add_to(m)
    folium.LayerControl().add_to(m)
    map_result=st_folium(m,height=580,use_container_width=True,returned_objects=['last_active_drawing'],key='mapa_integrado')
    st.caption('Dibuja un polígono y presiona «Analizar todas las amenazas», o selecciona un proyecto del catastro.')

if go:
    if selected is not None and mode=='Proyecto de inversión':
        utm=Transformer.from_crs('EPSG:4326','EPSG:32719',always_xy=True).transform
        ll=Transformer.from_crs('EPSG:32719','EPSG:4326',always_xy=True).transform
        geom=geom_transform(ll,geom_transform(utm,Point(float(selected.lon),float(selected.lat))).buffer(250))
    elif map_result and map_result.get('last_active_drawing'):
        geom=shape(map_result['last_active_drawing']['geometry'])
    else:
        st.error('Selecciona un proyecto o dibuja un polígono.');st.stop()
    st.session_state['multi_geom']=mapping(geom)
    st.session_state['multi_params']=(resolution,buffer_km,channel_ha,temp,humidity,wind,rain,depth,known_depth,historical,years,months)

@st.cache_data(ttl=86400,max_entries=8,show_spinner=False)
def terrain_cached(geom_json,res,buffer_km,channel_ha):
    geom=shape(json.loads(geom_json))
    grid=grid_from_polygon(geom,res,buffer_km*1000)
    dem,cover,meta=load_dem_and_cover(grid)
    terr=terrain_features(dem,cover,grid,channel_hectares=channel_ha)
    return grid,terr,meta

if 'multi_geom' in st.session_state:
    (resolution,buffer_km,channel_ha,temp,humidity,wind,rain,depth,known_depth,historical,years,months)=st.session_state['multi_params']
    try:
        with st.spinner('Consultando DEM y cobertura Copernicus...'):
            grid,terr,meta=terrain_cached(json.dumps(st.session_state['multi_geom']),resolution,buffer_km,channel_ha)
        mask=grid['mask']&np.isfinite(terr['dem'])
        if not mask.any():st.error('El polígono no tiene celdas válidas.');st.stop()
        st.subheader('Resultados territoriales del área seleccionada')
        a,b,c,d=st.columns(4)
        a.metric('Elevación máxima',f"{np.nanmax(terr['dem'][mask]):.0f} m")
        b.metric('Pendiente máxima',f"{np.nanmax(terr['slope'][mask]):.1f}°")
        def minimum_distance(x):
            z=x[mask];z=z[np.isfinite(z)]
            return f'{np.min(z):.0f} m' if len(z) else 'Sin detección'
        c.metric('Distancia a cauce',minimum_distance(terr['dist_channel']))
        d.metric('Distancia a talud',minimum_distance(terr['dist_talud']))
        coverage={WORLDCOVER_NAMES.get(int(k),str(k)):round(float(np.mean(terr['cover'][mask]==k)*100),1) for k in np.unique(terr['cover'][mask])}
        st.write('**Cobertura del suelo (ESA WorldCover)**')
        st.dataframe(pd.DataFrame([{'Cobertura':k,'Porcentaje':v} for k,v in coverage.items()]).sort_values('Porcentaje',ascending=False),hide_index=True)
        st.caption('WorldCover identifica zonas construidas, pero no permite diferenciar fiablemente vivienda ligera de hormigón ni pavimento de techumbre.')
        st.write('**Evaluación por amenaza**')
        fire=wildfire_index(terr['cover'],terr['slope'],temp,humidity,wind,rain)
        tail=tailings_exposure(terr['dist_channel'],terr['dist_talud'],terr['accum_ha'],terr['cover'])
        st.markdown('**Incendios forestales** · índice exploratorio de condiciones de propagación, no probabilidad de incendio')
        st.metric('Indicador medio de incendio',f"{summarize(fire,mask)['media']:.2f} / 1")
        st.markdown('**Relaves** · proximidad territorial y escorrentía; no se calcula probabilidad de falla')
        st.metric('Indicador territorial descriptivo',f"{summarize(tail,mask)['media']:.2f} / 1")
        st.warning('Este indicador de relaves no significa que exista un depósito dentro del polígono. Para evaluar uno, hay que vincular su ubicación y datos técnicos del catastro SERNAGEOMIN.')
        st.markdown('**Tsunami** · escala de profundidad de GeoRiskAI')
        if known_depth:
            tsunami_score=float(score_depth_tsunami(np.array([depth]))[0])
            st.metric('Puntaje amenaza tsunami',f'{tsunami_score:.2f} / 1')
            st.caption(f'Profundidad suministrada por usuario: {depth:.2f} m; no inferida del DEM.')
        else:
            tsunami_score=None
            st.info('Sin profundidad validada: no se calcula altura ni puntaje de tsunami.')
        st.markdown('**Inundación fluvial y pluvial**')
        st.info('Se muestran drenajes y zonas potenciales de acumulación, pero no una extensión ni profundidad de inundación validada. Requiere caudales, precipitación y modelación hidráulica/hidrológica.')
        candidate=float(np.mean(terr['fan_candidate'][mask])*100)
        st.metric('Área con morfología candidata a abanico',f'{candidate:.1f}%')
        st.caption('Detección geomorfológica preliminar: no equivale a abanico aluvial confirmado.')
        observations=[]
        if historical and years and months:
            with st.spinner('Buscando escenas históricas (puede tardar)...'):
                freq,observations,valid=historical_sentinel(grid,years,months,max_scenes=18)
            st.metric('Máxima frecuencia observada de agua superficial',f'{100*np.nanmax(freq[mask]):.1f}%' if np.isfinite(freq[mask]).any() else 'Sin datos')
            st.dataframe(pd.DataFrame(observations),hide_index=True)
            st.caption('NDWI muestra agua superficial en fechas observadas, no el máximo flujo ni la profundidad histórica.')
        report={'titulo':'GeoRiskAI Sentinel - Evaluación multiamenaza','fuentes':meta,'indicadores':{'incendio':summarize(fire,mask),'relaves':summarize(tail,mask),'puntaje_tsunami':tsunami_score,'abanicos_candidatos_pct':round(candidate,2),'distancia_cauce':minimum_distance(terr['dist_channel']),'distancia_talud':minimum_distance(terr['dist_talud'])},'cobertura_pct':coverage,'escenas':observations,'limitaciones':['No existe modelo hidráulico de inundación en esta página','No hay cálculo de estabilidad de relaves','No hay modelo supervisado entrenado por defecto','Los índices exploratorios no son riesgos comparables']}
        st.download_button('Descargar ficha multiamenaza JSON',json.dumps(report,ensure_ascii=False,indent=2),file_name='georiskai_multiamenaza.json',mime='application/json')
        st.page_link('pages/1_Visor_de_inundaciones.py',label='Abrir módulo de aprendizaje supervisado y mapas de inundación')
        st.page_link('pages/2_Incendios_forestales.py',label='Abrir análisis específico de incendios')
        st.page_link('pages/3_Relaves.py',label='Abrir análisis específico de relaves')
    except Exception as exc:
        st.error(f'No se pudo completar el análisis: {exc}')
        st.caption('Verifica la conexión STAC, el tamaño del polígono y el registro de errores de Streamlit Cloud.')
