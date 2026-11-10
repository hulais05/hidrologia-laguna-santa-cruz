"""
Genera los mapas de hidroperíodo, tira visual histórica (Filmstrip 1986-2026 Invierno vs Verano)
y el paquete JSON consolidado para el tablero web interactivo local.
"""
import os
os.environ["GDAL_HTTP_TIMEOUT"] = "10"
os.environ["GDAL_HTTP_CONNECTTIMEOUT"] = "6"
os.environ["GDAL_HTTP_MAX_RETRY"] = "2"
os.environ["GDAL_DISABLE_READDIR_ON_OPEN"] = "EMPTY_DIR"
os.environ["CPL_VSIL_CURL_ALLOWED_EXTENSIONS"] = ".TIF,.tif,.jp2"

import json
import pathlib
import warnings
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import pystac_client
import planetary_computer as pc
import rasterio
from rasterio.warp import reproject, Resampling, transform_bounds
from rasterio.windows import from_bounds as window_from_bounds
from rasterio.transform import from_bounds
from shapely.ops import transform as shp_transform
from pyproj import Transformer

warnings.filterwarnings("ignore")

OUT_DIR = pathlib.Path("/Users/martinhulais/.gemini/antigravity-cli/brain/20acfb64-c559-4c8b-acee-2d30343f803a/scratch/laguna_web")
IMG_DIR = OUT_DIR / "img"
IMG_DIR.mkdir(parents=True, exist_ok=True)

LAT_PT = -(47 + 37/60.0 + 46.09/3600.0)
LON_PT = -(67 + 25/60.0 + 42.3/3600.0)
tr_to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32719", always_xy=True)
PT_X, PT_Y = tr_to_utm.transform(LON_PT, LAT_PT)

grids = np.load(OUT_DIR / "hydroperiod_grids.npz")
freq_winter = grids["freq_winter"]
freq_summer = grids["freq_summer"]
freq_total = grids["freq_total"]
freq_early = grids["freq_early"]
freq_late = grids["freq_late"]
MASK_CORE = grids["mask_core"].astype(bool)
MASK_BASIN = grids["mask_basin"].astype(bool)
XMIN, XMAX = float(grids["xmin"]), float(grids["xmax"])
YMIN, YMAX = float(grids["ymin"]), float(grids["ymax"])
H, W = MASK_CORE.shape
DST_CRS = "EPSG:32719"
DST_TRANSFORM = from_bounds(XMIN, YMIN, XMAX, YMAX, W, H)

with open(OUT_DIR / "scenes_1985_2026.json") as f:
    scenes = json.load(f)

clim_path = OUT_DIR / "climate_1985_2026.json"
climate = json.load(open(clim_path)) if clim_path.exists() else []

# Load polygons in UTM for plotting contours
import rasterio.features
from shapely.geometry import shape
polys_core = [shape(g) for g, v in rasterio.features.shapes(MASK_CORE.astype(np.uint8), mask=MASK_CORE, transform=DST_TRANSFORM) if v == 1]
polys_basin = [shape(g) for g, v in rasterio.features.shapes(MASK_BASIN.astype(np.uint8), mask=MASK_BASIN, transform=DST_TRANSFORM) if v == 1]

def plot_contours(ax):
    for p in polys_basin:
        xs, ys = p.exterior.xy
        ax.plot(xs, ys, color="#f59e0b", lw=1.1, ls="--", alpha=0.85)
    for p in polys_core:
        xs, ys = p.exterior.xy
        ax.plot(xs, ys, color="#38bdf8", lw=1.4, alpha=0.95)
    ax.scatter([PT_X], [PT_Y], c="#00f0ff", edgecolors="white", s=45, zorder=10, lw=1.2)

# 1. Generate Hydroperiod Comparison Map (Invierno vs Verano vs Cambio Decadal)
print("Generando mapas de hidroperíodo...", flush=True)
fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), dpi=160)
fig.patch.set_facecolor("#0f172a")

cmap_water = LinearSegmentedColormap.from_list(
    "water_freq",
    ["#1e293b", "#334155", "#0369a1", "#0284c7", "#38bdf8", "#7dd3fc", "#e0f2fe"]
)
cmap_diff = LinearSegmentedColormap.from_list(
    "water_diff",
    ["#dc2626", "#f87171", "#1e293b", "#38bdf8", "#0284c7"]
)

# Zoom window tightly around the basin for maps
pad_x0, pad_x1 = PT_X - 1150, PT_X + 1350
pad_y0, pad_y1 = PT_Y - 850, PT_Y + 850
extent = [XMIN, XMAX, YMIN, YMAX]

titles = [
    "Hidroperíodo Invierno / Recarga (May–Oct)\nFrecuencia de agua libre (%)",
    "Hidroperíodo Verano / Estiaje (Nov–Abr)\nFrecuencia de agua libre (%)",
    "Cambio Decadal (2006–2026 vs 1985–2005)\nDiferencia en permanencia (puntos %)"
]
arrays = [
    np.where(MASK_BASIN, freq_winter, freq_winter * 0.25),
    np.where(MASK_BASIN, freq_summer, freq_summer * 0.25),
    np.where(MASK_BASIN, freq_late - freq_early, 0.0)
]

for idx, (ax, arr, title) in enumerate(zip(axes, arrays, titles)):
    ax.set_facecolor("#0f172a")
    if idx < 2:
        im = ax.imshow(arr, extent=extent, origin="upper", cmap=cmap_water, vmin=0, vmax=80)
        cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, orientation="horizontal")
        cb.set_label("% de escenas con agua libre", color="#94a3b8", fontsize=8.5)
        cb.ax.xaxis.set_tick_params(color="#94a3b8", labelcolor="#cbd5e1", labelsize=8)
    else:
        im = ax.imshow(arr, extent=extent, origin="upper", cmap=cmap_diff, vmin=-25, vmax=25)
        cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, orientation="horizontal")
        cb.set_label("Δ Permanencia (% 2006-26 menos 1985-05)", color="#94a3b8", fontsize=8.5)
        cb.ax.xaxis.set_tick_params(color="#94a3b8", labelcolor="#cbd5e1", labelsize=8)
    plot_contours(ax)
    ax.set_xlim(pad_x0, pad_x1)
    ax.set_ylim(pad_y0, pad_y1)
    ax.set_title(title, color="#f8fafc", fontsize=10, fontweight="bold", pad=8)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_edgecolor("#334155")

plt.tight_layout()
fig.savefig(IMG_DIR / "hydroperiod_maps.png", dpi=160, bbox_inches="tight", facecolor="#0f172a")
plt.close(fig)

# 2. Generate Historical Filmstrip (RGB + MNDWI) across decades & seasons
print("Generando tira histórica de imágenes satelitales (1986-2026)...", flush=True)
cat = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=pc.sign_inplace
)

def read_band_utm(href):
    with rasterio.open(href) as src:
        b = transform_bounds(DST_CRS, src.crs, XMIN - 60, YMIN - 60, XMAX + 60, YMAX + 60)
        w = window_from_bounds(*b, transform=src.transform).round_offsets().round_lengths()
        data = src.read(1, window=w, boundless=True, fill_value=0)
        win_tr = src.window_transform(w)
        dst = np.zeros((H, W), dtype=np.float32)
        reproject(
            source=data,
            destination=dst,
            src_transform=win_tr,
            src_crs=src.crs,
            dst_transform=DST_TRANSFORM,
            dst_crs=DST_CRS,
            resampling=Resampling.bilinear,
            dst_nodata=0
        )
        return dst

# Pick representative high-visibility scenes across history:
# Target years: ~1986/87, ~1994/96, ~2001/02, ~2007/08, ~2013/14, ~2018/19, ~2022/23, ~2025/26
target_spans = [
    (1985, 1989),
    (1992, 1996),
    (1999, 2002),
    (2005, 2008),
    (2011, 2014),
    (2016, 2019),
    (2021, 2023),
    (2025, 2026),
]

selected_film = []
for y0, y1 in target_spans:
    cands = [s for s in scenes if y0 <= s["year"] <= y1 and s["valid_pct"] >= 95 and s["sensor"] != "LANDSAT 7"]
    if not cands:
        cands = [s for s in scenes if y0 <= s["year"] <= y1 and s["valid_pct"] >= 85]
    if cands:
        # Pick scene with good water expression (near p75 of that period) to show the lagoon clearly
        cands.sort(key=lambda x: x["area_open_ha"], reverse=True)
        pick = cands[min(len(cands)-1, max(0, len(cands)//4))]
        selected_film.append(pick)

fig, axes = plt.subplots(2, len(selected_film), figsize=(2.3 * len(selected_film), 4.8), dpi=150)
fig.patch.set_facecolor("#0f172a")

cmap_mndwi = LinearSegmentedColormap.from_list(
    "mndwi_map",
    ["#451a03", "#78350f", "#a16207", "#cbd5e1", "#38bdf8", "#0284c7", "#1d4ed8"]
)

l_ids = [s["id"] for s in selected_film if s["family"] == "Landsat"]
s2_ids = [s["id"] for s in selected_film if s["family"] == "Sentinel-2"]
item_map = {}
if l_ids:
    for it in cat.search(collections=["landsat-c2-l2"], ids=l_ids).items():
        item_map[it.id] = it
if s2_ids:
    for it in cat.search(collections=["sentinel-2-l2a"], ids=s2_ids).items():
        item_map[it.id] = it

for col_idx, sc in enumerate(selected_film):
    try:
        it = item_map[sc["id"]]
        if sc["family"] == "Landsat":
            r = np.clip(read_band_utm(it.assets["red"].href) * 0.0000275 - 0.2, 0.001, 1.0)
            g = np.clip(read_band_utm(it.assets["green"].href) * 0.0000275 - 0.2, 0.001, 1.0)
            b = np.clip(read_band_utm(it.assets["blue"].href) * 0.0000275 - 0.2, 0.001, 1.0)
            s = np.clip(read_band_utm(it.assets["swir16"].href) * 0.0000275 - 0.2, 0.001, 1.0)
        else:
            pb = float(it.properties.get("s2:processing_baseline", "02.00"))
            off = -1000.0 if pb >= 4.0 else 0.0
            r = np.clip((read_band_utm(it.assets["B04"].href) + off) / 10000.0, 0.001, 1.0)
            g = np.clip((read_band_utm(it.assets["B03"].href) + off) / 10000.0, 0.001, 1.0)
            b = np.clip((read_band_utm(it.assets["B02"].href) + off) / 10000.0, 0.001, 1.0)
            s = np.clip((read_band_utm(it.assets["B11"].href) + off) / 10000.0, 0.001, 1.0)
        rgb = np.clip(np.dstack([r, g, b]) / 0.28, 0, 1) ** 0.8
        mndwi = (g - s) / (g + s + 1e-6)
    except Exception:
        rgb = np.zeros((H, W, 3))
        mndwi = np.zeros((H, W))

    ax_top = axes[0, col_idx]
    ax_bot = axes[1, col_idx]
    ax_top.imshow(rgb, extent=extent, origin="upper")
    plot_contours(ax_top)
    ax_top.set_xlim(pad_x0, pad_x1)
    ax_top.set_ylim(pad_y0, pad_y1)
    ax_top.set_xticks([]); ax_top.set_yticks([])
    est_short = "Invierno" if "Invierno" in sc["season"] else "Verano"
    ax_top.set_title(f"{sc['fecha']} ({est_short})\n{sc['sensor']} · {sc['area_open_ha']:.1f} ha", color="#f8fafc", fontsize=8.5, fontweight="bold")

    ax_bot.imshow(mndwi, extent=extent, origin="upper", cmap=cmap_mndwi, vmin=-0.35, vmax=0.35)
    plot_contours(ax_bot)
    ax_bot.set_xlim(pad_x0, pad_x1)
    ax_bot.set_ylim(pad_y0, pad_y1)
    ax_bot.set_xticks([]); ax_bot.set_yticks([])
    ax_bot.set_xlabel(f"MNDWI medio: {sc['mndwi_mean']:+.2f}", color="#94a3b8", fontsize=8)

axes[0, 0].set_ylabel("Color Real (RGB)", color="#cbd5e1", fontsize=9, fontweight="bold")
axes[1, 0].set_ylabel("Índice de Agua (MNDWI)", color="#38bdf8", fontsize=9, fontweight="bold")
plt.tight_layout()
fig.savefig(IMG_DIR / "filmstrip_1985_2026.png", dpi=150, bbox_inches="tight", facecolor="#0f172a")
plt.close(fig)

# 3. Build consolidated JSON for the web dashboard
print("Construyendo estadísticas consolidadas para el tablero web...", flush=True)

# Group by Year and Season (Invierno May-Oct vs Verano Nov-Abr)
by_year = {}
for s in scenes:
    y = s["year"]
    entry = by_year.setdefault(y, {"win": [], "sum": [], "all": []})
    entry["all"].append(s)
    if "Invierno" in s["season"]:
        entry["win"].append(s)
    else:
        entry["sum"].append(s)

# Annual climate aggregation
clim_by_year = {}
for c in climate:
    y = c["year"]
    ce = clim_by_year.setdefault(y, {"precip_mm": 0.0, "et0_mm": 0.0, "win_precip_mm": 0.0, "sum_precip_mm": 0.0, "temps": []})
    ce["precip_mm"] += c["precip_mm"]
    ce["et0_mm"] += c["et0_mm"]
    if 5 <= c["month"] <= 10:
        ce["win_precip_mm"] += c["precip_mm"]
    else:
        ce["sum_precip_mm"] += c["precip_mm"]
    ce["temps"].append(c["temp_c"])

annual_series = []
for y in range(1985, 2027):
    e = by_year.get(y, {"win": [], "sum": [], "all": []})
    ce = clim_by_year.get(y, {"precip_mm": 0.0, "et0_mm": 0.0, "win_precip_mm": 0.0, "sum_precip_mm": 0.0, "temps": [0.0]})
    win_areas = [x["area_open_ha"] for x in e["win"]]
    sum_areas = [x["area_open_ha"] for x in e["sum"]]
    all_areas = [x["area_open_ha"] for x in e["all"]]
    all_wet = [x["area_open_ha"] + x["area_wet_ha"] for x in e["all"]]
    all_mndwi = [x["mndwi_mean"] for x in e["all"]]

    annual_series.append({
        "year": y,
        "n_scenes": len(e["all"]),
        "n_win": len(win_areas),
        "n_sum": len(sum_areas),
        "win_mean_ha": round(float(np.mean(win_areas)), 2) if win_areas else None,
        "win_max_ha": round(float(np.max(win_areas)), 2) if win_areas else None,
        "sum_mean_ha": round(float(np.mean(sum_areas)), 2) if sum_areas else None,
        "sum_max_ha": round(float(np.max(sum_areas)), 2) if sum_areas else None,
        "sum_min_ha": round(float(np.min(sum_areas)), 2) if sum_areas else None,
        "annual_mean_ha": round(float(np.mean(all_areas)), 2) if all_areas else None,
        "annual_max_ha": round(float(np.max(all_areas)), 2) if all_areas else None,
        "annual_wet_total_ha": round(float(np.mean(all_wet)), 2) if all_wet else None,
        "mndwi_mean": round(float(np.mean(all_mndwi)), 3) if all_mndwi else None,
        "precip_mm": round(ce["precip_mm"], 1),
        "win_precip_mm": round(ce["win_precip_mm"], 1),
        "sum_precip_mm": round(ce["sum_precip_mm"], 1),
        "et0_mm": round(ce["et0_mm"], 1),
        "temp_c": round(float(np.mean(ce["temps"])), 1) if ce["temps"] else None,
    })

# Monthly climatology (1..12) across 1985-2026
month_names = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
monthly_cycle = []
for m in range(1, 13):
    m_sc = [s for s in scenes if s["month"] == m]
    m_cl = [c for c in climate if c["month"] == m]
    areas = [s["area_open_ha"] for s in m_sc]
    wets = [s["area_open_ha"] + s["area_wet_ha"] for s in m_sc]
    mndwis = [s["mndwi_mean"] for s in m_sc]
    monthly_cycle.append({
        "month": m,
        "name": month_names[m - 1],
        "n_scenes": len(m_sc),
        "area_mean_ha": round(float(np.mean(areas)), 2) if areas else 0.0,
        "area_median_ha": round(float(np.median(areas)), 2) if areas else 0.0,
        "area_p25_ha": round(float(np.percentile(areas, 25)), 2) if areas else 0.0,
        "area_p75_ha": round(float(np.percentile(areas, 75)), 2) if areas else 0.0,
        "wet_total_mean_ha": round(float(np.mean(wets)), 2) if wets else 0.0,
        "mndwi_mean": round(float(np.mean(mndwis)), 3) if mndwis else 0.0,
        "precip_mean_mm": round(float(np.mean([c["precip_mm"] for c in m_cl])), 1) if m_cl else 0.0,
        "et0_mean_mm": round(float(np.mean([c["et0_mm"] for c in m_cl])), 1) if m_cl else 0.0,
    })

# Decadal summary
decades = []
for label, y0, y1 in [("1985–1994", 1985, 1994), ("1995–2004", 1995, 2004), ("2005–2014", 2005, 2014), ("2015–2026", 2015, 2026)]:
    d_sc = [s for s in scenes if y0 <= s["year"] <= y1]
    d_win = [s["area_open_ha"] for s in d_sc if "Invierno" in s["season"]]
    d_sum = [s["area_open_ha"] for s in d_sc if "Verano" in s["season"]]
    d_all = [s["area_open_ha"] for s in d_sc]
    d_yr_cl = [a["precip_mm"] for a in annual_series if y0 <= a["year"] <= y1 and a["precip_mm"] > 0]
    decades.append({
        "periodo": label,
        "n_escenas": len(d_sc),
        "invierno_ha": round(float(np.mean(d_win)), 2) if d_win else 0.0,
        "verano_ha": round(float(np.mean(d_sum)), 2) if d_sum else 0.0,
        "promedio_ha": round(float(np.mean(d_all)), 2) if d_all else 0.0,
        "maximo_ha": round(float(np.max(d_all)), 2) if d_all else 0.0,
        "retencion_estival_pct": round((float(np.mean(d_sum)) / max(0.1, float(np.mean(d_win)))) * 100.0, 1) if (d_win and d_sum) else 0.0,
        "precip_anual_mm": round(float(np.mean(d_yr_cl)), 1) if d_yr_cl else 0.0
    })

all_win_ha = [s["area_open_ha"] for s in scenes if "Invierno" in s["season"]]
all_sum_ha = [s["area_open_ha"] for s in scenes if "Verano" in s["season"]]
all_ha = [s["area_open_ha"] for s in scenes]

summary = {
    "coordenadas": {
        "lat_dms": "47°37'46.09\"S",
        "lon_dms": "67°25'42.3\"O",
        "lat_dd": round(LAT_PT, 6),
        "lon_dd": round(LON_PT, 6),
        "utm_19s_e": round(PT_X, 1),
        "utm_19s_n": round(PT_Y, 1),
        "provincia": "Santa Cruz (Depto. Deseado)"
    },
    "geometria": {
        "cubeta_principal_ha": round(float(MASK_CORE.sum() * 0.09), 2),
        "cubeta_expansion_ha": round(float(MASK_BASIN.sum() * 0.09), 2),
        "espejo_permanente_gt50pct_ha": round(float((freq_total >= 50.0).sum() * 0.09), 2),
        "espejo_frecuente_gt25pct_ha": round(float((freq_total >= 25.0).sum() * 0.09), 2),
    },
    "kpis": {
        "total_escenas": len(scenes),
        "landsat_escenas": sum(1 for s in scenes if s["family"] == "Landsat"),
        "sentinel2_escenas": sum(1 for s in scenes if s["family"] == "Sentinel-2"),
        "invierno_media_ha": round(float(np.mean(all_win_ha)), 2),
        "invierno_p75_ha": round(float(np.percentile(all_win_ha, 75)), 2),
        "verano_media_ha": round(float(np.mean(all_sum_ha)), 2),
        "verano_p75_ha": round(float(np.percentile(all_sum_ha, 75)), 2),
        "max_historico_ha": round(float(np.max(all_ha)), 2),
        "max_historico_fecha": max(scenes, key=lambda x: x["area_open_ha"])["fecha"],
        "frecuencia_presencia_agua_pct": round((sum(1 for s in scenes if s["area_open_ha"] >= 2.0) / len(scenes)) * 100.0, 1),
        "frecuencia_invierno_agua_pct": round((sum(1 for s in scenes if "Invierno" in s["season"] and s["area_open_ha"] >= 2.0) / len(all_win_ha)) * 100.0, 1),
        "frecuencia_verano_agua_pct": round((sum(1 for s in scenes if "Verano" in s["season"] and s["area_open_ha"] >= 2.0) / len(all_sum_ha)) * 100.0, 1),
    },
    "annual_series": annual_series,
    "monthly_cycle": monthly_cycle,
    "decades": decades,
    "scenes": scenes
}

with open(OUT_DIR / "dashboard_data.json", "w") as f:
    json.dump(summary, f, indent=2)

print("RESUMEN KPIs:", json.dumps(summary["kpis"], indent=2), flush=True)
print("DECADAS:", json.dumps(summary["decades"], indent=2), flush=True)
