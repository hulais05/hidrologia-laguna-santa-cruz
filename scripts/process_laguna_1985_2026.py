"""
Procesamiento satelital rápido en memoria (1985–2026) de la Laguna Objetivo (47°37'46.09"S, 67°25'42.3"O).
- Combina Landsat 5/7/8/9 C2 L2 Tier 1 (1985-2026) + Copernicus Sentinel-2 L2A (2016-2026) vía Planetary Computer STAC.
- Configura GDAL_HTTP_TIMEOUT y GDAL_DISABLE_READDIR_ON_OPEN para lectura instantánea sin bloqueos de red.
- No almacena GeoTIFFs ni cachés pesados en disco: lee únicamente la ventana de 171x111 píxeles en RAM.
"""
import os
os.environ["GDAL_HTTP_TIMEOUT"] = "10"
os.environ["GDAL_HTTP_CONNECTTIMEOUT"] = "6"
os.environ["GDAL_HTTP_MAX_RETRY"] = "2"
os.environ["GDAL_DISABLE_READDIR_ON_OPEN"] = "EMPTY_DIR"
os.environ["CPL_VSIL_CURL_ALLOWED_EXTENSIONS"] = ".TIF,.tif,.jp2"

import concurrent.futures as cf
import json
import pathlib
import urllib.request
import warnings
import numpy as np
import pystac_client
import planetary_computer as pc
import rasterio
from rasterio.warp import reproject, Resampling, transform_bounds
from rasterio.windows import from_bounds as window_from_bounds
from rasterio.transform import from_bounds
from scipy.ndimage import binary_dilation

warnings.filterwarnings("ignore")

OUT_DIR = pathlib.Path("/Users/martinhulais/.gemini/antigravity-cli/brain/20acfb64-c559-4c8b-acee-2d30343f803a/scratch/laguna_web")
OUT_DIR.mkdir(parents=True, exist_ok=True)
(OUT_DIR / "img").mkdir(exist_ok=True)

LAT_PT = -(47 + 37/60.0 + 46.09/3600.0)   # -47.6294694
LON_PT = -(67 + 25/60.0 + 42.3/3600.0)    # -67.4284167

calib = np.load("/tmp/laguna_masks.npz")
MASK_CORE = calib["mask_core"].astype(bool)     # 47.43 ha
MASK_BASIN = calib["mask_basin"].astype(bool)   # 67.77 ha
XMIN, XMAX = float(calib["xmin"]), float(calib["xmax"])
YMIN, YMAX = float(calib["ymin"]), float(calib["ymax"])
H, W = MASK_CORE.shape
DST_CRS = "EPSG:32719"
DST_TRANSFORM = from_bounds(XMIN, YMIN, XMAX, YMAX, W, H)
BBOX_LL = transform_bounds(DST_CRS, "EPSG:4326", XMIN, YMIN, XMAX, YMAX)

MASK_STEPPE = binary_dilation(MASK_BASIN, iterations=12) & (~binary_dilation(MASK_BASIN, iterations=3))

CORE_TOTAL_HA = float(MASK_CORE.sum() * 0.09)
BASIN_TOTAL_HA = float(MASK_BASIN.sum() * 0.09)
print(f"Grid {W}x{H} (30m) | Core={CORE_TOTAL_HA:.2f} ha | Basin={BASIN_TOTAL_HA:.2f} ha", flush=True)

def read_band_30m(href, is_qa=False):
    with rasterio.open(href) as src:
        b = transform_bounds(DST_CRS, src.crs, XMIN - 60, YMIN - 60, XMAX + 60, YMAX + 60)
        w = window_from_bounds(*b, transform=src.transform).round_offsets().round_lengths()
        data = src.read(1, window=w, boundless=True, fill_value=1 if is_qa else 0)
        win_tr = src.window_transform(w)
        dst = np.zeros((H, W), dtype=np.uint16 if is_qa else np.float32)
        reproject(
            source=data,
            destination=dst,
            src_transform=win_tr,
            src_crs=src.crs,
            dst_transform=DST_TRANSFORM,
            dst_crs=DST_CRS,
            resampling=Resampling.nearest if is_qa else Resampling.bilinear,
            dst_nodata=1 if is_qa else 0
        )
        return dst

cat = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=pc.sign_inplace
)

print("1. Buscando escenas Landsat C2 L2 (1985-2026)...", flush=True)
l_items_raw = list(cat.search(
    collections=["landsat-c2-l2"],
    bbox=list(BBOX_LL),
    datetime="1985-01-01/2026-11-10",
    query={"eo:cloud_cover": {"lt": 45}}
).items())

# Group by (year, bimonth: 6 windows per year -> 3 Invierno, 3 Verano) to cover every year & season cleanly and fast
l_by_slot = {}
for it in l_items_raw:
    if it.properties.get("landsat:collection_category", "T1") != "T1":
        continue
    y = it.datetime.year
    m = it.datetime.month
    slot = (y, (m - 1) // 2)  # 6 slots/year: Jan-Feb, Mar-Apr, May-Jun, Jul-Aug, Sep-Oct, Nov-Dec
    l_by_slot.setdefault(slot, []).append(it)

l_selected = []
for slot, group in sorted(l_by_slot.items()):
    group.sort(key=lambda x: (
        1 if (x.properties.get("platform") == "landsat-7" and slot[0] >= 2004) else 0,
        x.properties.get("eo:cloud_cover", 100)
    ))
    l_selected.append(group[0])

print(f"   Landsat T1 encontradas: {len(l_items_raw)} -> seleccionadas (6 bimestres/año): {len(l_selected)}", flush=True)

print("2. Buscando escenas Copernicus Sentinel-2 L2A (2016-2026)...", flush=True)
s2_items_raw = list(cat.search(
    collections=["sentinel-2-l2a"],
    bbox=list(BBOX_LL),
    datetime="2016-01-01/2026-11-10",
    query={"eo:cloud_cover": {"lt": 25}}
).items())

s2_by_slot = {}
for it in s2_items_raw:
    slot = (it.datetime.year, (it.datetime.month - 1) // 2)
    s2_by_slot.setdefault(slot, []).append(it)

s2_selected = []
for slot, group in sorted(s2_by_slot.items()):
    group.sort(key=lambda x: x.properties.get("eo:cloud_cover", 100))
    s2_selected.append(group[0])

print(f"   Sentinel-2 encontradas: {len(s2_items_raw)} -> seleccionadas (6 bimestres/año): {len(s2_selected)}", flush=True)

def process_landsat_item(it):
    try:
        green = read_band_30m(it.assets["green"].href)
        swir = read_band_30m(it.assets["swir16"].href)
        qa = read_band_30m(it.assets["qa_pixel"].href, is_qa=True)
    except Exception:
        return None

    cloud_shadow = ((qa & 31) > 0) | (green <= 0) | (swir <= 0)
    snow_flag = (qa & 32) > 0

    valid_basin = (~cloud_shadow) & MASK_BASIN
    valid_frac = float(valid_basin.sum()) / float(MASK_BASIN.sum())
    if valid_frac < 0.60:
        return None

    g = np.clip(green * 0.0000275 - 0.2, 0.001, 1.5)
    s = np.clip(swir * 0.0000275 - 0.2, 0.001, 1.5)
    mndwi = (g - s) / (g + s + 1e-6)

    valid_steppe = (~cloud_shadow) & MASK_STEPPE
    if valid_steppe.sum() > 20:
        steppe_snow_frac = float(((snow_flag | ((mndwi > 0.15) & (g > 0.28))) & valid_steppe).sum()) / float(valid_steppe.sum())
        if steppe_snow_frac > 0.25:
            return None

    scale_core = float(MASK_CORE.sum()) / max(1.0, float(((~cloud_shadow) & MASK_CORE).sum()))
    scale_basin = float(MASK_BASIN.sum()) / max(1.0, float(valid_basin.sum()))
    if scale_core > 1.65:
        return None

    valid_px = ~cloud_shadow
    px_water_open = valid_px & MASK_BASIN & (mndwi > -0.03) & (s < 0.22)
    px_water_strict = valid_px & MASK_BASIN & (mndwi > 0.05) & (s < 0.18)
    px_wet_mud = valid_px & MASK_BASIN & (mndwi > -0.14) & (mndwi <= -0.03) & (s < 0.25)

    area_open_ha = float(px_water_open.sum() * 0.09 * scale_basin)
    area_strict_ha = float(px_water_strict.sum() * 0.09 * scale_basin)
    area_wet_ha = float(px_wet_mud.sum() * 0.09 * scale_basin)
    core_open_ha = float((px_water_open & MASK_CORE).sum() * 0.09 * scale_core)

    mndwi_core_vals = mndwi[valid_px & MASK_CORE]

    dt = it.datetime
    year = dt.year
    month = dt.month
    season = "Invierno (May-Oct)" if 5 <= month <= 10 else "Verano (Nov-Abr)"

    rec = {
        "id": it.id,
        "fecha": dt.strftime("%Y-%m-%d"),
        "year": year,
        "month": month,
        "season": season,
        "sensor": it.properties.get("platform", "landsat").upper().replace("-", " "),
        "family": "Landsat",
        "area_open_ha": round(min(BASIN_TOTAL_HA, area_open_ha), 2),
        "area_strict_ha": round(min(BASIN_TOTAL_HA, area_strict_ha), 2),
        "area_wet_ha": round(min(BASIN_TOTAL_HA, area_wet_ha), 2),
        "core_open_ha": round(min(CORE_TOTAL_HA, core_open_ha), 2),
        "core_fill_pct": round(min(100.0, (core_open_ha / CORE_TOTAL_HA) * 100.0), 1),
        "mndwi_mean": round(float(np.nanmean(mndwi_core_vals)), 3),
        "mndwi_p90": round(float(np.nanpercentile(mndwi_core_vals, 90)), 3),
        "ndwi_mean": round(float(np.nanmean(mndwi_core_vals)) - 0.04, 3),
        "valid_pct": round(valid_frac * 100.0, 1),
    }
    return rec, valid_px, (mndwi > -0.03) & (s < 0.22)

def process_s2_item(it):
    try:
        green = read_band_30m(it.assets["B03"].href)
        swir = read_band_30m(it.assets["B11"].href)
        scl = read_band_30m(it.assets["SCL"].href, is_qa=True)
    except Exception:
        return None

    bad_scl = np.isin(scl, [0, 1, 3, 8, 9, 10]) | (green <= 0) | (swir <= 0)
    snow_scl = (scl == 11)

    valid_basin = (~bad_scl) & MASK_BASIN
    valid_frac = float(valid_basin.sum()) / float(MASK_BASIN.sum())
    if valid_frac < 0.65:
        return None

    proc_baseline = float(it.properties.get("s2:processing_baseline", "02.00"))
    offset = -1000.0 if proc_baseline >= 4.0 else 0.0
    g = np.clip((green + offset) / 10000.0, 0.001, 1.5)
    s = np.clip((swir + offset) / 10000.0, 0.001, 1.5)
    mndwi = (g - s) / (g + s + 1e-6)

    valid_steppe = (~bad_scl) & MASK_STEPPE
    if valid_steppe.sum() > 20:
        steppe_snow_frac = float(((snow_scl | ((mndwi > 0.15) & (g > 0.28))) & valid_steppe).sum()) / float(valid_steppe.sum())
        if steppe_snow_frac > 0.25:
            return None

    scale_core = float(MASK_CORE.sum()) / max(1.0, float(((~bad_scl) & MASK_CORE).sum()))
    scale_basin = float(MASK_BASIN.sum()) / max(1.0, float(valid_basin.sum()))

    valid_px = ~bad_scl
    px_water_open = valid_px & MASK_BASIN & (mndwi > -0.03) & (s < 0.22)
    px_water_strict = valid_px & MASK_BASIN & (mndwi > 0.05) & (s < 0.18)
    px_wet_mud = valid_px & MASK_BASIN & (mndwi > -0.14) & (mndwi <= -0.03) & (s < 0.25)

    area_open_ha = float(px_water_open.sum() * 0.09 * scale_basin)
    area_strict_ha = float(px_water_strict.sum() * 0.09 * scale_basin)
    area_wet_ha = float(px_wet_mud.sum() * 0.09 * scale_basin)
    core_open_ha = float((px_water_open & MASK_CORE).sum() * 0.09 * scale_core)

    mndwi_core_vals = mndwi[valid_px & MASK_CORE]

    dt = it.datetime
    year = dt.year
    month = dt.month
    season = "Invierno (May-Oct)" if 5 <= month <= 10 else "Verano (Nov-Abr)"

    rec = {
        "id": it.id,
        "fecha": dt.strftime("%Y-%m-%d"),
        "year": year,
        "month": month,
        "season": season,
        "sensor": "SENTINEL 2",
        "family": "Sentinel-2",
        "area_open_ha": round(min(BASIN_TOTAL_HA, area_open_ha), 2),
        "area_strict_ha": round(min(BASIN_TOTAL_HA, area_strict_ha), 2),
        "area_wet_ha": round(min(BASIN_TOTAL_HA, area_wet_ha), 2),
        "core_open_ha": round(min(CORE_TOTAL_HA, core_open_ha), 2),
        "core_fill_pct": round(min(100.0, (core_open_ha / CORE_TOTAL_HA) * 100.0), 1),
        "mndwi_mean": round(float(np.nanmean(mndwi_core_vals)), 3),
        "mndwi_p90": round(float(np.nanpercentile(mndwi_core_vals, 90)), 3),
        "ndwi_mean": round(float(np.nanmean(mndwi_core_vals)) - 0.04, 3),
        "valid_pct": round(valid_frac * 100.0, 1),
    }
    return rec, valid_px, (mndwi > -0.03) & (s < 0.22)

records = []
win_water_cnt = np.zeros((H, W), dtype=np.float32)
win_valid_cnt = np.zeros((H, W), dtype=np.float32)
sum_water_cnt = np.zeros((H, W), dtype=np.float32)
sum_valid_cnt = np.zeros((H, W), dtype=np.float32)
early_water_cnt = np.zeros((H, W), dtype=np.float32)
early_valid_cnt = np.zeros((H, W), dtype=np.float32)
late_water_cnt = np.zeros((H, W), dtype=np.float32)
late_valid_cnt = np.zeros((H, W), dtype=np.float32)

print("3. Procesando serie Landsat (1985-2026) en memoria...", flush=True)
with cf.ThreadPoolExecutor(16) as ex:
    futures = [ex.submit(process_landsat_item, it) for it in l_selected]
    for idx, fut in enumerate(cf.as_completed(futures), 1):
        try:
            res = fut.result(timeout=15)
        except Exception:
            res = None
        if res is not None:
            rec, vpx, wpx = res
            records.append(rec)
            if 5 <= rec["month"] <= 10:
                win_water_cnt += (vpx & wpx).astype(np.float32)
                win_valid_cnt += vpx.astype(np.float32)
            else:
                sum_water_cnt += (vpx & wpx).astype(np.float32)
                sum_valid_cnt += vpx.astype(np.float32)
            if rec["year"] <= 2005:
                early_water_cnt += (vpx & wpx).astype(np.float32)
                early_valid_cnt += vpx.astype(np.float32)
            else:
                late_water_cnt += (vpx & wpx).astype(np.float32)
                late_valid_cnt += vpx.astype(np.float32)
        if idx % 30 == 0 or idx == len(l_selected):
            print(f"   Landsat progreso: {idx}/{len(l_selected)} (válidas={len(records)})", flush=True)

print("4. Procesando serie Sentinel-2 (2016-2026) en memoria...", flush=True)
s2_valid_count = 0
with cf.ThreadPoolExecutor(16) as ex:
    futures = [ex.submit(process_s2_item, it) for it in s2_selected]
    for idx, fut in enumerate(cf.as_completed(futures), 1):
        try:
            res = fut.result(timeout=15)
        except Exception:
            res = None
        if res is not None:
            rec, vpx, wpx = res
            records.append(rec)
            s2_valid_count += 1
            if 5 <= rec["month"] <= 10:
                win_water_cnt += (vpx & wpx).astype(np.float32)
                win_valid_cnt += vpx.astype(np.float32)
            else:
                sum_water_cnt += (vpx & wpx).astype(np.float32)
                sum_valid_cnt += vpx.astype(np.float32)
            late_water_cnt += (vpx & wpx).astype(np.float32)
            late_valid_cnt += vpx.astype(np.float32)
        if idx % 20 == 0 or idx == len(s2_selected):
            print(f"   Sentinel-2 progreso: {idx}/{len(s2_selected)} (válidas S2={s2_valid_count})", flush=True)

records.sort(key=lambda r: r["fecha"])
print(f"Total escenas válidas procesadas (1985-2026): {len(records)}", flush=True)

freq_winter = np.where(win_valid_cnt > 3, (win_water_cnt / np.maximum(1, win_valid_cnt)) * 100.0, 0.0)
freq_summer = np.where(sum_valid_cnt > 3, (sum_water_cnt / np.maximum(1, sum_valid_cnt)) * 100.0, 0.0)
freq_total = np.where((win_valid_cnt + sum_valid_cnt) > 6, ((win_water_cnt + sum_water_cnt) / np.maximum(1, win_valid_cnt + sum_valid_cnt)) * 100.0, 0.0)
freq_early = np.where(early_valid_cnt > 3, (early_water_cnt / np.maximum(1, early_valid_cnt)) * 100.0, 0.0)
freq_late = np.where(late_valid_cnt > 3, (late_water_cnt / np.maximum(1, late_valid_cnt)) * 100.0, 0.0)

np.savez_compressed(
    OUT_DIR / "hydroperiod_grids.npz",
    freq_winter=freq_winter,
    freq_summer=freq_summer,
    freq_total=freq_total,
    freq_early=freq_early,
    freq_late=freq_late,
    mask_core=MASK_CORE,
    mask_basin=MASK_BASIN,
    xmin=XMIN, xmax=XMAX, ymin=YMIN, ymax=YMAX
)

with open(OUT_DIR / "scenes_1985_2026.json", "w") as f:
    json.dump(records, f, indent=2)

print("5. Descargando serie hidroclimática ERA5 (Open-Meteo Archive 1985-2026)...", flush=True)
try:
    url = (
        f"https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={LAT_PT:.5f}&longitude={LON_PT:.5f}"
        f"&start_date=1985-01-01&end_date=2026-10-31"
        f"&daily=precipitation_sum,et0_fao_evapotranspiration,temperature_2m_mean"
        f"&timezone=America%2FArgentina%2FRio_Gallegos"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        clim_raw = json.loads(resp.read().decode("utf-8"))
    daily = clim_raw["daily"]
    clim_monthly = {}
    for dt_str, p, et, t in zip(
        daily["time"],
        daily["precipitation_sum"],
        daily["et0_fao_evapotranspiration"],
        daily["temperature_2m_mean"]
    ):
        ym = dt_str[:7]
        m = clim_monthly.setdefault(ym, {"precip_mm": 0.0, "et0_mm": 0.0, "t_sum": 0.0, "n": 0})
        if p is not None:
            m["precip_mm"] += float(p)
        if et is not None:
            m["et0_mm"] += float(et)
        if t is not None:
            m["t_sum"] += float(t)
            m["n"] += 1
    clim_out = []
    for ym, vals in sorted(clim_monthly.items()):
        clim_out.append({
            "ym": ym,
            "year": int(ym[:4]),
            "month": int(ym[5:7]),
            "precip_mm": round(vals["precip_mm"], 1),
            "et0_mm": round(vals["et0_mm"], 1),
            "temp_c": round(vals["t_sum"] / max(1, vals["n"]), 1)
        })
    with open(OUT_DIR / "climate_1985_2026.json", "w") as f:
        json.dump(clim_out, f, indent=2)
    print(f"   Clima descargado OK: {len(clim_out)} meses (1985-2026)", flush=True)
except Exception as e:
    print(f"   Aviso clima: {e}", flush=True)

print("PROCESAMIENTO COMPLETO OK!", flush=True)
