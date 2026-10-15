# GeoRiskAI Sentinel — Evaluación multiamenaza integrada

Se conserva `app.py` original y los módulos de inundación, incendios y relaves. Se agrega `pages/4_Analisis_multiamenaza.py` para consultar **el mismo polígono** y presentar juntos los indicadores de tsunami, inundaciones fluviales y pluviales, incendios forestales y relaves.

## Instalación
Sube `app.py`, `inundaciones_geo.py`, `analisis_multiamenaza.py`, `requirements.txt` y los cuatro archivos dentro de `pages/` a tu repositorio GitHub, respetando la estructura. Conserva tu carpeta `data/` original con proyectos y cartas CITSU. En Streamlit el archivo principal es `app.py`.

## Límites técnicos
- La consulta Copernicus DEM / ESA WorldCover requiere conectividad STAC.
- La consulta Landsat/Sentinel histórica es opcional y detecta agua superficial observable, no alturas ni caudales máximos.
- Para tsunami se requiere profundidad validada proporcionada por el usuario o un raster validado en el módulo específico.
- Para fluvial y pluvial faltan forzantes hidrológicos e hidráulicos para producir profundidades.
- Para relaves, el indicador describe el terreno, no presencia de un depósito ni probabilidad de colapso.
- Incendios utiliza meteorología ingresada manualmente, sin validación ni pronóstico.
- El modelo supervisado se encuentra en la página de inundaciones y requiere datos etiquetados para entrenarse.
- No se calcula un IRD agregado multiamenaza sin metodología validada.
