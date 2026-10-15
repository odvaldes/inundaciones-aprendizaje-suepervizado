"""Procesamiento exploratorio de inundaciones con colecciones Copernicus.
No sustituye simulación hidráulica, cartografía SHOA ni inspección geotécnica.
"""
from __future__ import annotations
import math
import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter, maximum_filter
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT
from rasterio.transform import from_origin
from rasterio.features import geometry_mask
from rasterio.warp import transform_bounds
from pyproj import Transformer
from shapely.geometry import mapping

STAC_URL = 'https://planetarycomputer.microsoft.com/api/stac/v1'
WORLDCOVER_NAMES = {10:'Árboles',20:'Arbustos',30:'Pastizales',40:'Cultivos',50:'Urbanizado / construido',60:'Suelo desnudo',70:'Nieve/hielo',80:'Agua',90:'Humedal herbáceo',95:'Manglares',100:'Musgos/líquenes'}


def grid_from_polygon(geom, resolution=30, buffer_m=2500, max_cells=350000):
    """La cuenca próxima se examina fuera del polígono; límite por seguridad."""
    from shapely.ops import transform as shape_transform
    to_utm = Transformer.from_crs('EPSG:4326', 'EPSG:32719', always_xy=True).transform
    g = shape_transform(to_utm, geom)
    xmin,ymin,xmax,ymax = g.buffer(buffer_m).bounds
    w = math.ceil((xmax-xmin)/resolution); h = math.ceil((ymax-ymin)/resolution)
    if w*h > max_cells:
        raise ValueError(f'Área de análisis demasiado extensa ({w*h:,} píxeles). Reduzca polígono, entorno o resolución.')
    tr = from_origin(xmin,ymax,resolution,resolution)
    mask = geometry_mask([mapping(g)],out_shape=(h,w),transform=tr,invert=True)
    to_wgs = Transformer.from_crs('EPSG:32719','EPSG:4326',always_xy=True)
    west,south=to_wgs.transform(xmin,ymin); east,north=to_wgs.transform(xmax,ymax)
    return {'transform':tr,'shape':(h,w),'crs':'EPSG:32719','mask':mask,'bbox':[west,south,east,north], 'resolution':resolution}


def _stac_items(collection,bbox,datetime=None,query=None,limit=100):
    from pystac_client import Client
    import planetary_computer as pc
    catalog=Client.open(STAC_URL)
    params={'collections':[collection],'bbox':bbox,'limit':limit}
    if datetime: params['datetime']=datetime
    if query: params['query']=query
    items=list(catalog.search(**params).items())
    return [pc.sign(item) for item in items]


def _read_asset(item,keys,grid,resampling=Resampling.bilinear):
    import rasterio
    asset=next((item.assets[k] for k in keys if k in item.assets),None)
    if asset is None: raise ValueError('No se encontró banda '+str(keys))
    with rasterio.Env(GDAL_HTTP_MAX_RETRY='2',GDAL_HTTP_RETRY_DELAY='1'):
        with rasterio.open(asset.href) as src:
            with WarpedVRT(src,crs=grid['crs'],transform=grid['transform'],width=grid['shape'][1],height=grid['shape'][0],resampling=resampling) as vrt:
                arr=vrt.read(1,masked=True).astype('float32')
                return arr.filled(np.nan)


def read_mosaic(collection,keys,grid,resampling=Resampling.bilinear):
    items=_stac_items(collection,grid['bbox'],limit=30)
    if not items: raise RuntimeError('Sin datos STAC para '+collection)
    output=np.full(grid['shape'],np.nan,dtype=np.float32)
    for item in items:
        try:
            a=_read_asset(item,keys,grid,resampling)
            good=np.isfinite(a)&~np.isfinite(output)
            output[good]=a[good]
            if np.isfinite(output).all():break
        except Exception:continue
    if not np.isfinite(output).any():raise RuntimeError('No fue posible leer '+collection)
    return output,len(items)


def load_dem_and_cover(grid):
    dem,ndem=read_mosaic('cop-dem-glo-30',['data'],grid)
    cover,ncover=read_mosaic('esa-worldcover',['map'],grid,Resampling.nearest)
    return dem,cover,{'dem_items':ndem,'cover_items':ncover}


def terrain_features(dem,cover,grid,channel_hectares=15,slope_threshold=25):
    """D8 aproximado, sin corrección hidrológica de depresiones; resultado indicativo."""
    res=grid['resolution']
    z=np.asarray(dem,dtype=float)
    valid=np.isfinite(z)
    if not valid.any():raise ValueError('DEM vacío')
    z=np.where(valid,z,np.nanmedian(z[valid]))
    smooth=gaussian_filter(z,1.0)
    dy,dx=np.gradient(smooth,res,res)
    slope=np.degrees(np.arctan(np.hypot(dx,dy)))
    h,w=z.shape
    # D8 de máxima caída, acumulación por orden descendente de cota.
    dst=np.full((h,w),-1,dtype=np.int32)
    rr,cc=np.indices((h,w))
    best=np.zeros((h,w),dtype=float)
    for dr,dc in ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)):
        shifted=np.full((h,w),np.inf)
        r0=max(0,-dr);r1=min(h,h-dr);c0=max(0,-dc);c1=min(w,w-dc)
        shifted[r0:r1,c0:c1]=smooth[r0+dr:r1+dr,c0+dc:c1+dc]
        drop=(smooth-shifted)/(res*(math.sqrt(2) if dr and dc else 1))
        choose=drop>best
        dst[choose]=(rr[choose]+dr)*w+(cc[choose]+dc)
        best[choose]=drop[choose]
    accum=np.ones(h*w,dtype=np.float32)
    for idx in np.argsort(-smooth.ravel()):
        nxt=dst.ravel()[idx]
        if nxt>=0:accum[nxt]+=accum[idx]
    area_ha=accum.reshape(h,w)*res*res/10000
    channels=(area_ha>=channel_hectares)&(slope<50)&valid
    taludes=(slope>=slope_threshold)&valid
    d_channel=distance_transform_edt(~channels)*res if channels.any() else np.full((h,w),np.nan)
    d_talud=distance_transform_edt(~taludes)*res if taludes.any() else np.full((h,w),np.nan)
    # Posibles desembocaduras en piedemonte: drenaje concentrado, caída de pendiente,
    # y pendientes suavizadas en su vecindad. NO delimita abanicos confirmados.
    local_uphill=maximum_filter(slope,size=11)
    fan_seed=channels&(slope<9)&(local_uphill>15)&(area_ha>=channel_hectares)
    fan_candidate=(distance_transform_edt(~fan_seed)*res<=180)&(slope<12)&valid if fan_seed.any() else np.zeros_like(channels)
    return {'slope':slope,'channels':channels,'taludes':taludes,'dist_channel':d_channel,'dist_talud':d_talud,'fan_candidate':fan_candidate,'accum_ha':area_ha,'cover':cover,'dem':dem}


def historical_sentinel(grid, years, months, max_scenes=24):
    """Serie histórica 2000+: Landsat C2 L2 (2000-2016) y Sentinel-2 L2A (2017+).

    NDWI detecta agua superficial observable, no extensión ni altura de inundación.
    Se consulta una escena de baja nubosidad por mes/año, limitada por max_scenes.
    """
    selected = []
    failures = []
    for year in sorted(set(int(y) for y in years)):
        if year < 2000 or year > 2026:
            continue
        collection = 'landsat-c2-l2' if year < 2017 else 'sentinel-2-l2a'
        try:
            its = _stac_items(collection, grid['bbox'],
                f'{year}-01-01/{year}-12-31',
                query={'eo:cloud_cover': {'lt': 55}}, limit=150)
        except Exception as exc:
            failures.append({'año':year,'fuente':collection,'error':str(exc)[:160]})
            continue
        its = [i for i in its if i.datetime and i.datetime.month in months]
        by_month = {}
        for item in sorted(its, key=lambda i: (i.datetime.month,
                i.properties.get('eo:cloud_cover') or 100)):
            by_month.setdefault(item.datetime.month, item)
        selected.extend((collection, item) for item in by_month.values())
    # Muestreo temporal repartido en toda la serie, no únicamente los primeros años.
    selected.sort(key=lambda pair: pair[1].datetime)
    if len(selected) > max_scenes:
        indexes = np.linspace(0, len(selected)-1, max_scenes, dtype=int)
        selected = [selected[i] for i in indexes]
    observations = list(failures)
    layers = []
    for collection, item in selected:
        try:
            if collection == 'sentinel-2-l2a':
                green = _read_asset(item, ['B03'], grid)
                nir = _read_asset(item, ['B08'], grid)
                scl = _read_asset(item, ['SCL'], grid, Resampling.nearest)
                invalid = np.isin(scl, [0, 1, 3, 8, 9, 10, 11]) | ~np.isfinite(scl)
                source = 'Sentinel-2'
            else:
                # Landsat 5/7: SR_B2 verde, SR_B4 NIR;
                # Landsat 8/9: SR_B3 verde, SR_B5 NIR.
                platform = str(item.properties.get('platform','')).lower()
                newer = any(t in platform for t in ('landsat-8','landsat-9','landsat_8','landsat_9'))
                green_key = 'SR_B3' if newer else 'SR_B2'
                nir_key = 'SR_B5' if newer else 'SR_B4'
                green = _read_asset(item, [green_key.lower(), green_key], grid)
                nir = _read_asset(item, [nir_key.lower(), nir_key], grid)
                qa = _read_asset(item, ['qa_pixel','QA_PIXEL'], grid, Resampling.nearest)
                qa_safe = np.nan_to_num(qa, nan=65535).astype(np.uint32)
                # Bits 0-5: fill, nube dilatada, cirrus, nube, sombra, nieve.
                invalid = ((qa_safe & 63) != 0) | ~np.isfinite(qa)
                # Landsat Collection 2 Level-2: reflectancia = DN*0.0000275-0.2.
                green = green * 0.0000275 - 0.2
                nir = nir * 0.0000275 - 0.2
                source = 'Landsat'
            denom = green + nir
            ndwi = np.divide(green-nir, denom,
                out=np.full_like(green,np.nan), where=np.abs(denom)>1e-6)
            valid = ~invalid & np.isfinite(ndwi)
            water = (ndwi > 0.2) & valid
            layers.append((water,valid))
            observations.append({'fecha':item.datetime.date().isoformat(),
                'fuente':source,
                'nubosidad_escena_pct':round(float(item.properties.get('eo:cloud_cover') or 0),1),
                'agua_detectada_pct':round(100*int(water.sum())/max(int(valid.sum()),1),2)})
        except Exception as exc:
            observations.append({'fecha':item.datetime.date().isoformat(),
                'fuente':collection,'error':str(exc)[:180]})
    if not layers:
        raise RuntimeError('No se procesaron escenas históricas. Revisa conectividad, fechas y cobertura STAC.')
    numerator = sum(w.astype(np.uint16) for w,v in layers)
    denominator = sum(v.astype(np.uint16) for w,v in layers)
    frequency = np.divide(numerator,denominator,
        out=np.full(grid['shape'],np.nan,dtype=np.float32),where=denominator>0)
    return frequency,observations,denominator


def score_depth_tsunami(depth):
    """Escala de altura del modelo tsunami (m), aplicada solo si profundidad validada."""
    d=np.asarray(depth,dtype=float)
    score=np.full(d.shape,np.nan,dtype=float)
    score[d==0]=0.0
    score[(d>0)&(d<=1)]=0.10
    score[(d>1)&(d<=2)]=0.56
    score[(d>2)&(d<=4)]=0.84
    score[d>4]=1.0
    return score


def train_supervised(features,grid,training_csv,event_type):
    """CSV: lon,lat,inundado,tipo; opcional profundidad_m. Etiquetas independientes."""
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier,RandomForestRegressor
    from sklearn.metrics import balanced_accuracy_score
    from sklearn.model_selection import train_test_split
    df=pd.read_csv(training_csv)
    needed={'lon','lat','inundado','tipo'}
    if not needed.issubset(df.columns):raise ValueError('CSV debe incluir: lon, lat, inundado (0/1), tipo')
    df=df[df['tipo'].astype(str).str.lower()==event_type.lower()].copy()
    to_utm=Transformer.from_crs('EPSG:4326',grid['crs'],always_xy=True)
    xx,yy=to_utm.transform(df.lon.to_numpy(),df.lat.to_numpy())
    inv=~grid['transform'];cc,rr=inv*(xx,yy)
    rr=np.floor(rr).astype(int);cc=np.floor(cc).astype(int)
    good=(rr>=0)&(rr<grid['shape'][0])&(cc>=0)&(cc<grid['shape'][1])
    df=df.iloc[np.flatnonzero(good)].copy();rr=rr[good];cc=cc[good]
    names=list(features)
    X=np.column_stack([np.asarray(features[k])[rr,cc] for k in names]);y=df.inundado.to_numpy(dtype=int)
    finite=np.isfinite(X).all(axis=1)&np.isin(y,[0,1]);X=X[finite];y=y[finite];df=df.iloc[np.flatnonzero(finite)]
    if len(y)<40 or len(np.unique(y))<2 or min(np.bincount(y))<10:
        raise ValueError('Se requieren al menos 40 muestras válidas, incluyendo 10 inundadas y 10 no inundadas del tipo seleccionado.')
    Xtrain,Xtest,ytrain,ytest=train_test_split(X,y,test_size=.25,stratify=y,random_state=42)
    model=RandomForestClassifier(n_estimators=180,min_samples_leaf=3,class_weight='balanced',random_state=42,n_jobs=-1)
    model.fit(Xtrain,ytrain)
    metric=balanced_accuracy_score(ytest,model.predict(Xtest))
    stack=np.column_stack([np.asarray(features[k]).ravel() for k in names]);ok=np.isfinite(stack).all(axis=1)
    probs=np.full(len(stack),np.nan,dtype=np.float32);probs[ok]=model.predict_proba(stack[ok])[:,1]
    result={'probabilidad':probs.reshape(grid['shape']),'precision_equilibrada_reserva':round(float(metric),3),'muestras':len(y),'variables':names}
    if 'profundidad_m' in df.columns:
        depths=pd.to_numeric(df.profundidad_m,errors='coerce').to_numpy()
        valid_depth=np.isfinite(depths)&(depths>=0)
        if valid_depth.sum()>=30:
            reg=RandomForestRegressor(n_estimators=180,min_samples_leaf=3,random_state=42,n_jobs=-1)
            reg.fit(X[valid_depth],depths[valid_depth]);pred=np.full(len(stack),np.nan,dtype=np.float32)
            pred[ok]=np.maximum(0,reg.predict(stack[ok]));result['profundidad_estimada_m']=pred.reshape(grid['shape'])
            result['advertencia_profundidad']='Estimación estadística no hidráulica; requiere validación independiente y cotas observadas.'
    return result


def features_for_ml(terrain,water_frequency):
    return {'elevacion_m':terrain['dem'],'pendiente_grados':terrain['slope'],'cobertura_worldcover':terrain['cover'], 'distancia_cauce_m':terrain['dist_channel'],'distancia_talud_m':terrain['dist_talud'],'area_aportante_ha':np.log1p(terrain['accum_ha']),'frecuencia_agua':water_frequency}
