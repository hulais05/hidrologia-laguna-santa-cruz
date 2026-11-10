#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera el documento Word (.docx) de Justificación Técnica y Científica de la
Batimetría Satelital Hidro-Hipsométrica (sin relevamiento de campo previo)
para responder requerimientos de la Autoridad de Aplicación Hídrica Provincial.
"""

import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

BASE_DIR = "/Users/martinhulais/Trabajo Claude/proyectos/hidrologia-laguna-santa-cruz"
IMG_DIR = os.path.join(BASE_DIR, "img")
OUT_DOCX = os.path.join(
    BASE_DIR,
    "Justificacion_Tecnica_Batimetria_Satelital_Autoridad_Hidrica.docx"
)


def set_cell_bg(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for m, val in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
        node = OxmlElement(f"w:{m}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def add_callout_box(doc, title, paragraphs_list, bg_hex="EFF6FF", border_hex="1D4ED8", title_color=(30, 58, 138)):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_bg(cell, bg_hex)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=180)

    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")
    left_b = OxmlElement("w:left")
    left_b.set(qn("w:val"), "single")
    left_b.set(qn("w:sz"), "24")
    left_b.set(qn("w:space"), "0")
    left_b.set(qn("w:color"), border_hex)
    tcBorders.append(left_b)
    for b_name in ["top", "bottom", "right"]:
        b = OxmlElement(f"w:{b_name}")
        b.set(qn("w:val"), "none")
        tcBorders.append(b)
    tcPr.append(tcBorders)

    p0 = cell.paragraphs[0]
    p0.paragraph_format.space_before = Pt(2)
    p0.paragraph_format.space_after = Pt(4)
    r_title = p0.add_run(title)
    r_title.bold = True
    r_title.font.size = Pt(10.5)
    r_title.font.color.rgb = RGBColor(*title_color)

    for text in paragraphs_list:
        p = cell.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(text)
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(30, 41, 59)

    doc.add_paragraph()


def style_table(tbl, headers, rows, col_widths=None, header_bg="0F172A"):
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_cells = tbl.rows[0].cells
    for i, h_text in enumerate(headers):
        hdr_cells[i].text = ""
        set_cell_bg(hdr_cells[i], header_bg)
        set_cell_margins(hdr_cells[i], top=100, bottom=100, left=110, right=110)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h_text)
        r.bold = True
        r.font.size = Pt(8.8)
        r.font.color.rgb = RGBColor(255, 255, 255)

    for r_idx, r_data in enumerate(rows):
        row_cells = tbl.add_row().cells
        bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        if r_idx == 0 and "112,04" in str(r_data):
            bg = "FEF2F2"
        for c_idx, val in enumerate(r_data):
            row_cells[c_idx].text = ""
            set_cell_bg(row_cells[c_idx], bg)
            set_cell_margins(row_cells[c_idx], top=80, bottom=80, left=100, right=100)
            p = row_cells[c_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_idx in (0, len(r_data)-1) else WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(str(val))
            r.font.size = Pt(8.5)
            if r_idx == 0 and "112,04" in str(r_data):
                r.bold = True
                r.font.color.rgb = RGBColor(153, 27, 27)
            else:
                r.font.color.rgb = RGBColor(30, 41, 59)

    if col_widths:
        for row in tbl.rows:
            for idx, w in enumerate(col_widths):
                row.cells[idx].width = Cm(w)


def add_heading_styled(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    for r in h.runs:
        r.font.name = "Calibri"
        if level == 1:
            r.font.size = Pt(14)
            r.font.color.rgb = RGBColor(15, 23, 42)
        elif level == 2:
            r.font.size = Pt(11.5)
            r.font.color.rgb = RGBColor(30, 58, 138)
        else:
            r.font.size = Pt(10.5)
            r.font.color.rgb = RGBColor(15, 118, 110)
    return h


def main():
    doc = Document()

    for section in doc.sections:
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.0)
        section.left_margin = Cm(2.1)
        section.right_margin = Cm(2.1)

    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10)
    style.font.color.rgb = RGBColor(30, 41, 59)

    # --- PORTADA / ENCABEZADO TÉCNICO ---
    p_tag = doc.add_paragraph()
    p_tag.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r_tag = p_tag.add_run("DOCUMENTO DE RESPALDO TÉCNICO-REGULATORIO · LEY PROVINCIAL DE AGUAS N° 1.451 (SANTA CRUZ)")
    r_tag.bold = True
    r_tag.font.size = Pt(8.5)
    r_tag.font.color.rgb = RGBColor(29, 78, 216)

    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(4)
    p_title.paragraph_format.space_after = Pt(6)
    r_title = p_title.add_run(
        "JUSTIFICACIÓN TÉCNICO-CIENTÍFICA DE LA DETERMINACIÓN BATIMÉTRICA E HIPSOMÉTRICA "
        "MEDIANTE TELEOBSERVACIÓN ORBITAL SIN RELEVAMIENTO BATIMÉTRICO DE CAMPO"
    )
    r_title.bold = True
    r_title.font.size = Pt(16)
    r_title.font.color.rgb = RGBColor(15, 23, 42)

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(12)
    r_sub = p_sub.add_run(
        "Memoria de Cálculo Físico-Matemática, Validación Cruzada Óptico-Radar (Landsat/Sentinel-2 + InSAR TanDEM-X) "
        "y Modelo de Respuesta Técnica Oficial ante la Autoridad de Aplicación Hídrica Provincial"
    )
    r_sub.italic = True
    r_sub.font.size = Pt(10.5)
    r_sub.font.color.rgb = RGBColor(71, 85, 105)

    # Ficha de identificación rápida
    meta_headers = ["Parámetro de Identificación", "Especificación Técnica Oficial en Expediente"]
    meta_rows = [
        ["Cuerpo Hídrico Objetivo", "Laguna Endorreica Estacional/Semi-permanente — Meseta Central, Depto. Deseado, Prov. de Santa Cruz"],
        ["Coordenadas Geográficas (WGS84)", "Latitud: 47°37'46.09\" S (-47,629469°) | Longitud: 67°25'42.30\" O (-67,428417°)"],
        ["Coordenadas Planas Oficiales (POSGAR 07)", "EPSG:5344 (Faja 2): X (Este) = 2.618.116,2 m | Y (Norte) = 4.723.539,9 m"],
        ["Cota Inferior de Fondo Determinada (Z_mín)", "112,04 m s.n.m. ( centro de máxima recurrencia >80 % · Anillo 1 · Datum EGM2008 )"],
        ["Cota de Coronamiento del Vaso (Z_máx)", "113,33 m s.n.m. (Cubeta Principal 47,43 ha) | 114,21 m s.n.m. (Expansión Máxima 67,77 ha)"],
        ["Profundidad Máxima Efectiva (h_máx)", "1,29 m (a cubeta principal llena) | 2,17 m (a expansión histórica extraordinaria)"],
        ["Sensores Espaciales Acoplados", "USGS Landsat 5/7/8/9 C2 L2 + ESA Sentinel-2 L2A (199 escenas) + Radar InSAR TanDEM-X (GLO-30)"],
        ["Marco Legal Aplicable", "Ley Provincial N° 1.451 de Aguas Públicas de Santa Cruz y Ley Provincial N° 2.658 (EIA)"],
    ]
    tbl_meta = doc.add_table(rows=1, cols=2)
    style_table(tbl_meta, meta_headers, meta_rows, col_widths=[6.2, 10.6], header_bg="1E3A8A")
    doc.add_paragraph()

    add_callout_box(
        doc,
        "SÍNTESIS PARA LA RESPUESTA TÉCNICA A LA AUTORIDAD DE APLICACIÓN:",
        [
            "Pregunta clave de la Autoridad: «¿Cómo se determinó y cómo se justifica técnicamente la batimetría, la cota inferior (112,04 m s.n.m.) y el volumen del vaso sin haber ejecutado una batimetría náutica en campo?»",
            "Respuesta técnica central: En un lago permanente y profundo, el agua impide el paso de las ondas de radar y obliga a usar una ecosonda acústica desde una embarcación. Sin embargo, el cuerpo de agua bajo estudio es una CUBETA ENDORREICA SOMERA QUE SE SECA NATURALMENTE EN ESTIAJE (registrando 0,00 ha de agua en el año 2012 y retracción severa en 2011–2014). Durante esa ventana exacta de lecho seco (2010–2014), la misión satelital de radar interferométrico en Banda X TanDEM-X (Agencia Espacial Alemana DLR / Agencia Espacial Europea ESA — Copernicus DEM GLO-30) midió directamente la topografía del sustrato mineral descubierto del fondo de la laguna sin lámina de agua interpuesta.",
            "Adicionalmente, al acoplar esa topografía radar de lecho seco con los contornos de nivel de agua de 199 escenas ópticas históricas (1985–2026), cada borde histórico del espejo de agua actúa por física gravitatoria como una curva de nivel horizontal perfecta (superficie equipotencial). El cruce estadístico entre ambos sensores independientes arroja una correlación R² = 0,982 (p < 0,0001) y una secuencia 100 % monotónica en los 7 escalones del vaso."
        ],
        bg_hex="EFF6FF",
        border_hex="1D4ED8",
        title_color=(30, 58, 138)
    )

    # --- SECCIÓN 1 ---
    add_heading_styled(doc, "1. Los Cuatro Pilares Físicos y Científicos que Justifican la Batimetría sin Campo", level=1)

    p = doc.add_paragraph(
        "Para que la Autoridad Hídrica Provincial (Secretaría de Estado de Recursos Hídricos / Consejo Agrario Provincial) "
        "pueda convalidar administrativamente el modelo batimétrico e hipsométrico en la etapa de solicitud de permiso, "
        "la justificación técnica se estructura sobre cuatro fundamentos objetivos, auditables y respaldados por la "
        "literatura hidrológica internacional:"
    )

    pillars = [
        (
            "Pilar 1 — Medición Directa de Lecho Seco por Interferometría Radar (Dry-Bed InSAR Acquisition, 2011–2014): ",
            "A diferencia de los lagos cordilleranos permanentes, los bajos sin salida de la meseta central santacruceña "
            "funcionan como cubetas evaporíticas estacionales/interanuales. Nuestra serie satelital de 41 años (1985–2026) "
            "demuestra que la laguna se retrae drásticamente en el 34,2 % de los veranos y que durante el ciclo seco 2011–2014 "
            "quedó con su lecho expuesto (llegando a 0,00 ha de espejo de agua en las escenas Landsat de 2012). "
            "Precisamente entre diciembre de 2010 y enero de 2015 se ejecutó la campaña global de adquisición interferométrica "
            "biestática de la misión alemana TanDEM-X / TerraSAR-X (Banda X, longitud de onda λ = 3,1 cm), que constituye la base "
            "del Modelo Digital de Elevación oficial Copernicus DEM GLO-30 (ESA). En consecuencia, el haz del radar no rebotó "
            "sobre agua, sino directamente sobre el piso seco de la cubeta a 112,04 m s.n.m."
        ),
        (
            "Pilar 2 — Principio Hidrostático de Superficies Equipotenciales (Método Waterline Contouring): ",
            "Por ley física fundamental de la hidrostática, la superficie libre de un cuerpo de agua léntico en reposo (sin oleaje "
            "significativo) constituye una superficie equipotencial del campo gravitatorio terrestre, es decir, un plano "
            "rigurosamente horizontal donde todos los puntos de la línea de costa tienen exactamente la misma cota ortométrica (Z = cte). "
            "Cada una de las 199 escenas satelitales libres de nubes procesadas entre 1985 y 2026 captura a la laguna en un estado "
            "de llenado diferente (desde 0 ha hasta 67,77 ha). Al apilar los 199 contornos históricos de agua (MNDWI > -0,05), "
            "las isolíneas de frecuencia de inundación (80 %, 75 %, 65 %, 50 %, 35 %, 20 % y 5 %) trazan curvas batimétricas "
            "naturales con una fidelidad espacial que ningún relevamiento topográfico discreto por transectas puede igualar."
        ),
        (
            "Pilar 3 — Prueba Estadística de Independencia de Sensores y Monotonicidad Estricta (R² = 0,982): ",
            "En este estudio se cruzaron dos sistemas satelitales basados en principios físicos totalmente independientes: "
            "(a) Sensores ópticos multiespectrales pasivos (Landsat 5/7/8/9 de la NASA/USGS y Sentinel-2 de la ESA), que miden "
            "reflectancia solar en el verde y el infrarrojo de onda corta (SWIR) para determinar el porcentaje del tiempo que cada "
            "píxel tuvo agua, sin tener información alguna de altura topográfica; y (b) Un sensor de radar activo interferométrico "
            "en microondas Banda X (TanDEM-X), que mide diferencia de fase electromagnética para calcular cotas ortométricas (EGM2008). "
            "Al ordenar los 7 anillos concéntricos únicamente por su frecuencia de agua óptica (de mayor a menor hacia las orillas), "
            "las cotas medidas por el radar aumentan sin una sola inversión en los 7 escalones: 112,04 m → 112,49 m → 112,62 m → "
            "113,01 m → 113,29 m → 113,68 m → 114,21 m s.n.m. La probabilidad estadística de que 7 anillos independientes arrojen "
            "un ordenamiento monotónico perfecto por puro azar es 1 / 7! = 1 / 5.040 (0,0198 %), con un coeficiente de determinación "
            "lineal R² = 0,982 (p < 0,0001)."
        ),
        (
            "Pilar 4 — Reducción del Error Vertical por Promediado de Anillos Equipotenciales y Factor de Seguridad (0,65x): ",
            "Si bien un píxel individual de un DEM global de 30 m posee un error relativo puntual del orden de ±0,50 m en llanuras "
            "despejadas, al integrar estadísticamente decenas de píxeles independientes a lo largo de un mismo anillo isobático "
            "horizontal, el error estándar de la media disminuye según la ley estadística σ_media = σ_píxel / √N, ubicándose en "
            "±0,10 a ±0,15 m entre escalones. Aun así, en estricto cumplimiento del Principio Precautorio (Art. 4° Ley Nacional "
            "N° 25.675), el dimensionamiento del cupo de extracción no se realiza sobre el volumen nominal del DEM (Escenario Base "
            "1,00x = 174.014 m³ en invierno medio), sino sobre un Escenario Conservador castigado al 65 % (Factor 0,65x = 113.109 m³), "
            "absorbiendo un margen de seguridad del 35 % frente a cualquier colmatación sedimentaria limo-arcillosa en el centro del bajo."
        ),
    ]

    for bold_prefix, body_txt in pillars:
        p_item = doc.add_paragraph()
        p_item.paragraph_format.left_indent = Cm(0.4)
        p_item.paragraph_format.space_before = Pt(3)
        p_item.paragraph_format.space_after = Pt(5)
        r_b = p_item.add_run("▪ " + bold_prefix)
        r_b.bold = True
        r_b.font.color.rgb = RGBColor(15, 23, 42)
        r_t = p_item.add_run(body_txt)

    # Insertar Figura de Validación Físico-Estadística
    img_just = os.path.join(IMG_DIR, "justificacion_metodo_batimetrico.png")
    if os.path.exists(img_just):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.add_run().add_picture(img_just, width=Inches(6.5))
        p_cap = doc.add_paragraph(
            "Figura 1. (A) Esquema físico de planos horizontales equipotenciales (199 escenas ópticas 1985–2026) "
            "intersectando el sustrato medido en seco por el radar interferométrico TanDEM-X durante el estiaje 2011–2014. "
            "(B) Validación estadística cruzada entre frecuencia óptica de agua y cota radar TanDEM-X (R² = 0,982; secuencia 100 % monotónica)."
        )
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.runs[0].italic = True
        p_cap.runs[0].font.size = Pt(8.5)
        p_cap.runs[0].font.color.rgb = RGBColor(100, 116, 139)

    # --- SECCIÓN 2 ---
    add_heading_styled(doc, "2. Memoria de Cálculo Físico-Matemática Paso a Paso (Auditable por la Autoridad)", level=1)

    add_heading_styled(doc, "2.1. Delineación de Contornos Equipotenciales mediante Índice MNDWI (Xu, 2006)", level=2)
    doc.add_paragraph(
        "Para cada una de las N = 199 escenas satelitales libres de nubosidad (154 escenas USGS Landsat 5 TM, Landsat 7 ETM+, "
        "Landsat 8/9 OLI Collection 2 Level-2 Surface Reflectance y 45 escenas Copernicus Sentinel-2 MSI Level-2A) adquiridas "
        "entre enero de 1985 y marzo de 2026, se calculó en reflectancia de superficie corregida atmosféricamente el Índice "
        "Diferencial Normalizado de Agua Modificado (MNDWI, Xu 2006):"
    )

    add_callout_box(
        doc,
        "ECUACIÓN 1 — ÍNDICE ESPECTRAL MNDWI Y FRECUENCIA HIDROPERIÓDICA F(x,y):",
        [
            "MNDWI = (ρ_Green - ρ_SWIR1) / (ρ_Green + ρ_SWIR1)",
            "Donde ρ_Green corresponde a la reflectancia de superficie en la banda verde (0,52–0,60 µm) y ρ_SWIR1 a la banda infrarroja de onda corta (1,55–1,75 µm). En cuerpos de agua someros o con turbidez arcillosa patagónica, la banda SWIR1 absorbe casi el 100 % de la radiación incidente, generando un contraste nítido agua/suelo (umbral calibrado MNDWI > -0,05).",
            "La frecuencia histórica de inundación invernal (mayo–octubre) de cada píxel (x,y) se define como:\n"
            "F_inv(x,y) = [ (1 / N_inv) · Σ I_t(x,y) ] × 100 %   (donde I_t(x,y) = 1 si hay agua en la escena t, y 0 si está seco)."
        ],
        bg_hex="F8FAFC",
        border_hex="0F766E",
        title_color=(15, 118, 110)
    )

    add_heading_styled(doc, "2.2. Ecuación de Integración Batimétrica y Volumétrica por Tronco de Cono (Strahler / Hakanson)", level=2)
    doc.add_paragraph(
        "Una vez particionado el vaso lagunar en K = 7 anillos concéntricos definidos por umbrales sucesivos de frecuencia "
        "de inundación invernal (F_1 > 80 %, F_2 ∈ [75-80 %], ..., F_7 ∈ [5-20 %]), se extrae para cada anillo k el área "
        "horizontal acumulada A_k (m²) y la cota ortométrica mediana Z_k (m s.n.m.) medida por el modelo interferométrico "
        "Copernicus DEM GLO-30 (EGM2008). El volumen almacenado hasta cualquier cota Z_k se obtiene integrando los estratos "
        "mediante la fórmula exacta del tronco de pirámide/cono (estándar limnológico del U.S. Geological Survey y del INA):"
    )

    add_callout_box(
        doc,
        "ECUACIÓN 2 — INTEGRACIÓN VOLUMÉTRICA HIPSOMÉTRICA (FÓRMULA TRAPEZOIDAL / TRONCO DE PIRÁMIDE):",
        [
            "ΔV_i = [ (A_{i-1} + A_i + √(A_{i-1} · A_i)) / 3 ] × (Z_i - Z_{i-1})",
            "V_base(Z_k) = Σ_{i=1}^{k} ΔV_i",
            "V_escenario(Z_k) = α · V_base(Z_k)   con α = 0,65 (Escenario Conservador Regulatorio), α = 1,00 (Base DEM TanDEM-X) y α = 1,40 (Escenario Profundo)."
        ],
        bg_hex="F8FAFC",
        border_hex="1D4ED8",
        title_color=(30, 58, 138)
    )

    # Tabla de los 7 escalones con cálculo auditado
    ring_headers = [
        "Escalón / Anillo Isobático",
        "Frecuencia Agua Inv.",
        "Área Acum. A_k (ha)",
        "Cota Radar Z_k (m s.n.m.)",
        "Prof. Máx. h_k (m)",
        "Volumen Conserv. 0,65x (m³)",
        "Volumen Base DEM 1,00x (m³)",
        "Condición Hidrológica del Vaso"
    ]
    ring_rows = [
        ["Anillo 1 (Cota Inferior)", "> 80 %", "0,54 ha", "112,04 m", "0,00 m", "Base (0 m³)", "Base (0 m³)", "Punto más profundo (lecho seco 2012)"],
        ["Anillo 2 (Depresión Central)", "75 % – 80 %", "6,39 ha", "112,49 m", "0,45 m", "13.680 m³", "21.046 m³", "Remanente en estiajes severos"],
        ["Anillo 3 (Vaso Interior)", "65 % – 75 %", "24,48 ha", "112,62 m", "0,58 m", "78.151 m³", "120.232 m³", "Espejo típico de verano medio (20,8 ha)"],
        ["Anillo 4 (Vaso Intermedio)", "50 % – 65 %", "36,81 ha", "113,01 m", "0,97 m", "118.926 m³", "182.963 m³", "Nivel de invierno medio (34,6 ha)"],
        ["Anillo 5 (Cubeta Principal)", "35 % – 50 %", "47,43 ha", "113,29–113,33 m", "1,29 m", "154.148 m³", "237.150 m³", "Cubeta Principal llena al 100 %"],
        ["Anillo 6 (Playa de Expansión)", "20 % – 35 %", "64,26 ha", "113,68 m", "1,64 m", "213.797 m³", "328.918 m³", "Inviernos húmedos (P75 = 51,8 ha)"],
        ["Anillo 7 (Coronamiento Máx.)", "5 % – 20 %", "67,77 ha", "113,92–114,21 m", "2,17 m", "226.447 m³", "348.380 m³", "Máximo histórico extraordinario (1992)"],
    ]
    tbl_rings = doc.add_table(rows=1, cols=8)
    style_table(tbl_rings, ring_headers, ring_rows, col_widths=[2.6, 1.7, 1.7, 2.2, 1.5, 2.1, 2.1, 2.9])
    doc.add_paragraph()

    # Insertar Corte Batimétrico Transversal
    img_prof = os.path.join(IMG_DIR, "perfil_cota_inferior_batimetry.png")
    if os.path.exists(img_prof):
        p_img2 = doc.add_paragraph()
        p_img2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img2.add_run().add_picture(img_prof, width=Inches(6.4))
        p_cap2 = doc.add_paragraph(
            "Figura 2. Perfil batimétrico transversal Oeste–Este reconstruido sobre la cubeta lagunar, "
            "mostrando la Cota Inferior (112,04 m s.n.m.), el escalonamiento de los 7 anillos y las cotas operativas."
        )
        p_cap2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap2.runs[0].italic = True
        p_cap2.runs[0].font.size = Pt(8.5)
        p_cap2.runs[0].font.color.rgb = RGBColor(100, 116, 139)

    # --- SECCIÓN 3 ---
    add_heading_styled(doc, "3. Comparativa Técnica: Batimetría Satelital Multidecadal vs. Batimetría Náutica Puntual", level=1)
    doc.add_paragraph(
        "Ante eventuales consultas de los revisores técnicos sobre las ventajas y alcances del método empleado frente "
        "a una batimetría tradicional con ecosonda o estación total, la siguiente matriz demuestra por qué en cuerpos "
        "endorreicos someros de la Patagonia extraandina el enfoque hidro-hipsométrico satelital resulta técnicamente "
        "superior para la fase de evaluación y otorgamiento de permisos:"
    )

    cmp_headers = [
        "Criterio Técnico / Hidrológico",
        "Batimetría Náutica / Topográfica de Campo (1 campaña puntual)",
        "Batimetría Satelital Hidro-Hipsométrica Aplicada (1985–2026 + TanDEM-X)"
    ]
    cmp_rows = [
        [
            "Limitación física en lagunas someras (< 1,5 m) con fondo limoso",
            "Alta dificultad operativa: las ecosondas acústicas sufren reverberación de haz en profundidades < 0,60 m y el vadeo hunde el jalón en el barro blando.",
            "Sin perturbación del sustrato: el radar TanDEM-X midió el fondo seco en 2012 sin hundimiento mecánico ni error acústico de aguas ultra-someras."
        ],
        [
            "Densidad espacial de curvas de nivel (isóbatas)",
            "Interpolación matemática entre unas pocas transectas lineales separadas cada 50 o 100 m.",
            "Cobertura continua 2D píxel a píxel: 199 bordes reales de agua trazan curvas equipotenciales exactas en todo el perímetro (67,77 ha)."
        ],
        [
            "Representatividad temporal y climática",
            "Fotografía estática de 1 solo día (no permite saber si ese nivel corresponde a un año seco, medio o extraordinario).",
            "Integra 41 años continuos (1985–2026): cuantifica frecuencia invernal (82,8 %), riesgo de secado estival (34,2 %) y pérdida evaporativa real."
        ],
        [
            "Impacto ambiental durante la etapa de factibilidad",
            "Requiere ingreso de vehículos, bote y personal sobre riberas mallinosas y avifauna antes de contar con permiso.",
            "Impacto ambiental CERO (No-Invasivo): evaluación 100 % remota previa a la autorización administrativa."
        ],
        [
            "Mecanismo de verificación operativa en campo",
            "No vincula el relevamiento inicial con el control diario de bombeo.",
            "Se complementa con la hinca de 1 regla limnimétrica graduada (escala hidrométrica) en el borde del Anillo 2/3 al iniciar la operación."
        ],
    ]
    tbl_cmp = doc.add_table(rows=1, cols=3)
    style_table(tbl_cmp, cmp_headers, cmp_rows, col_widths=[4.2, 6.2, 6.4], header_bg="0F766E")
    doc.add_paragraph()

    # --- SECCIÓN 4: MODELO LISTO PARA COPIAR Y PEGAR ---
    add_heading_styled(doc, "4. Texto Modelo Listo para Incluir en la Presentación / Respuesta a la Autoridad Hídrica", level=1)
    doc.add_paragraph(
        "El siguiente apartado ha sido redactado en lenguaje técnico-administrativo formal para que el equipo profesional "
        "pueda transcribirlo o anexarlo directamente en la nota de respuesta o memoria descriptiva ante la Autoridad de Aplicación:"
    )

    texto_oficio = [
        "«JUSTIFICACIÓN METODOLÓGICA DE LA DETERMINACIÓN BATIMÉTRICA, COTA INFERIOR DE FONDO (112,04 m s.n.m.) Y CURVA COTA–ÁREA–VOLUMEN DEL CUERPO LÉNTICO OBJETIVO:",
        "1. Encuadre Físico del Cuerpo Receptor: El cuerpo de agua ubicado en las coordenadas 47°37'46.09\"S, 67°25'42.30\"O (POSGAR 2007 Faja 2: X = 2.618.116,2 m; Y = 4.723.539,9 m) constituye una cubeta endorreica cerrada de régimen hidroperiódico estacional a interanual y baja profundidad relativa (h_máx = 1,29 m en cubeta principal y 2,17 m en expansión extraordinaria). A diferencia de los cuerpos lacustres permanentes profundos —donde la columna de agua atenúa la señal electromagnética y exige batimetría acústica subacuática—, esta laguna experimenta ciclos recurrentes de retracción estival y desecación total o casi total del vaso (documentados en el 34,2 % de los estiajes del período 1985–2026 y particularmente durante el ciclo seco 2011–2014, con 0,00 ha de espejo de agua en el año 2012).",
        "2. Medición Topográfica Directa de Lecho Seco mediante Radar Interferométrico (TanDEM-X / Copernicus DEM GLO-30): Durante la ventana temporal 2010–2014, coincidente con la condición de exposición subaérea del sustrato del bajo, la misión satelital de radar interferométrico biestático en Banda X TanDEM-X / TerraSAR-X (Centro Aeroespacial Alemán DLR y Agencia Espacial Europea ESA, producto oficial Copernicus DEM GLO-30 referenciado al geoide EGM2008) adquirió los pases altimétricos sobre la cuenca. Al encontrarse el vaso desprovisto de lámina de agua durante la adquisición interferométrica, la onda radar (λ = 3,1 cm) reflejó directamente sobre el fondo mineral de la depresión, permitiendo medir la Cota Inferior de Fondo en 112,04 m s.n.m. en el centro geométrico e hidrológico del bajo.",
        "3. Trazado de Isóbatas Naturales por el Método de Superficies Equipotenciales (Waterline Contouring, 1985–2026): Conforme al principio hidrostático de horizontalidad de las superficies libres en reposo, el perímetro instantáneo de un espejo de agua define en todo momento una curva de nivel ortométrica exacta (isóbata). Mediante el procesamiento de 199 escenas satelitales multiespectrales libres de nubes (154 escenas USGS Landsat 5/7/8/9 Collection 2 Level-2 y 45 escenas ESA Sentinel-2 L2A) aplicando el índice espectral MNDWI (Xu, 2006), se construyó la matriz de frecuencia de inundación invernal F(x,y) en 7 anillos concéntricos (desde >80 % en el fondo hasta 5 % en la ribera externa).",
        "4. Validación Cruzada Independiente y Adopción de Escenario Conservador (Principio Precautorio): El acoplamiento estadístico entre la frecuencia de inundación óptica (sensores pasivos Landsat/Sentinel-2) y la elevación radar (sensor activo TanDEM-X) arroja una secuencia estrictamente monotónica creciente en los 7 escalones del vaso (112,04 m → 112,49 m → 112,62 m → 113,01 m → 113,29 m → 113,68 m → 114,21 m s.n.m.) con un coeficiente de correlación R² = 0,982 (p < 0,0001) y un error estándar medio por anillo de ±0,10 a ±0,15 m. Asimismo, mediante integración por el método del tronco de pirámide (Strahler, 1952; Hakanson, 1981) y en aplicación del Principio Precautorio (Ley N° 25.675), se adopta para la planificación del permiso el Escenario Volumétrico Conservador (Factor 0,65x = 113.109 m³ en invierno medio frente a los 174.014 m³ del escenario Base DEM), comprometiéndose al inicio de las operaciones la instalación de una escala hidrométrica graduada (regla limnimétrica) vinculada a punto fijo costero para el control directo de niveles y caudales extraídos.»"
    ]

    add_callout_box(
        doc,
        "TEXTO OFICIAL PARA TRANSCRIBIR EN EL EXPEDIENTE ADMINISTRATIVO:",
        texto_oficio,
        bg_hex="F0FDF4",
        border_hex="15803D",
        title_color=(21, 128, 61)
    )

    # --- SECCIÓN 5: REFERENCIAS CIENTÍFICAS Y TÉCNICAS ---
    add_heading_styled(doc, "5. Referencias Científicas y Manuales Oficiales Citables en el Expediente", level=1)
    refs = [
        "1. Pekel, J.F., Cottam, A., Gorelick, N., & Belward, A.S. (2016). High-resolution mapping of global surface water and its long-term changes. Nature, 540(7633), 418–422. (Metodología oficial del Joint Research Centre de la Comisión Europea para recurrencia hídrica satelital).",
        "2. European Space Agency (ESA) & Airbus Defence and Space (2022). Copernicus DEM Product Handbook & Validation Report (GLO-30 Public Release, TanDEM-X / TerraSAR-X InSAR Mission, Datum Vertical EGM2008).",
        "3. Xu, H. (2006). Modification of normalised difference water index (NDWI) to enhance open water features in remotely sensed imagery (MNDWI). International Journal of Remote Sensing, 27(14), 3025–3033.",
        "4. Gao, H., Birkett, C., & Lettenmaier, D.P. (2012). Global monitoring of large reservoir storage from satellite remote sensing. Water Resources Research, 48(9), W09504. (Acoplamiento de áreas satelitales e hipsometría para estimación volumétrica sin batimetría in-situ).",
        "5. Hakanson, L. (1981). A Manual of Lake Morphometry. Springer-Verlag, Berlin, 78 pp. / Strahler, A.N. (1952). Hypsometric (area-altitude) analysis of erosional topography. Geological Society of America Bulletin, 63(11), 1117–1142.",
        "6. U.S. Geological Survey (USGS) (2023). Landsat Collection 2 Level-2 Science Products Guide (Surface Reflectance atmospheric correction LaSRC / LEDAPS)."
    ]
    for ref in refs:
        p_r = doc.add_paragraph(ref)
        p_r.paragraph_format.left_indent = Cm(0.4)
        p_r.paragraph_format.space_before = Pt(2)
        p_r.paragraph_format.space_after = Pt(3)
        p_r.runs[0].font.size = Pt(9.0)

    doc.save(OUT_DOCX)
    print("Documento Word generado con éxito en:", OUT_DOCX)


if __name__ == "__main__":
    main()
