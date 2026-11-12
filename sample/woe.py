"""「Where on Earth?」のサンプル動画(縦 1080x1920)。衛星写真で寄りから宇宙まで引いていく場所当て3択。

衛星画像: Sentinel-2 cloudless 2016 by EOX(Contains modified Copernicus Sentinel data 2016、CC BY 4.0)
読み上げ・効果音・文字の部品は Painted When?(/home/user/painted-when)のものを流用する。

使い方: python woe.py <場所の番号 0〜> <出力先>
"""
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, "/home/user/painted-when")
import tiles  # noqa: E402
import art_shorts as A  # noqa: E402
import quiz as Q  # noqa: E402
import narration as N  # noqa: E402

W, H, FPS = 1080, 1920, 30
MAXZ = tiles.MAXZ

PLACES = [
    # (正解, 国, 経度, 緯度, 冒頭の窓の幅(z14 の画素), 外れ2つ, ひとこと)
    ("Venice", "Italy", 12.3360, 45.4375, 420, ["Amsterdam", "St. Petersburg"], "A UNESCO World Heritage Site"),
    ("Mount Fuji", "Japan", 138.7274, 35.3606, 900, ["Mount Kilimanjaro", "Mount Rainier"], "A UNESCO World Heritage Site"),
    ("Angkor Wat", "Cambodia", 103.8670, 13.4125, 260, ["Borobudur", "Bagan"], "A UNESCO World Heritage Site"),
]
END_W = 540 * 2 ** 4          # いちばん引いたときの窓の幅(z14 の画素、約80km)
CREDIT = "Satellite image: Sentinel-2 cloudless 2016 by EOX · Contains modified Copernicus Sentinel data 2016 · CC BY 4.0"


class Earth:
    """場所を中心に、窓の幅 w(z14 の画素)の範囲を 1080x1920 に描く。ズームの段ごとにモザイクを用意する。"""

    def __init__(self, lon, lat):
        self.lon, self.lat = lon, lat
        self.mosaics = {}

    def level_for(self, w):
        # その段での窓の幅が 540〜1080 画素になる段(拡大は2倍まで)。z14 より細かい段はない
        f = MAXZ - math.log2(max(w, 1) / 540)
        return int(min(MAXZ, math.floor(f)))

    def mosaic(self, z):
        if z not in self.mosaics:
            self.mosaics[z] = tiles.mosaic(self.lon, self.lat, z, 1080, 1920)
        return self.mosaics[z]

    def render(self, w):
        z = self.level_for(w)
        m = self.mosaic(z)
        wl = w / 2 ** (MAXZ - z)
        hl = wl * H / W
        cx, cy = m.width / 2, m.height / 2
        return m.resize((W, H), Image.BICUBIC, box=(cx - wl / 2, cy - hl / 2, cx + wl / 2, cy + hl / 2))


def shade():
    """上と下を暗くして、文字を読みやすくする。"""
    a = np.zeros((H, W), np.float32)
    a[:460] = np.linspace(0.65, 0, 460)[:, None]
    a[1060:] = np.linspace(0, 0.75, H - 1060)[:, None]
    return Image.merge("RGBA", [Image.new("L", (W, H), 0)] * 3 + [Image.fromarray((a * 255).astype(np.uint8))])


def build(i, out):
    name, country, lon, lat, start_w, wrong, note = PLACES[i]
    import random
    rng = random.Random(name)
    labels = [name] + wrong
    rng.shuffle(labels)
    correct = labels.index(name)

    # 読み上げ(Google の声)と時刻
    tts = N.make_tts("google")
    lines = {
        "q": "Where on Earth is this?",
        "c0": f"Is it {labels[0]}?", "c1": f"{labels[1]}?", "c2": f"Or {labels[2]}?",
        "lock": "Lock in your answer!",
        "ans": f"It's {name}, in {country}!",
        "info": f"{note}.",
        "outro": "How did you do? Tell me in the comments.",
    }
    clips = {k: tts(t) for k, t in lines.items()}
    dur = {k: len(v) / N.SR for k, v in clips.items()}
    at = {"q": 0.08}
    at["c0"] = at["q"] + dur["q"] + 0.35
    at["c1"] = at["c0"] + dur["c0"] + 0.25
    at["c2"] = at["c1"] + dur["c1"] + 0.25
    at["lock"] = at["c2"] + dur["c2"] + 0.35
    reveal = at["lock"] + dur["lock"] + 2.0
    at["ans"] = reveal + 0.15
    at["info"] = at["ans"] + dur["ans"] + 0.3
    at["outro"] = at["info"] + dur["info"] + 0.6
    end = at["outro"] + dur["outro"] + 1.0
    zoom = (0.3, reveal - 0.3)    # 答えまでの間に、寄りから引いていく
    back = (reveal + 0.4, reveal + 2.6)   # 答えのあと、場所に向かってもう一度寄る
    back_w = start_w * 1.6

    # 音
    n = int(math.ceil(end * N.SR))
    voice, fx = np.zeros(n, np.float32), np.zeros(n, np.float32)

    def put(buf, x, t):
        k = int(t * N.SR)
        x = x[: max(0, n - k)]
        buf[k:k + len(x)] += x
    for k, x in clips.items():
        put(voice, x, at[k])
    put(fx, N.sfx_whoosh(), 0.0)
    for c in ("c0", "c1", "c2"):
        put(fx, N.sfx_pop(), at[c])
    t = reveal - 3.0
    while t < reveal - 0.05:
        put(fx, N.sfx_tick(), t)
        t += 0.5
    put(fx, N.sfx_ding(), reveal)
    mix = voice / max(1e-6, float(np.abs(voice).max())) * 0.8 + fx * 0.35
    mix /= max(1.0, float(np.abs(mix).max()) / 0.95)
    wav = out / f"woe_{i}.wav"
    N.write_wav(wav, np.stack([mix, mix], 1))

    # 画面の部品
    earth = Earth(lon, lat)
    sh = shade()
    kicker = Q.text_layer(["WHERE ON EARTH?"], A.font(A.SANS_BOLD, 30), Q.GOLD, W)
    qmain = Q.text_layer(["Where on Earth is this?"], A.font(A.SANS_BOLD, 64), Q.WHITE, W)
    qout = Q.text_layer(["How did you do?"], A.font(A.SANS_BOLD, 64), Q.WHITE, W)
    fch = A.font(A.SANS_BOLD, 38)
    cw = 400
    pills = [pill(lb, fch, cw, (16, 18, 22, 220), Q.WHITE, (255, 255, 255, 130)) for lb in labels]
    right = pill(labels[correct], fch, cw, Q.GOLD + (255,), (25, 20, 10), None)
    title = Q.text_layer([name], A.font(A.SERIF_IT, 62), Q.WHITE, W)
    sub = Q.text_layer([f"{country} · {note}"], A.font(A.SANS, 32), (225, 222, 214, 255), W)
    credit = Q.text_layer(["Satellite image: Sentinel-2 cloudless 2016 by EOX",
                           "Contains modified Copernicus Sentinel data 2016 · CC BY 4.0"],
                          A.font(A.SANS, 22), (215, 215, 215, 210), W, shadow=170)
    ys = [1080, 1180, 1280]          # 選択肢は縦に3つ(場所の名前は長いので)
    cx_pill = 480                    # 右側の YouTube のボタンを避けて少し左に

    def frame(t):
        e = A.ease((t - zoom[0]) / (zoom[1] - zoom[0]))
        w = math.exp(math.log(start_w) + (math.log(END_W) - math.log(start_w)) * e)
        b = A.ease((t - back[0]) / (back[1] - back[0]))
        if b > 0:
            w = math.exp(math.log(END_W) + (math.log(back_w) - math.log(END_W)) * b)
        img = earth.render(w).convert("RGBA")
        img.alpha_composite(sh)
        r = A.ease((t - reveal) / 0.3)
        # 答えの印:中心に輪を広げる
        if r > 0:
            d = ImageDraw.Draw(img)
            pulse = (t - reveal) % 1.2 / 1.2
            for k, rad in enumerate((26, 26 + 60 * pulse)):
                alpha = int(255 * r * (1 if k == 0 else 1 - pulse))
                d.ellipse([W / 2 - rad, H / 2 - rad, W / 2 + rad, H / 2 + rad], outline=Q.GOLD + (alpha,), width=6)
        img.alpha_composite(kicker, (0, 130))
        oa = A.ease((t - at["outro"]) / 0.4)
        if oa < 1:
            img.alpha_composite(Q.with_alpha(qmain, 1 - oa), (0, 178))
        if oa > 0:
            img.alpha_composite(Q.with_alpha(qout, oa), (0, 178))
        # 選択肢(最初から)と、読み上げに合わせた弾み
        for k, p in enumerate(pills):
            px, py = int(cx_pill - p.width / 2), ys[k] - p.height // 2
            if k == correct and r > 0:
                img.alpha_composite(Q.with_alpha(p, 1 - r), (px, py))
                img.alpha_composite(Q.with_alpha(right, r), (px, py))
                continue
            q = p
            if 0 <= t - at[f"c{k}"] < 0.4 and r <= 0:
                s = 1 + 0.08 * math.sin(math.pi * (t - at[f"c{k}"]) / 0.4)
                q = p.resize((int(p.width * s), int(p.height * s)), Image.BICUBIC)
            img.alpha_composite(Q.with_alpha(q, 1 - 0.7 * r), (int(cx_pill - q.width / 2), ys[k] - q.height // 2))
        # 残り時間のバー
        ta = 1 - A.ease((t - reveal) / 0.3)
        if ta > 0:
            left = 1 - min(1.0, max(0.0, t / reveal))
            d = ImageDraw.Draw(img)
            bx0, bw, by = cx_pill - cw // 2, cw, 1352
            d.rounded_rectangle([bx0, by, bx0 + bw, by + 8], radius=4, fill=(255, 255, 255, int(60 * ta)))
            if left > 0:
                col = Q.GOLD if left > 0.3 else (235, 110, 90)
                d.rounded_rectangle([bx0, by, bx0 + max(8, int(bw * left)), by + 8], radius=4,
                                    fill=col + (int(255 * ta),))
        # 答え合わせ:場所の名前と国
        ia = A.ease((t - at["ans"]) / 0.5)
        if ia > 0:
            img.alpha_composite(Q.with_alpha(title, ia), (0, 300))
            img.alpha_composite(Q.with_alpha(sub, ia), (0, 380))
        img.alpha_composite(credit, (0, 1440))
        return img.convert("RGB")

    for k in range(MAXZ, 7, -1):          # 使う段のモザイクを先に取得する
        if earth.level_for(start_w) >= k >= earth.level_for(END_W):
            earth.mosaic(k)
    frames = int(round(end * FPS))
    mp4 = out / f"woe_{i}_{name.replace(' ', '_')}.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", str(wav), "-map", "0:v", "-map", "1:a", "-t", f"{frames / FPS:.3f}",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(mp4)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(frames):
        p.stdin.write(frame(f / FPS).tobytes())
    p.stdin.close()
    p.wait()
    frame(0).save(out / f"woe_{i}_first.png")
    print(mp4, f"{end:.1f}s")
    return frame


def pill(label, fnt, w, fill, text_fill, outline):
    hgt = 84
    im = Image.new("RGBA", (w + 20, hgt + 20), (0, 0, 0, 0))
    s = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(s).rounded_rectangle([10, 14, 10 + w, 14 + hgt], radius=hgt // 2, fill=(0, 0, 0, 150))
    im.alpha_composite(s.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 10, 10 + w, 10 + hgt], radius=hgt // 2, fill=fill, outline=outline, width=3 if outline else 0)
    d.text((10 + w / 2, 10 + hgt / 2), label, font=fnt, fill=text_fill, anchor="mm")
    return im


if __name__ == "__main__":
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    build(int(sys.argv[1]), out)
