# Hidrología Satelital, Volúmenes (m³) y Dossier de Permiso · Laguna Objetivo (1985–2026)

Análisis hidro-estacional continuo (41 años: **1985–2026**) del cuerpo de agua ubicado en **Lat `47°37'46.09"S`, Lon `67°25'42.3"O`** (Depto. Deseado, Provincia de Santa Cruz).

## Contenido del Repositorio
- `index.html` + `dashboard_data.json` + `img/`: Tablero web interactivo (D3.js).
- `laguna_santa_cruz_standalone.html`: Versión autocontenida en un único archivo (incluye datos e imágenes embebidas) lista para abrir en cualquier navegador o enviar por correo.
- `streamlit_app.py` + `requirements.txt`: Aplicación lista para desplegar en **Streamlit Community Cloud**.
- `scripts/`: Scripts de procesamiento en memoria vía Planetary Computer STAC (`Landsat 5/7/8/9 C2 L2` + `Copernicus Sentinel-2 L2A` + `Copernicus DEM GLO-30` + serie climática `NASA POWER`).
