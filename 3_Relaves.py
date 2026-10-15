import io,json
import numpy as np
import pandas as pd
import streamlit as st
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
from shapely.geometry import shape, Point, mapping
from inundaciones_geo import grid_from_polygon,load_dem_and_cover,terrain_features,WORLDCOVER_NAMES
from analisis_multiamenaza import tailings_exposure,summarize

st.set_page_config(page_title='Relaves | GeoRiskAI',page_icon='⛰️',layout='wide')
st.title('Relaves · exposición territorial y drenaje')
st.page_link('app.py',label='← Visor principal')
st.warning('No estima probabilidad de falla, estabilidad geotécnica, distancia de recorrido de una rotura ni pérdidas. Requiere modelación de rotura y datos del depósito para esas conclusiones.')
st.caption('Dibuja el perímetro de un relave o carga puntos georreferenciados del catastro oficial. Se examina el entorno y la dirección de drenaje aproximada a partir del DEM.')
upload=st.file_uploader('Catastro de relaves (CSV con lat, lon y nombre; opcional)',type='csv')
records=pd.DataFrame()
if upload:
    try:
        records=pd.read_csv(upload)
        if not {'lat','lon'}.issubset(records.columns):raise ValueError('Se necesitan columnas lat y lon en grados decimales.')
        records=records.dropna(subset=['lat','lon'])
    except Exception as e:st.error(f'Catastro inválido: {e}');records=pd.DataFrame()
left,right=st.columns([1,2])
with left:
    mode=st.radio('Zona de análisis',['Dibujar polígono','Relave del catastro'] if not records.empty else ['Dibujar polígono'])
    selected=None
    if mode=='Relave del catastro':
        i=st.selectbox('Relave',range(len(records)),format_func=lambda j:str(records.iloc[j].get('nombre',f'Relave {j+1}')))
        selected=records.iloc[i]
    resolution=st.selectbox('Resolución DEM (m)',[30,60,90],index=1)
    buffer=st.slider('Entorno para evaluar drenaje (km)',1,8,4)
    min_ha=st.slider('Área aportante mínima (ha)',2,100,15)
    run=st.button('Analizar entorno del relave',type='primary',use_container_width=True)
with right:
    center=[float(selected.lat),float(selected.lon)] if selected is not None else [-29.9,-71.1]
    m=folium.Map(location=center,zoom_start=11,tiles=None)
    folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',name='Satélite',attr='Esri').add_to(m)
    if not records.empty:
        for _,r in records.head(1000).iterrows():
            folium.CircleMarker([float(r.lat),float(r.lon)],radius=4,tooltip=str(r.get('nombre','Relave')),color='#d85a28').add_to(m)
    Draw(export=False,draw_options={'polygon':True,'rectangle':True,'polyline':False,'marker':False,'circle':False,'circlemarker':False}).add_to(m)
    drawn=st_folium(m,height=510,use_container_width=True,returned_objects=['last_active_drawing'],key='mapa_relaves')
if run:
    if selected is not None:
        from shapely.ops import transform
        from pyproj import Transformer
        forward=Transformer.from_crs('EPSG:4326','EPSG:32719',always_xy=True).transform
        backward=Transformer.from_crs('EPSG:32719','EPSG:4326',always_xy=True).transform
        geom=transform(backward,transform(forward,Point(float(selected.lon),float(selected.lat))).buffer(250))
    elif (drawn or {}).get('last_active_drawing'):
        geom=shape(drawn['last_active_drawing']['geometry'])
    else:st.error('Dibuja un polígono o selecciona un relave.');st.stop()
    st.session_state['relave_geom']=mapping(geom)
if 'relave_geom' in st.session_state:
    try:
        geom=shape(st.session_state['relave_geom'])
        with st.spinner('Analizando relieve y drenajes desde Copernicus...'):
            grid=grid_from_polygon(geom,resolution,buffer*1000)
            dem,cover,meta=load_dem_and_cover(grid)
            terrain=terrain_features(dem,cover,grid,channel_hectares=min_ha)
            indicator=tailings_exposure(terrain['dist_channel'],terrain['dist_talud'],terrain['accum_ha'],cover)
        mask=grid['mask']&np.isfinite(dem)
        if not mask.any():st.error('No hay datos válidos.');st.stop()
        res=summarize(indicator,mask)
        a,b,c=st.columns(3)
        a.metric('Indicador descriptivo máximo',f"{res['maximo']:.2f} / 1")
        ch=terrain['dist_channel'][mask];ta=terrain['dist_talud'][mask]
        b.metric('Distancia a drenaje',f"{np.nanmin(ch):.0f} m" if np.isfinite(ch).any() else 'Sin detección')
        c.metric('Distancia a talud',f"{np.nanmin(ta):.0f} m" if np.isfinite(ta).any() else 'Sin detección')
        st.info('El indicador es una señal descriptiva para priorizar revisión, NO riesgo de colapso. La exposición aguas abajo requiere modelar trayectoria y volumen de liberación; no se deduce del indicador.')
        st.write('Área urbanizada ESA WorldCover en el polígono:',round(float(np.mean(cover[mask]==50)*100),1),'%')
        st.download_button('Descargar ficha JSON',json.dumps({'analisis':'relave','tipo':'exposición descriptiva no oficial','indicador':res,'fuentes':meta},ensure_ascii=False,indent=2),file_name='georiskai_relave.json',mime='application/json')
    except Exception as e:st.error(f'No fue posible completar el análisis: {e}')
