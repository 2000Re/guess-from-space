"""チャンネルのアイコンとバナー、サイトの画像を作る(動画と同じ衛星写真・配色・フォント)。

使い方: python tools/make_branding.py [--out branding]
  branding/icon.png    アイコン 800x800(YouTube では円形に切り抜かれ、小さく表示される)
  branding/banner.png  バナー 2560x1440(文字は、どの端末でも表示される中央 1546x423 に収める)
  docs/icon.png・docs/banner.jpg  サイト用(アイコンの縮小と、バナーの中央部分)

衛星写真は動画と同じ Sentinel-2 cloudless 2016(EOX、CC BY 4.0)。出典はチャンネルの説明欄(branding/description.txt)に書く。
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import make_video as V  # noqa: E402
import tiles  # noqa: E402

ICON = (-11.4010, 21.1240, 11)        # アイコン: アフリカの「サハラの目」(同心円の地形)
STRIP = [                              # バナーの背景に並べる場所 (経度, 緯度, ズーム)
    (12.3360, 45.4375, 13),            # ヴェネツィア
    (55.1385, 25.1150, 13),            # パーム・ジュメイラ
    (138.7274, 35.3606, 11),           # 富士山
    (25.3960, 36.4040, 12),            # サントリーニ
    (-151.7415, -16.5004, 12),         # ボラボラ
    (-69.9800, 41.8500, 10),           # ケープコッド
    (-87.5347, 17.3158, 13),           # グレート・ブルーホール
]
NAVY = (11, 18, 32)


def icon(out):
    size = 800
    img = ImageOps.autocontrast(tiles.mosaic(*ICON[:2], ICON[2], size, size), cutoff=1)
    img = Image.blend(img, Image.new("RGB", img.size, NAVY), 0.35).convert("RGBA")
    # 周りを少し暗く(円形に切り抜かれたときの縁)
    yy, xx = np.mgrid[:size, :size]
    r = np.hypot(xx - size / 2, yy - size / 2) / (size / 2)
    a = np.clip((r - 0.5) / 0.5, 0, 1) * 0.7
    img.alpha_composite(Image.merge("RGBA", [Image.new("L", (size, size), 0)] * 3
                                    + [Image.fromarray((a * 255).astype(np.uint8))]))
    d = ImageDraw.Draw(img)
    c = size / 2
    # 動画の答えの印と同じ金色の輪と、照準の短い線
    for rad, wdt, al in ((150, 18, 255), (215, 8, 150)):
        d.ellipse([c - rad, c - rad, c + rad, c + rad], outline=V.GOLD + (al,), width=wdt)
    for ang in range(4):
        dx, dy = [(1, 0), (0, 1), (-1, 0), (0, -1)][ang]
        d.line([c + dx * 245, c + dy * 245, c + dx * 300, c + dy * 300], fill=V.GOLD + (255,), width=14)
    img.convert("RGB").save(out / "icon.png")
    return img


def banner(out):
    W, H = 2560, 1440
    canvas = Image.new("RGB", (W, H), NAVY)
    n = len(STRIP)
    tw = W // n + 1
    for i, (lon, lat, z) in enumerate(STRIP):
        canvas.paste(tiles.mosaic(lon, lat, z, tw, H), (i * (W // n), 0))
    # 中央の帯を暗くして文字を読みやすく
    shade = np.zeros((H, W), np.float32)
    y = np.arange(H)[:, None]
    shade += np.clip(1 - np.abs(y - H / 2) / 330, 0, 1) * 0.72 + 0.18
    canvas = canvas.convert("RGBA")
    canvas.alpha_composite(Image.merge("RGBA", [Image.new("L", (W, H), v) for v in NAVY]
                                       + [Image.fromarray((np.clip(shade, 0, 1) * 255).astype(np.uint8))]))
    t1 = V.text_layer(["GUESS FROM SPACE"], V.font(V.SANS_BOLD, 128), V.WHITE, W)
    t2 = V.text_layer(["Where on Earth is this?  ·  A satellite geography quiz"], V.font(V.SANS, 52), V.GOLD, W)
    canvas.alpha_composite(t1, (0, H // 2 - 150))
    canvas.alpha_composite(t2, (0, H // 2 + 20))
    canvas = canvas.convert("RGB")
    canvas.save(out / "banner.png")
    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "branding"))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    ic = icon(out)
    bn = banner(out)
    docs = ROOT / "docs"
    ic.convert("RGB").resize((192, 192), Image.LANCZOS).save(docs / "icon.png")
    bn.crop((0, 1440 // 2 - 380, 2560, 1440 // 2 + 380)).resize((1280, 380), Image.LANCZOS).save(
        docs / "banner.jpg", quality=86)
    print(out / "icon.png", out / "banner.png", f"tiles: {tiles.stats}")


if __name__ == "__main__":
    main()
