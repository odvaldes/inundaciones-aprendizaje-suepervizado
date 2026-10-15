import json
import numpy as np
import streamlit as st
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
from shapely.geometry import shape, mapping
from inundaciones_geo import grid_from_polygon, load_dem_and_cover, terrain_features, WORLDCOVER_NAMES
from analisis_multiamenaza import wildfire_index, summarize

st.set_page_config(page_title="Incendios forestales | GeoRiskAI",page_icon="🔥",layout="wide")
st.title("Incendios forestales · cobertura y condiciones meteorológicas")
st.page_link("app.py",label="← Visor principal")
st.warning("Índice exploratorio de condiciones favorables a propagación; NO representa probabilidad de incendio, comportamiento del fuego ni un índice oficial.")
st.caption("Copernicus DEM + ESA WorldCover. WorldCover es una clasificación de cobertura, no un mapa actualizado de combustible fino ni de especies.")
left,right=st.columns([1,2])
with left:
    st.subheader("Escenario meteorológico")
    temp=st.number_input("Temperatura del aire (°C)",min_value=-10.,max_value=55.,value=33.)
    rh=st.slider("Humedad relativa (%)",0,100,25)
    wind=st.slider("Viento (km/h)",0,150,35)
    rain=st.number_input("Precipitación reciente (mm)",min_value=0.,max_value=500.,value=0.)
    st.caption("Los valores meteorológicos son ingresados por el usuario. No son observaciones descargadas automáticamente.")
    resolution=st.selectbox("Resolución del análisis (m)",[30,60,90],index=1)
    extent=st.slider("Entorno del polígono (km)",1,5,2)
    go=st.button("Analizar riesgo preliminar de incendio",type="primary",use_container_width=True)
with right:
    m=folium.Map(location=[-29.96,-71.25],zoom_start=10,tiles=None)
    folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',name='Satélite',attr='Esri').add_to(m)
    folium.TileLayer('OpenStreetMap',name='Calles').add_to(m)
    Draw(export=False,draw_options={'polygon':True,'rectangle':True,'polyline':False,'marker':False,'circle':False,'circlemarker':False}).add_to(m)
    folium.LayerControl().add_to(m)
    drawn=st_folium(m,height=510,use_container_width=True,returned_objects=['last_active_drawing'],key='mapa_incendios')
if go:
    feature=(drawn or {}).get('last_active_drawing')
    if not feature:st.error('Dibuja primero un polígono en el mapa.');st.stop()
    st.session_state['incendio_geom']=feature['geometry']
if 'incendio_geom' in st.session_state:
    try:
        geom=shape(st.session_state['incendio_geom'])
        with st.spinner('Consultando Copernicus DEM y ESA WorldCover...'):
            grid=grid_from_polygon(geom,resolution,extent*1000)
            dem,cover,metadata=load_dem_and_cover(grid)
            terrain=terrain_features(dem,cover,grid)
            index=wildfire_index(cover,terrain['slope'],temp,rh,wind,rain)
        mask=grid['mask']&np.isfinite(dem)
        if not mask.any():st.error('Sin datos válidos dentro del polígono.');st.stop()
        result=summarize(index,mask)
        st.subheader('Resultados del polígono')
        a,b,c=st.columns(3)
        a.metric('Índice exploratorio medio',f"{result['media']:.2f} / 1")
        b.metric('Índice máximo',f"{result['maximo']:.2f} / 1")
        c.metric('Pendiente máxima',f"{np.nanmax(terrain['slope'][mask]):.1f}°")
        st.write('Coberturas ESA WorldCover dentro del polígono:')
        counts={WORLDCOVER_NAMES.get(int(code),str(code)):round(float(np.mean(cover[mask]==code)*100),1) for code in np.unique(cover[mask])}
        st.dataframe([{'Cobertura':k,'Porcentaje':v} for k,v in sorted(counts.items(),key=lambda p:-p[1])],hide_index=True)
        st.download_button('Descargar resultados JSON',data=json.dumps({'amenaza':'incendio forestal','indicador':'heurístico, no oficial','indice':result,'cobertura_pct':counts,'meteorologia':{'temperatura_c':temp,'humedad_pct':rh,'viento_kmh':wind,'precipitacion_mm':rain},'fuentes':metadata},ensure_ascii=False,indent=2),file_name='georiskai_incendio.json',mime='application/json')
    except Exception as e:st.error(f'No fue posible completar la consulta: {e}')
