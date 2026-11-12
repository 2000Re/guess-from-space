"""places.py の場所を、寄り(start)と引き(end)の2枚ずつ並べた一覧画像にする。中心が合っているか、形が見えるかの確認用。

使い方: python tools/check_places.py [--only venice,mount-fuji] [--out check]
  check/places_<n>.jpg … 1枚に最大20か所。各場所の左が冒頭の寄り、右がいちばん引いたところ(中心に赤い印)
小さく描くので、動画を作るより少ないタイルで済む(タイルは tile_cache/ に保存され、動画づくりでも使われる)。
"""
import argparse
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import places as P  # noqa: E402
import tiles  # noqa: E402

TW, TH = 216, 384


def view(lon, lat, km):
    """幅 km の範囲を TW×TH に。表示の大きさに合う粗い段のタイルを使う。"""
    px14 = km * 1000 / tiles.meters_per_px(lat)
    z = int(min(tiles.MAXZ, math.floor(tiles.MAXZ - math.log2(max(px14, 1) / TW))))
    wl = px14 / 2 ** (tiles.MAXZ - z)
    m = tiles.mosaic(lon, lat, z, math.ceil(wl) + 2, math.ceil(wl * TH / TW) + 2)
    cx, cy = m.width / 2, m.height / 2
    hl = wl * TH / TW
    return m.resize((TW, TH), Image.BICUBIC, box=(cx - wl / 2, cy - hl / 2, cx + wl / 2, cy + hl / 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--out", default="check")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    ps = P.PLACES
    if args.only:
        keys = args.only.split(",")
        ps = [p for p in ps if P.key(p) in keys]
    fnt = ImageFont.truetype(str(ROOT / "fonts" / "LiberationSans-Bold.ttf"), 15)
    per, cols = 20, 5
    for page in range(0, len(ps), per):
        chunk = ps[page:page + per]
        rows = math.ceil(len(chunk) / cols)
        sheet = Image.new("RGB", (cols * (2 * TW + 12), rows * (TH + 30)), (20, 20, 20))
        for i, p in enumerate(chunk):
            x, y = (i % cols) * (2 * TW + 12), (i // cols) * (TH + 30)
            a = view(p["lon"], p["lat"], p["start"])
            b = view(p["lon"], p["lat"], p.get("end", P.END_KM))
            ImageDraw.Draw(b).ellipse([TW / 2 - 5, TH / 2 - 5, TW / 2 + 5, TH / 2 + 5], outline=(255, 40, 40), width=2)
            sheet.paste(a, (x, y + 26))
            sheet.paste(b, (x + TW + 2, y + 26))
            ImageDraw.Draw(sheet).text((x + 4, y + 5), f"{page + i}. {p['name']}", font=fnt, fill=(255, 255, 255))
            print(f"{page + i:3d} {p['name']}  tiles {tiles.stats}", flush=True)
        f = out / f"places_{page // per + 1}.jpg"
        sheet.save(f, quality=85)
        print(f)


if __name__ == "__main__":
    main()
