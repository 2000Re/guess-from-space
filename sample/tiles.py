"""Sentinel-2 cloudless 2016(EOX、CC BY 4.0)のタイルを取得して、指定範囲のモザイク画像を作る。"""
import io, math, time, urllib.request
from pathlib import Path
from PIL import Image

LAYER = "s2cloudless_3857"   # 2016年版(CC BY 4.0)。2017年以降は別ライセンスなので使わない
URL = "https://tiles.maps.eox.at/wmts/1.0.0/" + LAYER + "/default/g/{z}/{y}/{x}.jpg"
CACHE = Path(__file__).resolve().parent / "tile_cache"
MAXZ = 14
UA = "where-on-earth-sample/0.1"


def lonlat_to_px(lon, lat, z):
    n = 256 * 2 ** z
    x = (lon + 180) / 360 * n
    s = math.sin(math.radians(lat))
    y = (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * n
    return x, y


def tile(z, x, y):
    p = CACHE / f"{z}/{x}/{y}.jpg"
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(4):
            try:
                req = urllib.request.Request(URL.format(z=z, x=x, y=y), headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=30) as r:
                    p.write_bytes(r.read())
                break
            except Exception:
                if attempt == 3:
                    return Image.new("RGB", (256, 256), (20, 24, 30))
                time.sleep(2 ** attempt)
        time.sleep(0.05)
    return Image.open(p).convert("RGB")


def mosaic(lon, lat, z, w, h):
    """(lon, lat) を中心に、ズーム z で w×h 画素の画像。"""
    cx, cy = lonlat_to_px(lon, lat, z)
    x0, y0 = cx - w / 2, cy - h / 2
    tx0, ty0 = int(x0 // 256), int(y0 // 256)
    tx1, ty1 = int((x0 + w) // 256), int((y0 + h) // 256)
    out = Image.new("RGB", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256))
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            out.paste(tile(z, tx % (2 ** z), ty), ((tx - tx0) * 256, (ty - ty0) * 256))
    ox, oy = x0 - tx0 * 256, y0 - ty0 * 256
    return out.crop((int(ox), int(oy), int(ox) + w, int(oy) + h))
