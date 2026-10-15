# GeoRiskAI Sentinel

Aplicación Streamlit para visualizar proyectos de inversión pública, cruzarlos con la carta CITSU y calcular un índice multicriterio de riesgo por tsunami.

## Archivos de datos requeridos

Agrega dentro de `data/`:

1. `MDS_PROYECTOS 2024 2026.xlsx`
2. `CITSU_Coquimbo_La_Serena_2da_Ed_2015.kmz`

## Ejecución local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Publicación en GitHub

1. Crea un repositorio.
2. Sube todo el contenido de esta carpeta.
3. Confirma que `app.py`, `requirements.txt`, `.streamlit/config.toml` y `data/` estén en la rama `main`.

## Publicación en Streamlit Community Cloud

1. Conecta Streamlit Community Cloud con GitHub.
2. Selecciona el repositorio y la rama `main`.
3. Usa `app.py` como archivo principal.
4. Presiona **Deploy**.

## Nota de seguridad

Si los datos no pueden ser públicos, utiliza un repositorio privado y verifica las condiciones de acceso antes de desplegar.

## Upgrade: Visor de inundaciones por tsunami, pluviales y fluviales (Coquimbo)

Se **conservan** `app.py`, los proyectos de inversión, los KMZ/CITSU y el cálculo del índice tsunami original. Se agrega la página `pages/1_Visor_de_inundaciones.py` y el motor `inundaciones_geo.py`. La página principal ahora ofrece también el mapa satelital Esri.

### Funciones

- Seleccionar un proyecto georreferenciado del catastro o dibujar un polígono sobre mapa satelital.
- Consultar automáticamente **Copernicus DEM GLO-30**, **ESA WorldCover** y **Sentinel-2 L2A** desde Microsoft Planetary Computer STAC, sujeto a disponibilidad/conectividad.
- Seleccionar varios años y meses; examinar agua superficial detectada mediante NDWI y máscara SCL de nubes.
- Derivar pendientes, taludes, acumulación de flujo D8 y cauces **potenciales** desde el DEM, considerando una zona ampliada aguas arriba. Los abanicos son **candidatos**, no polígonos geomorfológicos verificados.
- Clasificar cobertura de suelo (árboles, construido, pastizales, etc.). **No se infiere** materialidad de viviendas ni impermeabilidad precisa a partir de WorldCover.
- Entrenar **Random Forest** por tipo de amenaza solo cuando se suministra un CSV con puntos históricos etiquetados. Columnas obligatorias `lon,lat,inundado,tipo`; `tipo` = `tsunami`, `fluvial` o `pluvial`, `inundado` = 0/1. Columna opcional `profundidad_m` para regresión de profundidad con al menos 30 datos válidos.
- Cargar GeoTIFF georreferenciado de **profundidad de inundación** de un escenario hidráulico validado; calcular la profundidad máxima del polígono. En tsunami se aplica la escala 0, 0.10, 0.56, 0.84, 1.00 para 0, (0,1], (1,2], (2,4], >4 m. Con materialidad y año se aplica el IRD definido por el usuario (0.667 A + 0.333 (0.75 M + 0.25 N)).

### Advertencias científicas

1. **La detección de agua por Sentinel-2 no equivale a un evento de inundación**. El máximo observado depende de las fechas y nubes; la imagen satelital no entrega caudal máximo ni altura de agua.
2. El DEM no es un modelo hidrodinámico. No se puede estimar profundidad real solo con pendientes y elevación. La regresión de profundidades exige ejemplos de profundidades medidos y validación independiente.
3. La validación aleatoria interna del modelo ML es exploratoria; para publicación se requieren particiones espaciales y temporales y conjuntos externos.
4. D8 es una aproximación de drenaje sin corrección de depresiones, por lo que **no debe usarse** como delimitación definitiva de cauces, abanicos o peligros.
5. La cobertura `urbanizado` de WorldCover no identifica pavimento ni resistencia estructural. La clasificación de materiales ligeros/robustos necesita catastros o datos de entrenamiento de mayor resolución.
6. El análisis se limita inicialmente a polígonos acotados y al entorno de Coquimbo–La Serena. Las fuentes pueden exigir conexión a Internet y pueden fallar o limitar solicitudes. Los años previos a la disponibilidad de Sentinel-2 L2A no tienen escenas en esta colección.
7. La escala tsunami no se traslada automáticamente a inundaciones pluviales o fluviales; deben validarse sus umbrales.

### Instalación

Sube **todos los archivos** del ZIP manteniendo `pages/`, `data/`, `.streamlit/`, `app.py`, `inundaciones_geo.py` y `requirements.txt`. En Streamlit Cloud el archivo principal sigue siendo **`app.py`**; la página nueva aparecerá en la navegación.
