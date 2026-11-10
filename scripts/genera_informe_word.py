"""
Genera el documento Word (.docx) explicativo e integral del proyecto:
'Análisis Hidro-Volumétrico Satelital (1985–2026) y Dossier Técnico para Solicitud de Permiso de Uso de Agua — Laguna Objetivo, Santa Cruz'
Con el estilo corporativo de ESG Consulting SAS.
"""
import json
import pathlib
import shutil
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

PROJ_DIR = pathlib.Path("/Users/martinhulais/Trabajo Claude/proyectos/hidrologia-laguna-santa-cruz")
IMG_DIR = PROJ_DIR / "img"

# Copy QGIS overview image if available
if pathlib.Path("/tmp/qgis_laguna_polys.png").exists():
    shutil.copy2("/tmp/qgis_laguna_polys.png", IMG_DIR / "qgis_laguna_polys.png")

with open(PROJ_DIR / "dashboard_data.json", encoding="utf-8") as f:
    DATA = json.load(f)

# 1. Generate high-res chart figure (Annual Series + Monthly Regime + Hypsometric Curve) for Word
print("Generando figura de gráficos (serie anual, ciclo mensual e hipsometría) para el Word...", flush=True)
fig = plt.figure(figsize=(14, 8.2), dpi=160)
fig.patch.set_facecolor("white")
gs = fig.add_gridspec(2, 2, height_ratios=[1.15, 1.0], hspace=0.35, wspace=0.25)

# Panel A (Top full width): Serie Histórica Anual 1985-2026 (Invierno vs Verano en m3 y ha)
ax_ann = fig.add_subplot(gs[0, :])
rows = [r for r in DATA["annual_series"] if r["n_scenes"] > 0]
yrs_w = [r["year"] for r in rows if r["win_vol_mean_m3"] is not None]
vol_w = [r["win_vol_mean_m3"] / 1000.0 for r in rows if r["win_vol_mean_m3"] is not None]
yrs_s = [r["year"] for r in rows if r["sum_vol_mean_m3"] is not None]
vol_s = [r["sum_vol_mean_m3"] / 1000.0 for r in rows if r["sum_vol_mean_m3"] is not None]

ax_ann.axhline(237.15, color="#64748b", ls="--", lw=1.0, label="Capacidad Cubeta Principal llena (47,4 ha = 237.150 m³)")
ax_ann.plot(yrs_w, vol_w, "-o", color="#0284c7", lw=2.2, ms=4.5, label="Invierno / Recarga (May–Oct, miles de m³)")
ax_ann.plot(yrs_s, vol_s, "-s", color="#d97706", lw=2.0, ms=4.0, label="Verano / Estiaje (Nov–Abr, miles de m³)")
ax_ann.set_title("A. Serie Histórica Anual de Almacenamiento Hídrico (1985–2026) — Escenario Base (miles de m³)", fontsize=11, fontweight="bold", color="#1F3864", pad=8)
ax_ann.set_ylabel("Volumen Almacenado (miles de m³)", fontsize=9.5, color="#1F3864")
ax_ann.set_xlim(1985, 2026.5)
ax_ann.set_ylim(0, 410)
ax_ann.grid(True, ls=":", alpha=0.5, color="#cbd5e1")
ax_ann.legend(loc="upper left", fontsize=8.5, frameon=True)

# Twin axis for precipitation bars at bottom or right scale
ax_p = ax_ann.twinx()
all_yrs = [r["year"] for r in DATA["annual_series"]]
all_p = [r["precip_mm"] for r in DATA["annual_series"]]
ax_p.bar(all_yrs, all_p, width=0.55, color="#93c5fd", alpha=0.35, label="Precipitación anual (mm)")
ax_p.set_ylabel("Precipitación Anual (mm)", fontsize=9, color="#2563eb")
ax_p.set_ylim(0, 900)

# Panel B (Bottom Left): Ciclo Estacional Mensual (Ene-Dic)
ax_mon = fig.add_subplot(gs[1, 0])
m_names = [m["name"] for m in DATA["monthly_cycle"]]
m_mean = [m["vol_mean_m3"] / 1000.0 for m in DATA["monthly_cycle"]]
m_p25 = [m["vol_p25_m3"] / 1000.0 for m in DATA["monthly_cycle"]]
m_p75 = [m["vol_p75_m3"] / 1000.0 for m in DATA["monthly_cycle"]]
x_idx = np.arange(len(m_names))
ax_mon.axvspan(4, 9, color="#e0f2fe", alpha=0.6, label="Ventana Húmeda / Recarga (May–Oct)")
ax_mon.fill_between(x_idx, m_p25, m_p75, color="#38bdf8", alpha=0.25, label="Rango Intercuartil (P25–P75)")
ax_mon.plot(x_idx, m_mean, "-o", color="#0284c7", lw=2.3, label="Volumen Medio Mensual (miles m³)")
ax_mon.set_xticks(x_idx)
ax_mon.set_xticklabels(m_names, fontsize=8.5)
ax_mon.set_ylabel("Volumen (miles de m³)", fontsize=9.5, color="#1F3864")
ax_mon.set_title("B. Régimen Estacional Mensual (Enero–Diciembre, 1985–2026)", fontsize=10.5, fontweight="bold", color="#1F3864")
ax_mon.grid(True, ls=":", alpha=0.5, color="#cbd5e1")
ax_mon.legend(loc="upper left", fontsize=8)

# Panel C (Bottom Right): Curva Hipsométrica Cota-Área-Volumen (3 Escenarios)
ax_hyp = fig.add_subplot(gs[1, 1])
h_a = [h["area_ha"] for h in DATA["hypsometry"]]
h_vb = [h["vol_base_m3"] / 1000.0 for h in DATA["hypsometry"]]
h_vc = [h["vol_conservador_m3"] / 1000.0 for h in DATA["hypsometry"]]
h_vp = [h["vol_profundo_m3"] / 1000.0 for h in DATA["hypsometry"]]
ax_hyp.plot(h_a, h_vp, "--", color="#059669", lw=1.8, label="Escenario Profundo 1,40x (z̄ = 0,70 m)")
ax_hyp.plot(h_a, h_vb, "-o", color="#0284c7", lw=2.4, ms=4, label="Escenario Base DEM 1,00x (z̄ = 0,50 m)")
ax_hyp.plot(h_a, h_vc, "--", color="#d97706", lw=1.8, label="Escenario Conservador 0,65x (z̄ = 0,33 m)")
ax_hyp.axvline(34.6, color="#0284c7", ls=":", lw=1.2)
ax_hyp.text(33.5, 420, "Media Inv.\n(34,6 ha)", fontsize=8, color="#0284c7", ha="right")
ax_hyp.axvline(47.43, color="#475569", ls=":", lw=1.2)
ax_hyp.text(46.5, 470, "Cubeta Ppal\n(47,4 ha)", fontsize=8, color="#475569", ha="right")
ax_hyp.set_xlabel("Superficie de Espejo de Agua (ha)", fontsize=9.5, color="#1F3864")
ax_hyp.set_ylabel("Volumen Almacenado (miles de m³)", fontsize=9.5, color="#1F3864")
ax_hyp.set_title("C. Curva Hipsométrica Área (ha) vs. Volumen (miles de m³)", fontsize=10.5, fontweight="bold", color="#1F3864")
ax_hyp.grid(True, ls=":", alpha=0.5, color="#cbd5e1")
ax_hyp.legend(loc="upper left", fontsize=8)

fig.savefig(IMG_DIR / "serie_anual_y_mensual.png", dpi=160, bbox_inches="tight", facecolor="white")
plt.close(fig)

# 2. Build Word Document (.docx)
print("Construyendo documento Word (.docx)...", flush=True)
NAVY = RGBColor(0x1F, 0x38, 0x64)
AZUL = RGBColor(0x2F, 0x54, 0x96)
GRIS = RGBColor(0x33, 0x33, 0x33)
GRIS2 = RGBColor(0x59, 0x59, 0x59)

doc = Document()
for s in doc.sections:
    s.top_margin = s.bottom_margin = Cm(2.0)
    s.left_margin = s.right_margin = Cm(2.2)

st = doc.styles["Normal"]
st.font.name = "Calibri"
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
st.font.size = Pt(10.5)
st.font.color.rgb = GRIS

def par(texto="", bold_prefix=None, size=None, color=None, italic=False, space_after=5, align=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    if align:
        p.alignment = align
    if bold_prefix:
        r = p.add_run(bold_prefix)
        r.bold = True
        r.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)
        if size:
            r.font.size = Pt(size)
    r = p.add_run(texto)
    r.italic = italic
    if size:
        r.font.size = Pt(size)
    if color:
        r.font.color.rgb = color
    return p

def titulo(texto, nivel=1):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14 if nivel == 1 else 10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(texto)
    r.bold = True
    r.font.size = Pt(13.5 if nivel == 1 else 11.5)
    r.font.color.rgb = NAVY if nivel == 1 else AZUL
    if nivel == 1:
        pPr = p._p.get_or_add_pPr()
        bdr = OxmlElement("w:pBdr")
        b = OxmlElement("w:bottom")
        b.set(qn("w:val"), "single"); b.set(qn("w:sz"), "6"); b.set(qn("w:space"), "1"); b.set(qn("w:color"), "1F3864")
        bdr.append(b); pPr.append(bdr)
    return p

def vineta(texto, bold_prefix=None):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(3)
    if bold_prefix:
        r = p.add_run(bold_prefix)
        r.bold = True
        r.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)
    p.add_run(texto)
    return p

def sombrear(celda, hexcolor):
    tcPr = celda._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)

def tabla(encabezados, filas, anchos=None):
    t = doc.add_table(rows=1, cols=len(encabezados))
    t.style = "Table Grid"
    for i, h in enumerate(encabezados):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(h)
        r.bold = True; r.font.size = Pt(9); r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        sombrear(c, "1F3864")
    for k, fila in enumerate(filas):
        cells = t.add_row().cells
        for i, v in enumerate(fila):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(v))
            r.font.size = Pt(9)
            if i == 0:
                r.bold = True
            if k % 2 == 1:
                sombrear(cells[i], "F2F4F8")
    if anchos:
        for fila in t.rows:
            for i, w in enumerate(anchos):
                fila.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t

def figura(ruta, pie, ancho=16.5):
    if not pathlib.Path(ruta).exists():
        return
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(ruta), width=Cm(ancho))
    par(pie, size=8.5, color=GRIS2, italic=True, space_after=8, align=WD_ALIGN_PARAGRAPH.CENTER)

# Header
hdr = doc.sections[0].header.paragraphs[0]
r_hdr = hdr.add_run("ESG Consulting SAS · Informe Técnico Hidrológico Satelital (1985–2026) · Santa Cruz")
r_hdr.font.size = Pt(8); r_hdr.font.color.rgb = GRIS2

# Title block
par("ESG CONSULTING SAS · INFORME TÉCNICO Y DOSSIER REGULATORIO", size=9, color=GRIS2, space_after=2)
p_tit = doc.add_paragraph()
r_tit = p_tit.add_run("Evolución Hidro-Estacional (1985–2026), Estimación Volumétrica (m³) y Base Técnica para Permiso de Uso de Agua en Laguna Objetivo (Santa Cruz)")
r_tit.bold = True; r_tit.font.size = Pt(16.5); r_tit.font.color.rgb = NAVY
p_tit.paragraph_format.space_after = Pt(4)

par("Coordenadas: Lat 47°37'46.09\"S, Lon 67°25'42.30\"O · Departamento Deseado, Provincia de Santa Cruz", size=11, color=AZUL, space_after=2)
par("Tablero Web Interactivo en Vivo: https://hulais05.github.io/hidrologia-laguna-santa-cruz/ · Repositorio: github.com/hulais05/hidrologia-laguna-santa-cruz", size=9, color=GRIS2, space_after=10)

# Section 1: Resumen Ejecutivo
titulo("1. Resumen Ejecutivo y Objetivo del Estudio", 1)
par("El presente documento sintetiza la metodología, los resultados hidro-volumétricos y los lineamientos regulatorios del estudio satelital multi-década (1985–2026, 41 años de registro continuo) desarrollado sobre el cuerpo de agua ubicado en las coordenadas 47°37'46.09\"S y 67°25'42.30\"O (Departamento Deseado, Provincia de Santa Cruz).")
par("El objetivo central del análisis consiste en comprender de manera cuantitativa y auditable cómo funciona hidrológicamente la laguna entre los períodos húmedos de recarga (Invierno–Primavera, Mayo a Octubre) y los períodos secos de estiaje (Verano–Otoño, Noviembre a Abril), determinando su superficie de espejo de agua libre (en hectáreas) y su volumen almacenado (en metros cúbicos, m³) para sustentar técnicamente una Solicitud de Permiso de Uso de Agua Pública ante la Autoridad de Aplicación provincial (Consejo Agrario Provincial / Dirección Provincial de Recursos Hídricos — Ley Provincial N° 1451, y Secretaría de Estado de Minería / Ambiente).")

vineta("Se procesaron en memoria 199 escenas satelitales libres de nubes (154 escenas de las misiones USGS Landsat 5, 7, 8 y 9 a 30 m de resolución entre 1985 y 2026, más 45 escenas de la misión europea Copernicus Sentinel-2 L2A a 10 m de resolución entre 2016 y 2026), integradas con el Modelo Digital de Elevación Copernicus DEM GLO-30 y 492 meses de datos hidroclimáticos (precipitación y evapotranspiración potencial ET₀).", "Base de Evidencia Auditable (41 años): ")
vineta("El cuerpo de agua constituye un bajo colector endorreico cerrado cuya cota de fondo se ubica en 112,20 m s.n.m., recibiendo el drenaje radial de una cuenca de aporte topográfica de 38,4 km² (3.840 ha, con divisorias de hasta 215,9 m s.n.m.). Presenta una Cubeta Principal bien definida de 47,43 ha (cota de borde 113,05 m s.n.m.) y una Cubeta de Expansión Máxima de 67,77 ha (cota 113,80 m s.n.m.).", "Geometría Física de la Cubeta y Cuenca: ")
vineta("Durante el semestre de recarga invernal (Mayo–Octubre), la laguna presenta espejo de agua libre en el 82,8% de los años estudiados, con una superficie media de 34,60 ha y un almacenamiento medio estimado en 174.014 m³ en el Escenario Base DEM (rango de 113.109 m³ en escenario conservador a 243.619 m³ en escenario profundo). En años húmedos (percentil 75), el espejo invernal alcanza 51,84 ha (267.392 m³).", "Funcionamiento en Período Húmedo (Invierno–Primavera): ")
vineta("Durante el semestre estival de alta demanda evaporativa (Noviembre–Abril), el espejo se contrae a una media histórica de 20,76 ha (110.679 m³ en escenario base), lo que implica que la laguna pierde naturalmente a la atmósfera unos 63.335 m³/año por evaporación directa. En la última década (2015–2026), la retención estival promedio ascendió al 77,7% respecto del volumen invernal.", "Funcionamiento en Período Seco (Verano–Otoño) y Pérdida Evaporativa: ")
vineta("Un permiso de captación controlada (por ejemplo en el orden de 10.000 a 25.000 m³/año, equivalente a 50–140 m³/día durante la ventana húmeda) captura apenas entre el 15% y el 35% del volumen que de otro modo se evapora naturalmente hacia la atmósfera cada verano, sin afectar a terceros aguas abajo (por ser cuenca endorreica cerrada) y sin comprometer la recarga del invierno siguiente.", "Conclusión para la Viabilidad del Permiso: ")

if (IMG_DIR / "qgis_laguna_polys.png").exists():
    figura(IMG_DIR / "qgis_laguna_polys.png", "Figura 1. Ubicación del punto objetivo (47°37'46.09\"S, 67°25'42.30\"O, punto cian), contorno de la Cubeta Principal (47,43 ha, línea celeste continua) y Cubeta de Expansión Máxima (67,77 ha, línea naranja punteada) en QGIS. Al norte (a 540 m) se observa la traza vial existente.", ancho=15.5)

# Section 2: Ficha Geodésica y Morfométrica
titulo("2. Identificación Geodésica Oficial y Parámetros Morfométricos", 1)
par("Para la presentación formal ante las autoridades de la Provincia de Santa Cruz (tanto en expedientes hídricos ante el Consejo Agrario Provincial como en Informes de Impacto Ambiental mineros donde coexisten cartografías en POSGAR 2007 y Campo Inchauspe), la Tabla 1 consolida las coordenadas exactas del punto de estudio en los cuatro sistemas de referencia oficiales, junto con los parámetros morfométricos extraídos del Copernicus DEM GLO-30.")

tabla(
    ["Parámetro / Sistema de Referencia", "Código EPSG", "Valor / Coordenada Exacta", "Observación Técnica para el Expediente"],
    [
        ["Coordenadas Geográficas (WGS84)", "EPSG:4326", "47°37'46.09\"S · 67°25'42.30\"O\n(-47.629469, -67.428417)", "Sector central-norte profundo de la cubeta principal"],
        ["POSGAR 2007 / Argentina Faja 2", "EPSG:5344", "X (Este): 2.618.116,2 m\nY (Norte): 4.723.539,9 m", "Marco geodésico oficial vigente (IGN / Catastro Provincial)"],
        ["Campo Inchauspe / Faja 2", "EPSG:22192", "X (Este): 2.618.205,6 m\nY (Norte): 4.723.740,7 m", "Datum histórico habitual en legajos mineros/catastrales previos"],
        ["Proyección UTM Zona 19 Sur", "EPSG:32719", "Este: 618.068,7 m\nNorte: 4.723.684,9 m", "Grilla métrica nativa de las escenas Landsat y Sentinel-2"],
        ["Cota de Fondo de la Cubeta", "Copernicus DEM", "112,20 m s.n.m.", "Punto más deprimido del bajo endorreico"],
        ["Cota Borde Cubeta Principal", "Copernicus DEM", "113,05 m s.n.m. (Área: 47,43 ha)", "Desnivel de llenado principal: 0,85 m (tirante medio: 0,50 m)"],
        ["Cota Borde Expansión Máxima", "Copernicus DEM", "113,80 m s.n.m. (Área: 67,77 ha)", "Nivel alcanzado en pulsos húmedos extraordinarios"],
        ["Cuenca de Aporte Topográfica", "Copernicus DEM", "38,4 km² (3.840 ha)", "Cota media divisoria: 164,4 m s.n.m. (máx: 215,9 m s.n.m.)"],
        ["Distancia al Camino Existente", "Medición SIG", "540 m (hacia el Norte)", "Mínima traza de acceso desde la margen norte de la cubeta"],
    ],
    anchos=[4.2, 2.5, 4.8, 5.0]
)

figura(IMG_DIR / "cuenca_batimetry_map.png", "Figura 2. Izquierda: Modelo Digital de Elevación Copernicus DEM GLO-30 mostrando la convergencia de cañadones hacia el bajo endorreico (cota 112,2 m s.n.m.). Derecha: Modelo batimétrico/hipsométrico calibrado de la cubeta (Escenario Base).", ancho=16.5)

# Section 3: Metodología
titulo("3. Metodología de Procesamiento Satelital e Hipsométrico", 1)
par("El análisis se ejecutó mediante lectura directa en memoria sobre archivos Cloud-Optimized GeoTIFF (COG) del catálogo público STAC (Microsoft Planetary Computer), garantizando trazabilidad total sobre colecciones oficiales calibradas a reflectancia de superficie:")
vineta("Se utilizaron las colecciones USGS Landsat Collection 2 Level-2 Tier 1 (sensores TM de Landsat 5, ETM+ de Landsat 7 y OLI de Landsat 8/9, resolución espacial de 30 m = 0,09 ha/píxel) para el período 1985–2026, y Copernicus Sentinel-2 Level-2A (sensor MSI, resolución de 10 m y 20 m) para el período 2016–2026.", "1. Armonización Multi-Sensor (1985–2026): ")
vineta("En cada escena se aplicó enmascaramiento estricto de nubes, cirros y sombras de nube mediante las bandas de calidad QA_PIXEL (Landsat) y SCL (Sentinel-2). Adicionalmente, se implementó un anillo de control sobre la estepa seca circundante (buffer externo) para descartar escenas invernales con cobertura nívea regional (>25%), evitando falsos positivos por nieve sobre el terreno.", "2. Control de Nubes, Sombras y Nieve Esteparia: ")
vineta("Para discriminar con precisión el espejo de agua en lagunas patagónicas someras o con sedimento en suspensión, se empleó el Índice de Agua de Diferencia Normalizada Modificado de Xu (MNDWI = [Green − SWIR1] / [Green + SWIR1]) complementado con un umbral de absorción en el infrarrojo de onda corta (SWIR1 < 0,22). El uso de la banda SWIR1 en lugar de NIR (NDWI clásico) evita que la turbidez mineral o el fondo somero subestimen la lámina de agua.", "3. Detección Espectral de Agua Libre (MNDWI): ")
vineta("Cruzando la topografía del Copernicus DEM GLO-30 con los anillos de frecuencia de inundación satelital (que actúan como isobatas naturales del terreno), se calibró la curva hipsométrica potencial de la cubeta: V(A) = A · z̄(A), donde el tirante medio sigue la ley de forma de cubeta endorreica z̄(A) = z̄_ref · (A / 47,43 ha)^0,35. Para brindar máxima robustez técnica antes del aforo batimétrico de campo, todos los volúmenes se expresan en tres escenarios: Conservador (z̄_ref = 0,33 m; factor 0,65x), Base DEM (z̄_ref = 0,50 m; factor 1,00x) y Profundo (z̄_ref = 0,70 m; factor 1,40x).", "4. Modelación Volumétrica en 3 Escenarios Batimétricos: ")

# Section 4: Resultados Históricos, Estacionales y Volumétricos
titulo("4. Resultados: Dinámica Invierno vs. Verano y Volúmenes en m³", 1)
par("La Tabla 2 presenta la síntesis hidro-volumétrica comparativa entre el semestre húmedo de recarga (Invierno–Primavera, Mayo a Octubre) y el semestre seco de estiaje (Verano–Otoño, Noviembre a Abril) en los tres escenarios batimétricos.")

tabla(
    ["Indicador Hidrológico (Serie 1985–2026)", "Superficie de Espejo (ha)", "Volumen Escenario Conservador (0,65x)", "Volumen Escenario Base DEM (1,00x)", "Volumen Escenario Profundo (1,40x)"],
    [
        ["Media en Período Húmedo / Invierno (May–Oct)", "34,60 ha", "113.109 m³", "174.014 m³", "243.619 m³"],
        ["Percentil 75 en Invierno (Años Húmedos)", "51,84 ha", "173.805 m³", "267.392 m³", "374.349 m³"],
        ["Mediana en Invierno (Q50 — Garantía 50%)", "37,56 ha", "119.520 m³", "183.877 m³", "257.428 m³"],
        ["Capacidad a Cubeta Principal Llena (Cota 113,05 m)", "47,43 ha", "154.148 m³", "237.150 m³", "332.010 m³"],
        ["Media en Período Seco / Verano (Nov–Abr)", "20,76 ha", "71.941 m³", "110.679 m³", "154.951 m³"],
        ["Percentil 75 en Verano (Veranos Húmedos)", "46,59 ha", "154.972 m³", "238.419 m³", "333.787 m³"],
        ["Capacidad a Expansión Máxima (Cota 113,80 m)", "67,77 ha", "249.554 m³", "383.930 m³", "537.502 m³"],
        ["Pérdida Natural por Evaporación Estival (ΔV Inv→Ver)", "-13,84 ha", "41.168 m³/año", "63.335 m³/año", "88.669 m³/año"],
    ],
    anchos=[5.0, 2.5, 3.0, 3.0, 3.0]
)

figura(IMG_DIR / "serie_anual_y_mensual.png", "Figura 3. Arriba (A): Serie histórica interanual 1985–2026 de volumen almacenado en Invierno vs. Verano y precipitación anual. Abajo izquierda (B): Ciclo mensual promedio (Enero–Diciembre) e intervalo intercuartil P25–P75. Abajo derecha (C): Curva hipsométrica Área vs. Volumen en los 3 escenarios.", ancho=16.5)

titulo("4.1. Evolución a través de las Cuatro Décadas (1985–2026)", 2)
par("El desglose decadal (Tabla 3) demuestra un aspecto fundamental del sistema: la recarga invernal es altamente estable entre décadas (~31,5 a 35,3 ha en promedio durante Mayo–Octubre), incluso durante la década más seca registrada (2005–2014, cuando la lluvia anual promedió apenas 213,3 mm). Lo que responde sensiblemente a la precipitación anual es la persistencia del espejo hacia el final del verano (que fue del 29,0% en la década seca 2005–2014 y subió al 77,7% en la década húmeda reciente 2015–2026).")

tabla(
    ["Década / Período", "Escenas Válidas", "Invierno Media (ha / m³ Base)", "Verano Media (ha / m³ Base)", "Pico Máximo (ha / m³ Base)", "Retención Estival (%)", "Lluvia Media Anual"],
    [
        ["1985–1994 (*)", "8", "s/d invernal", "17,21 ha (93.921 m³)", "67,77 ha (383.930 m³)", "—", "247,6 mm"],
        ["1995–2004", "33", "31,48 ha (158.120 m³)", "21,29 ha (114.664 m³)", "67,77 ha (383.930 m³)", "67,6 %", "243,2 mm"],
        ["2005–2014 (Seca)", "53", "35,29 ha (178.902 m³)", "10,25 ha (54.442 m³)", "67,77 ha (383.930 m³)", "29,0 %", "213,3 mm"],
        ["2015–2026 (Actual)", "105", "35,29 ha (176.220 m³)", "27,41 ha (144.872 m³)", "67,77 ha (383.930 m³)", "77,7 %", "271,0 mm"],
    ],
    anchos=[2.8, 1.6, 3.4, 3.4, 3.3, 2.0, 2.0]
)
par("(*) Nota: En el período 1985–1994, la recepción satelital Landsat 5 en el extremo austral de Sudamérica registraba únicamente pasadas estivales (Nov–Mar).", size=8.5, color=GRIS2, italic=True, space_after=6)

figura(IMG_DIR / "hydroperiod_maps.png", "Figura 4. Mapas de hidroperíodo por píxel (1985–2026): Frecuencia de agua libre en Invierno (izquierda), Verano (centro) y diferencia decadal 2006–2026 vs. 1985–2005 (derecha).", ancho=16.5)
figura(IMG_DIR / "filmstrip_1985_2026.png", "Figura 5. Evidencia visual multi-década (1986–2025) en Color Real (fila superior) e Índice de Agua MNDWI (fila inferior).", ancho=16.5)

# Section 5: Dossier Regulatorio y Qué Falta para el Expediente
titulo("5. Guía para el Redactor del Permiso: Argumentos y Datos Faltantes", 1)
par("Con el fin de facilitar la labor del profesional que redacte la solicitud de permiso de uso de agua ante la Autoridad de Aplicación de Santa Cruz, a continuación se estructuran: (a) los argumentos hidro-ambientales ya demostrados por este estudio y la regla operativa sugerida, y (b) el listado de información complementaria de campo y administrativa que no puede obtenerse por satélite y debe integrarse al expediente.")

titulo("5.1. Argumentos Técnicos de Sustentabilidad y Regla Operativa Propuesta", 2)
vineta("Por tratarse de un bajo cerrado sin emisario superficial (cota de fondo 112,20 m s.n.m. rodeada por terrenos de 120 a 216 m s.n.m.), el almacenamiento superficial no alimenta cursos permanentes ni compromete derechos de agua de terceros aguas abajo.", "1. Cuenca Endorreica Cerrada (Nula Afectación Aguas Abajo): ")
vineta("El balance estacional 1985–2026 demuestra que cada año se pierden hacia la atmósfera ~63.335 m³ en el escenario base (41.168 m³ en el conservador) entre octubre y marzo por evaporación natural. Solicitar un cupo de extracción controlado (por ejemplo, 100 m³/día durante 180 días = 18.000 m³/año) representa apenas el 10,3% del volumen medio invernal y menos del 29% del agua que de todos modos se pierde por evaporación cada verano.", "2. Captura Parcial de Pérdidas por Evaporación Estival: ")
vineta("Se recomienda incluir en la solicitud un esquema de bombeo adaptativo con tres umbrales verificables mediante regla limnimétrica en el punto objetivo: (i) Bombeo al 100% del cupo autorizado cuando el espejo supere las 15 ha (cota ≥ 112,75 m s.n.m., volumen ≥ 54.000 m³); (ii) Reducción al 50% cuando el espejo se ubique entre 10 y 15 ha; y (iii) Suspensión temporal preventiva (reserva ecológica de humedal) si el espejo desciende por debajo de 10 ha.", "3. Cláusula de Garantía Ambiental y Umbral de Corte (Regla Operativa): ")

titulo("5.2. Checklist de Información Faltante a Relevar para Cerrar el Documento", 2)
par("La Tabla 4 detalla los seis (6) puntos específicos que el equipo técnico/legal debe levantar en terreno o definir en gabinete para completar la carpeta ante Recursos Hídricos (CAP) y la autoridad ambiental minera:")

tabla(
    ["N°", "Ítem Faltante para el Expediente", "Tipo de Dato", "Detalle de lo que debe hacer el Profesional / Equipo"],
    [
        ["1", "Calibración Batimétrica Expeditiva in-situ", "Campo (Hidrología)", "Realizar 1 medición de profundidad real (sonda o regla graduada) en el punto 47°37'46.09\"S, 67°25'42.30\"O e instalar una escala limnimétrica. Esto permite certificar ante la autoridad cuál de los 3 escenarios (Conservador 0,33 m, Base 0,50 m o Profundo 0,70 m) aplica como definitivo."],
        ["2", "Análisis Físico-Químico de Calidad de Agua", "Campo / Laboratorio", "Tomar 1 muestra de agua superficial para determinar pH, Conductividad Eléctrica, SDT, Cloruros, Sulfatos, Alcalinidad, Dureza y Sólidos Suspendidos. Demostrar su carácter salobre/mineralizado (no apto para consumo humano) refuerza la factibilidad de uso industrial, perforación o riego de caminos."],
        ["3", "Identificación Catastral y Acuerdo con Superficiario", "Legal / Catastro", "Consignar Nomenclatura Catastral, Matrícula y nombre del establecimiento/propietario superficial en el Depto. Deseado, junto con el permiso de paso para los 540 m entre la orilla norte de la laguna y el camino existente."],
        ["4", "Ingeniería Descriptiva del Sistema de Captación", "Ingeniería", "Especificar caudal instantáneo de bomba (L/s), modalidad de extracción (ej. motobomba a camión cisterna o manguera con chupador flotante y filtro de malla para no succionar lodo bentónico) e instalación de caudalímetro totalizador."],
        ["5", "Memoria de Demanda Mensual y Destino del Uso", "Operaciones", "Declarar el volumen diario/mensual requerido (m³/día y m³/mes), el destino específico (perforación exploratoria, control de polvo en caminos, obradores) y el plazo del permiso solicitado."],
        ["6", "Verificación Rápida de Avifauna Acuática", "Campo (Biótica)", "Registro fotográfico rápido de campo de la cubeta y su vega periférica (verificando presencia/ausencia de avifauna sensible) para respaldar el umbral de corte estival de 10 ha."],
    ],
    anchos=[0.8, 4.0, 2.7, 9.0]
)

out_docx = PROJ_DIR / "Informe_Hidrologia_Satelital_y_Dossier_Permiso_Laguna_Santa_Cruz_1985_2026.docx"
doc.save(out_docx)
print(f"Documento Word generado con éxito en: {out_docx}", flush=True)
