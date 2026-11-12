"""Sentinel-2 cloudless 2016(EOX、CC BY 4.0)のタイルを取得して、指定範囲のモザイク画像を作る。

- 層は s2cloudless_3857(2016年版、Web メルカトル)だけを使う。2017年以降の層はライセンスが違うので使わない
- 取得したタイルは tile_cache/ に保存し、同じタイルを二度取りに行かない(GitHub Actions では actions/cache で引き継ぐ)
- 配信元に負荷をかけないよう、通信は1本ずつ、MIN_INTERVAL 秒以上あけて行う
"""
import io
import math
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

LAYER = "s2cloudless_3857"
URL = "https://tiles.maps.eox.at/wmts/1.0.0/" + LAYER + "/default/g/{z}/{y}/{x}.jpg"
CACHE = Path(os.environ.get("TILE_CACHE") or Path(__file__).resolve().parent / "tile_cache")
MAXZ = 14                       # 最大ズーム(約10m/画素)
MIN_INTERVAL = 0.1              # 通信の間隔(秒)
USER_AGENT = os.environ.get("GFS_USER_AGENT", "guess-from-space/1.0 (+https://github.com/2000Re/guess-from-space)")

# 出典(CC BY 4.0 の条件。動画・説明欄・サイトに必ず書く)
ATTRIBUTION = ("Sentinel-2 cloudless 2016 by EOX IT Services GmbH (https://s2maps.eu) · "
               "Contains modified Copernicus Sentinel data 2016 · CC BY 4.0")
ATTRIBUTION_LINES = ["Satellite image: Sentinel-2 cloudless 2016 by EOX (s2maps.eu)",
                     "Contains modified Copernicus Sentinel data 2016 · CC BY 4.0"]

_last = [0.0]
stats = {"fetched": 0, "cached": 0}


def lonlat_to_px(lon, lat, z):
    n = 256 * 2 ** z
    x = (lon + 180) / 360 * n
    s = math.sin(math.radians(lat))
    y = (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * n
    return x, y


def meters_per_px(lat, z=MAXZ):
    return 40075016.686 * math.cos(math.radians(lat)) / (256 * 2 ** z)


def _fetch(url):
    wait = MIN_INTERVAL - (time.monotonic() - _last[0])
    if wait > 0:
        time.sleep(wait)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read()
    finally:
        _last[0] = time.monotonic()


def tile(z, x, y):
    p = CACHE / f"{z}/{x}/{y}.jpg"
    if p.exists():
        stats["cached"] += 1
    else:
        data = None
        for attempt in range(4):
            try:
                data = _fetch(URL.format(z=z, x=x, y=y))
                Image.open(io.BytesIO(data)).verify()     # 壊れた画像をキャッシュしない
                break
            except urllib.error.HTTPError as e:
                if e.code in (400, 404):                  # 範囲外(極地など)。海の色で埋める
                    return Image.new("RGB", (256, 256), (8, 22, 48))
                err = e
            except Exception as e:  # noqa: BLE001 通信断・壊れた画像
                err = e
            data = None
            time.sleep(2 ** (attempt + 1))
        if data is None:
            raise RuntimeError(f"タイル {z}/{x}/{y} を取得できませんでした: {err}")
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".part")
        tmp.write_bytes(data)
        tmp.replace(p)
        stats["fetched"] += 1
    im = Image.open(p)
    return (im.convert("RGBA") if im.mode == "P" else im).convert("RGB")


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
