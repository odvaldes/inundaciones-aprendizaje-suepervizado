# GeoRiskAI Sentinel — ampliación incendios y relaves

Esta entrega contiene archivos para **añadir** al repositorio existente sin sustituir `data/`, cartas CITSU ni catastro de inversiones. Se usó como base la última versión local disponible de `app.py` y de la página de inundaciones.

## Instalación

1. Conserva la carpeta `data/` y los archivos originales de tu repositorio.
2. Copia `analisis_multiamenaza.py` a la raíz y los archivos `2_Incendios_forestales.py` y `3_Relaves.py` a `pages/`.
3. En `app.py` incorpora los dos `st.sidebar.page_link(...)` que aparecen en este paquete, o reemplázalo **solo si corresponde a la misma versión base**.
4. Agrega `requests` a `requirements.txt` solo si tu instalación lo necesita (no es obligatorio para estas dos páginas).
5. En Streamlit sigue usando `app.py`.

## Datos y limitaciones

- Copernicus DEM GLO-30 y ESA WorldCover se consultan vía STAC Planetary Computer usando las funciones de `inundaciones_geo.py` ya existentes. Requiere conectividad y puede fallar por disponibilidad o límites de servicio.
- El índice de incendio es **heurístico** y usa meteorología ingresada manualmente. No se ha entrenado un modelo supervisado ni conectado una API meteorológica en esta versión.
- El análisis de relaves admite CSV `lat,lon,nombre` de fuente oficial. No incorpora automáticamente el catastro de SERNAGEOMIN ni estima estabilidad de depósitos.
- La identificación de drenajes y taludes es preliminar (D8 aproximado, DEM ~30m); no equivale a cartografía validada de amenaza ni a simulación hidráulica.
- Los indicadores NO deben interpretarse como probabilidad de incendio, falla de relaves, daño o pérdida esperada.

## Pruebas

Validación de sintaxis y pruebas unitarias de rangos de índices; pendiente prueba de acceso real a STAC y despliegue Streamlit Cloud.
