"""Indicadores exploratorios de exposición; no equivalen a probabilidad de siniestro."""
import numpy as np

VEG_CODES = (10, 20, 30, 40)

def wildfire_index(cover, slope, temperature_c, humidity_pct, wind_kmh, precipitation_mm=0.0):
    """Índice heurístico 0–1 de condiciones favorables a propagación; NO probabilidad.
    Pesos explícitos exploratorios, no oficiales CONAF/SENAPRED.
    """
    c=np.asarray(cover); s=np.asarray(slope,dtype=float)
    fuel=np.select([c==10,c==20,c==30,c==40,c==50,c==60],[.85,.95,.95,.70,.15,.20],default=.05)
    slope_factor=np.clip(s/40,0,1)
    heat=np.clip((float(temperature_c)-20)/20,0,1)
    dry=np.clip((75-float(humidity_pct))/65,0,1)
    wind=np.clip(float(wind_kmh)/60,0,1)
    rain=np.clip(float(precipitation_mm)/20,0,1)
    score=.38*fuel+.15*slope_factor+.16*heat+.15*dry+.16*wind
    return np.clip(score*(1-.4*rain),0,1)

def tailings_exposure(dist_channel_m, dist_talud_m, accum_ha, cover):
    """Índice descriptivo de exposición territorial, NO estabilidad de relaves.
    No representa ruta de rotura, onda ni probabilidad de colapso.
    """
    d=np.asarray(dist_channel_m,dtype=float); t=np.asarray(dist_talud_m,dtype=float)
    a=np.asarray(accum_ha,dtype=float); c=np.asarray(cover)
    d=np.where(np.isfinite(d),d,1e6);t=np.where(np.isfinite(t),t,1e6)
    return np.clip(.4*np.exp(-d/250)+.2*np.exp(-t/150)+.2*np.clip(a/100,0,1)+.2*(c==50),0,1)

def summarize(values,mask):
    v=np.asarray(values)[mask];v=v[np.isfinite(v)]
    return {'media':round(float(np.mean(v)),3),'maximo':round(float(np.max(v)),3),'pixeles':int(len(v))} if len(v) else None
