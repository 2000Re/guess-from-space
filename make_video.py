"""Guess From Space: 衛星写真の場所当て3択クイズの縦動画(1080x1920、15〜17秒)を作る。

  0秒    衛星写真を寄りで画面いっぱいに。最初のコマから問い・3択・残り時間のバー。0秒に効果音、すぐ読み上げ
  〜     「Is it A? B? Or C?」に合わせて選択肢が弾み、その間に広い範囲まで引いていく
  答え   「Lock in your answer!」→ 約2秒 → チャイムで正解が金色に。中心に輪の印、場所名・国・ひとこと
  最後   その場所へもう一度寄り、見出しが「How did you do?」に変わる
画面下には衛星画像の出典(CC BY 4.0 の条件)を常に出す。

衛星画像: Sentinel-2 cloudless 2016 by EOX(Contains modified Copernicus Sentinel data 2016、CC BY 4.0)

使い方:
  python make_video.py --history upload_history.json --out out      投稿用(未投稿の場所を選び、out/meta.json も書く)
  python make_video.py --place venice --tts dummy --out out          場所を指定して試す(--place は places.key の名前)
"""
import argparse
import json
import math
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import narration as N
import places as P
import locales
import tiles

HERE = Path(__file__).resolve().parent
FONT_DIR = HERE / "fonts"
SERIF_IT = FONT_DIR / "LiberationSerif-Italic.ttf"
SANS = FONT_DIR / "LiberationSans-Regular.ttf"
SANS_BOLD = FONT_DIR / "LiberationSans-Bold.ttf"

W, H, FPS = 1080, 1920, 30
TZ = ZoneInfo("Asia/Tokyo")
GOLD = (236, 200, 120)
WHITE = (250, 246, 236)
CHANNEL = "Guess From Space"
CHANNEL_HANDLE = "@guess-from-space"
SITE = "https://2000re.github.io/guess-from-space"

QUESTION = "Where on Earth is this?"
CHOICE_YS = [1080, 1180, 1280]   # 選択肢は縦に3つ(場所の名前は長いので)
CHOICE_CX = 480                  # 右側の YouTube のボタンを避けて少し左に
CHOICE_W = 440
TIMER_Y = 1352
CREDIT_Y = 1440


TAIL = 0.4          # 最後の読み上げのあとの間(秒)。以前は 1.0(2026-11-21 に短くした)
LOOP_SEC = 1.1      # 最後のこの秒数で、冒頭の寄りの場面に戻る

# ---------------------------------------------------------------- 文字と部品


def font(path, size):
    return ImageFont.truetype(str(path), size)


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def text_layer(lines, fnt, fill, width=W, spacing=1.18, shadow=200):
    """中央揃えの文字(ぼかした影つき)の RGBA 画像。"""
    lh = int(fnt.size * spacing)
    layer = Image.new("RGBA", (width, lh * len(lines) + 12), (0, 0, 0, 0))
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    d, ds = ImageDraw.Draw(layer), ImageDraw.Draw(sh)
    for i, ln in enumerate(lines):
        y = i * lh + int(lh * 0.8)
        ds.text((width / 2, y + 3), ln, font=fnt, fill=(0, 0, 0, shadow), anchor="ms")
        d.text((width / 2, y), ln, font=fnt, fill=fill, anchor="ms")
    out = sh.filter(ImageFilter.GaussianBlur(5))
    out.alpha_composite(layer)
    return out


def with_alpha(layer, a):
    if a >= 1:
        return layer
    out = layer.copy()
    out.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
    return out


def wrap(text, fnt, max_w):
    """1行に収まらなければ、2行の長さがなるべく揃う位置で折り返す。"""
    if fnt.getlength(text) <= max_w:
        return [text]
    words = text.split()
    best = min(range(1, len(words)), key=lambda i: max(fnt.getlength(" ".join(words[:i])),
                                                       fnt.getlength(" ".join(words[i:]))))
    return [" ".join(words[:best]), " ".join(words[best:])]


def fit_font(text, path, size, max_w, min_size=24):
    while size > min_size and font(path, size).getlength(text) > max_w:
        size -= 2
    return font(path, size)


def pill(label, w, fill, text_fill, outline):
    hgt = 84
    im = Image.new("RGBA", (w + 20, hgt + 20), (0, 0, 0, 0))
    s = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(s).rounded_rectangle([10, 14, 10 + w, 14 + hgt], radius=hgt // 2, fill=(0, 0, 0, 150))
    im.alpha_composite(s.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 10, 10 + w, 10 + hgt], radius=hgt // 2, fill=fill, outline=outline,
                        width=3 if outline else 0)
    fnt = fit_font(label, SANS_BOLD, 38, w - 50)
    d.text((10 + w / 2, 10 + hgt / 2), label, font=fnt, fill=text_fill, anchor="mm")
    return im


def shade():
    """上と下を暗くして、文字を読みやすくする。"""
    a = np.zeros((H, W), np.float32)
    a[:520] = np.linspace(0.65, 0, 520)[:, None]
    a[1000:] = np.linspace(0, 0.75, H - 1000)[:, None]
    return Image.merge("RGBA", [Image.new("L", (W, H), 0)] * 3 + [Image.fromarray((a * 255).astype(np.uint8))])


# ---------------------------------------------------------------- 衛星写真


class Earth:
    """場所を中心に、幅 km キロメートルの範囲を W×H に描く。ズームの段ごとにモザイクを用意する。"""

    def __init__(self, lon, lat):
        self.lon, self.lat = lon, lat
        self.mpp = tiles.meters_per_px(lat)        # z14 の1画素の大きさ(m)
        self.mosaics = {}

    def px14(self, km):
        return km * 1000 / self.mpp

    def level_for(self, km):
        # その段での窓の幅が 540〜1080 画素になる段(拡大は2倍まで)。z14 より細かい段はない
        f = tiles.MAXZ - math.log2(max(self.px14(km), 1) / 540)
        return int(min(tiles.MAXZ, math.floor(f)))

    def mosaic(self, z):
        if z not in self.mosaics:
            self.mosaics[z] = tiles.mosaic(self.lon, self.lat, z, W, H)
        return self.mosaics[z]

    def prefetch(self, km_min, km_max):
        for z in range(self.level_for(km_min), self.level_for(km_max) - 1, -1):
            self.mosaic(z)

    def render(self, km, size=(W, H)):
        z = self.level_for(km)
        m = self.mosaic(z)
        wl = self.px14(km) / 2 ** (tiles.MAXZ - z)
        hl = wl * H / W
        cx, cy = m.width / 2, m.height / 2
        return m.resize(size, Image.BICUBIC, box=(cx - wl / 2, cy - hl / 2, cx + wl / 2, cy + hl / 2))


# ---------------------------------------------------------------- 1本の動画


def choices_for(place, rng):
    labels = [place["name"]] + list(place["wrong"])
    rng.shuffle(labels)
    return labels, labels.index(place["name"])


# 毎回ちがう言い回し(繰り返しの多い動画に見えないように)。番号で回すので、同じ番号なら作り直しても同じ
LINES = {
    "q": [QUESTION, "Can you name this place from space?", "Where in the world is this?", "Which famous place is this?",
          "Do you recognize this place?"],
    "lock": ["Lock in your answer!", "Pick your place!", "Got your guess?", "Make your choice!", "Final answer?"],
    "outro": ["How did you do? Tell me in the comments.", "Did you recognize it?", "Have you been there? Tell me below!",
              "Were you right? Comment your answer!", "Which place should we fly over next?"],
}
# ゲームの舞台の回(places.GAME_PLACES)の言い回し
GAME_LINES = {
    "q": ["A famous video game is based on this place. Where is it?",
          "Gamers, you may know this place. Where on Earth is it?",
          "This real place inspired a famous video game. Can you name it?"],
    "outro": ["Have you played it? Tell me in the comments!", "Which game should we visit next? Comment below!",
              "Did you know this place from the game?"],
}
GAME_KICKER = "GAME WORLD · REAL PLACE"
LEADS = ["Can you guess the place from space? Comment your answer before the reveal! 🌍",
         "Name this place before the camera zooms out! 🛰️",
         "Pause and guess first: where on Earth is this? 🌍",
         "How well do you know the world from above? Guess the place! 🛰️"]


def vary(number, key, game=False):
    opts = GAME_LINES[key] if game and key in GAME_LINES else LINES[key]
    return opts[(number + sum(map(ord, key))) % len(opts)]


def script(place, labels, number=1):
    game = bool(place.get("game"))
    return {
        "q": vary(number, "q", game),
        "c0": f"Is it {labels[0]}?", "c1": f"{labels[1]}?", "c2": f"Or {labels[2]}?",
        "lock": vary(number, "lock"),
        "ans": f"It's {P.spoken_name(place)}, {P.where(place)}!",
        # ひとこと(note)は読み上げず、画面に出すだけ(2026-11-21〜。答えのあとに離れる人が多かったので短くした)
        "outro": vary(number, "outro", game),
    }


def build(place, labels, correct, tts, out, stem="quiz", number=1):
    """動画を out/<stem>.mp4 に書き、(ファイル名, 長さ, frame 関数) を返す。"""
    start_km = place["start"]
    end_km = place.get("end", P.END_KM)

    lines = script(place, labels, number)
    clips = {k: tts(t) for k, t in lines.items()}
    dur = {k: len(v) / N.SR for k, v in clips.items()}
    at = {"q": 0.08}
    # 間は短めに(2026-11-21 に詰めた。平均視聴割合が Wait, That Big? の 90% 台に対して 70% 台だったため)
    at["c0"] = at["q"] + dur["q"] + 0.2
    at["c1"] = at["c0"] + dur["c0"] + 0.15
    at["c2"] = at["c1"] + dur["c1"] + 0.15
    at["lock"] = at["c2"] + dur["c2"] + 0.2
    reveal = at["lock"] + dur["lock"] + 1.5
    at["ans"] = reveal + 0.15
    at["outro"] = at["ans"] + dur["ans"] + 0.35
    end = at["outro"] + dur["outro"] + TAIL
    zoom = (0.3, reveal - 0.3)              # 答えまでの間に、寄りから引いていく
    loop = (end - LOOP_SEC, end)            # 最後に冒頭と同じ寄りの場面へ戻る(くり返し再生のつながりを自然に)
    back = (reveal + 0.4, min(reveal + 2.6, loop[0]))   # 答えのあと、場所に向かってもう一度寄る(最後の区間の前まで)
    back_km = start_km * 1.6

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
    wav = out / f"{stem}.wav"
    N.write_wav(wav, np.stack([mix, mix], 1))

    # 画面の部品
    earth = Earth(place["lon"], place["lat"])
    earth.prefetch(start_km, end_km)
    sh = shade()
    kicker = text_layer([GAME_KICKER if place.get("game") else "GUESS FROM SPACE"], font(SANS_BOLD, 30), GOLD)
    qmain = text_layer([QUESTION], font(SANS_BOLD, 64), WHITE)
    qout = text_layer(["How did you do?"], font(SANS_BOLD, 64), WHITE)
    pills = [pill(lb, CHOICE_W, (16, 18, 22, 220), WHITE, (255, 255, 255, 130)) for lb in labels]
    right = pill(labels[correct], CHOICE_W, GOLD + (255,), (25, 20, 10), None)
    title = text_layer([place["name"]], fit_font(place["name"], SERIF_IT, 66, 980), WHITE)
    fsub = font(SANS, 32)
    sub = text_layer(wrap(f"{place['country']} · {place['note']}", fsub, 960), fsub, (232, 228, 218, 255))
    credit = text_layer(tiles.ATTRIBUTION_LINES, font(SANS, 23), (230, 230, 230, 235), shadow=255)
    credit.alpha_composite(credit.copy())        # 影を2重にして、明るい地面でも読めるように

    def frame(t):
        e = ease((t - zoom[0]) / (zoom[1] - zoom[0]))
        km = math.exp(math.log(start_km) + (math.log(end_km) - math.log(start_km)) * e)
        b = ease((t - back[0]) / (back[1] - back[0]))
        if b > 0:
            km = math.exp(math.log(end_km) + (math.log(back_km) - math.log(end_km)) * b)
        lp = ease((t - loop[0]) / (loop[1] - loop[0]))
        if lp > 0:
            km = math.exp(math.log(km) + (math.log(start_km) - math.log(km)) * lp)
        img = earth.render(km).convert("RGBA")
        img.alpha_composite(sh)
        r = ease((t - reveal) / 0.3) * (1 - lp)
        if r > 0:      # 答えの印:中心に輪を広げる(別の層に描いて重ねる。直接描くと薄い輪が濃く出る)
            ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(ring)
            pulse = (t - reveal) % 1.2 / 1.2
            for k, rad in enumerate((48, 48 + 70 * pulse)):
                alpha = int(255 * r * (1 if k == 0 else 1 - pulse))
                box = [W / 2 - rad, H / 2 - rad, W / 2 + rad, H / 2 + rad]
                # 明るい地面(砂漠・雪)でも見えるよう、暗い縁取りの上に金色の輪
                d.ellipse([box[0] - 3, box[1] - 3, box[2] + 3, box[3] + 3], outline=(10, 14, 24, alpha * 2 // 3), width=12)
                d.ellipse(box, outline=GOLD + (alpha,), width=6)
            img.alpha_composite(ring)
        img.alpha_composite(kicker, (0, 130))
        oa = ease((t - at["outro"]) / 0.4) * (1 - lp)
        if oa < 1:
            img.alpha_composite(with_alpha(qmain, 1 - oa), (0, 178))
        if oa > 0:
            img.alpha_composite(with_alpha(qout, oa), (0, 178))
        # 選択肢(最初から)と、読み上げに合わせた弾み
        for k, p in enumerate(pills):
            px, py = int(CHOICE_CX - p.width / 2), CHOICE_YS[k] - p.height // 2
            if k == correct and r > 0:
                img.alpha_composite(with_alpha(p, 1 - r), (px, py))
                img.alpha_composite(with_alpha(right, r), (px, py))
                continue
            q = p
            if 0 <= t - at[f"c{k}"] < 0.4 and r <= 0:
                s = 1 + 0.08 * math.sin(math.pi * (t - at[f"c{k}"]) / 0.4)
                q = p.resize((int(p.width * s), int(p.height * s)), Image.BICUBIC)
            img.alpha_composite(with_alpha(q, 1 - 0.7 * r), (int(CHOICE_CX - q.width / 2), CHOICE_YS[k] - q.height // 2))
        # 残り時間のバー
        ta = 1 - ease((t - reveal) / 0.3)
        left = 1 - min(1.0, max(0.0, t / reveal))
        if lp > 0:                  # 最後は、冒頭と同じく満タンのバーに戻す
            ta, left = lp, 1.0
        if ta > 0:
            d = ImageDraw.Draw(img)
            bx0 = CHOICE_CX - CHOICE_W // 2
            d.rounded_rectangle([bx0, TIMER_Y, bx0 + CHOICE_W, TIMER_Y + 8], radius=4, fill=(255, 255, 255, int(60 * ta)))
            if left > 0:
                col = GOLD if left > 0.3 else (235, 110, 90)
                d.rounded_rectangle([bx0, TIMER_Y, bx0 + max(8, int(CHOICE_W * left)), TIMER_Y + 8], radius=4,
                                    fill=col + (int(255 * ta),))
        # 答え合わせ:場所の名前・国・ひとこと
        ia = ease((t - at["ans"]) / 0.5) * (1 - lp)
        if ia > 0:
            img.alpha_composite(with_alpha(title, ia), (0, 300))
            img.alpha_composite(with_alpha(sub, ia), (0, 385))
        img.alpha_composite(credit, (0, CREDIT_Y))
        return img.convert("RGB")

    frames = int(round(end * FPS))
    mp4 = out / f"{stem}.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", str(wav), "-map", "0:v", "-map", "1:a", "-t", f"{frames / FPS:.3f}",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(mp4)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for f in range(frames):
            p.stdin.write(frame(f / FPS).tobytes())
    finally:
        p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg が失敗しました")
    wav.unlink()

    # サイト用の画像(引いたところ、縦長の小さい JPEG。出典はページに書く)
    earth.render(min(end_km, start_km * 2.5), (360, 640)).save(out / "site.jpg", quality=82)
    frame(0).save(out / "first_frame.jpg", quality=88)
    return mp4.name, end, frame


# ---------------------------------------------------------------- 場所の選び方


def load_history(path):
    p = Path(path) if path else None
    return json.loads(p.read_text()) if p and p.exists() else []


NATURE_SHARE = 0.3
GAME_EVERY = 7          # この本数に1本、ゲームの舞台の回(番号が GAME_EVERY の倍数の回)


def choose_game(history, rng):
    """まだ出していないゲームの舞台から選ぶ。ふつうの回で最近出した場所・直前と同じ国は後回し。全部出したら None。"""
    used = {h["key"] for h in history}
    fresh = [p for p in P.GAME_PLACES if P.key(p) not in used]
    if not fresh:
        return None
    recent = {h["key"] for h in history[-20:]}
    last = history[-1]["key"] if history else None
    last_country = next((p["country"] for p in P.ALL_PLACES if P.key(p) == last), None)
    best = [p for p in fresh if P.key(p)[len("game-"):] not in recent and p["country"] != last_country]
    return rng.choice(best or fresh)
GREY_CITY_SHARE = 0.1


def choose_place(history, rng):
    """まだ出していない場所から選ぶ。直前の回と同じ国は避ける。全部出したら、いちばん前に出した場所から繰り返す。"""
    used = [h["key"] for h in history]
    last_country = None
    if history:
        last = next((p for p in P.ALL_PLACES if P.key(p) == history[-1]["key"]), None)
        last_country = last and last["country"]
    fresh = [p for p in P.PLACES if P.key(p) not in used]
    if not fresh:
        print("警告: 場所のリストを使い切りました。places.py に場所を足してください。前に出した場所を繰り返します",
              file=sys.stderr)
        order = {k: i for i, k in enumerate(used)}      # 後の回で上書きされる = 最後に出した位置
        fresh = sorted(P.PLACES, key=lambda p: order.get(P.key(p), -1))[: max(1, len(P.PLACES) // 4)]
    pool = [p for p in fresh if p["country"] != last_country] or fresh
    # 街・海岸・島の形(リスボン・ケープコッドなど)の方が、山・湖・火山などの内陸の自然や、灰色の街並みばかりの
    # 街より見られていた(2026-11-21 の stats.md)ので、自然は NATURE_SHARE、灰色の街は GREY_CITY_SHARE の割合だけにする
    groups = [([p for p in pool if P.key(p) in P.NATURE], NATURE_SHARE),
              ([p for p in pool if P.key(p) in P.GREY_CITY], GREY_CITY_SHARE),
              ([p for p in pool if P.key(p) not in P.NATURE | P.GREY_CITY], 1 - NATURE_SHARE - GREY_CITY_SHARE)]
    groups = [(g, w) for g, w in groups if g]
    r, acc = rng.random() * sum(w for _, w in groups), 0.0
    for g, w in groups:
        acc += w
        if r < acc:
            return rng.choice(g)
    return rng.choice(groups[-1][0])


# ---------------------------------------------------------------- YouTube とサイト


def _yt(s):
    """YouTube はタイトル・説明文の < > を受け付けないので置き換える。"""
    return str(s).replace("<", "‹").replace(">", "›")


# 題名の型。番号順に回す。どの型だったかは upload_history.json の title_style に残り、stats.md で比べる。
# 地域名(in Europe など)は、外れの選択肢が別の地域だと答えが絞れてしまうので入れない
TITLES = [
    ("classic", "Where on Earth is this? 🌍 Satellite Quiz"),
    ("space", "Can you name this place from space? 🛰️"),
    ("photo", "Guess the place from this satellite photo 🌍"),
    ("width", "This photo is only {km} km wide. Where on Earth is it? 🛰️"),
    ("orbit", "Seen from orbit: can you tell where this is? 🛰️"),
    ("zoom", "Zoom out and guess the place 🌍"),
    ("famous", "A famous place seen from space. Can you name it? 🛰️"),
    ("pros", "Geography pros: where on Earth is this? 🌍"),
    ("five_seconds", "Can you name this place in 5 seconds? 🛰️"),
    ("above", "What famous place is this, seen from above? 🌍"),
    ("across", "Just {km} km across. Can you guess this place? 🛰️"),
    ("map_lovers", "Map lovers: can you recognize this place from space? 🌍"),
]


# ゲームの舞台の回の題名(ゲームの回の中で順に回す)。ゲーム名は題名に書かない(答えの手がかりになるので)
GAME_TITLES = [
    ("game_real", "This video game place is real. Where on Earth is it? 🎮"),
    ("game_gamers", "Gamers: can you find this game setting from space? 🎮"),
    ("game_world", "A famous game world, seen from space. Where is it? 🛰️"),
]


def video_title(number, place=None):
    """(題名, 型)。答えは書かない。番号順に回すので、毎回ちがう題名になる(12本で一周)。
    {km} は冒頭の写真の幅(places.py の start)。答えの手がかりにはならない。"""
    if place and place.get("game"):
        style, title = GAME_TITLES[(number // GAME_EVERY) % len(GAME_TITLES)]
        return title, style
    style, title = TITLES[(number - 1) % len(TITLES)]
    if "{km}" in title:
        if not place or not place.get("start"):
            style, title = TITLES[0]
        else:
            km = place["start"]
            title = title.format(km=f"{km:g}")
    return title, style


# 姉妹チャンネル(説明欄の終わりで紹介する。上級者向け機能でリンクがクリックできる)
SISTERS = [
    ("🗺️ Wait, That Big? — the true size of countries on the map", "https://www.youtube.com/@wait-that-big"),
    ("🎨 Painted When? — guess the year a famous painting was made", "https://www.youtube.com/@painted-when"),
    ("🔍 Too Close to Tell — guess the museum object from an extreme close-up", "https://www.youtube.com/@too-close-to-tell"),
]


def youtube_meta(place, labels, correct, number):
    answer = labels[correct]
    game = place.get("game")
    lead = ("A real place from a famous video game, seen from space. Can you name it before the reveal? 🎮"
            if game else LEADS[number % len(LEADS)])
    lines = [
        lead,
        "",
        "Choices: " + " / ".join(labels),
        "",
        "⬇️ Answer below ⬇️",
        ".", ".", ".",
        f"Answer: {answer} ({place['country']})",
        (place["game_desc"] if game else place["note"].rstrip(".") + "."),
        f"Map: https://www.openstreetmap.org/?mlat={place['lat']:.4f}&mlon={place['lon']:.4f}#map=12/"
        f"{place['lat']:.4f}/{place['lon']:.4f}",
        "",
        f"Play more on the website: {SITE}/",
        "",
        "More quizzes from the same creator:",
        *[f"{t}: {u}" for t, u in SISTERS],
        "",
        "Satellite image: " + tiles.ATTRIBUTION,
        "License: https://creativecommons.org/licenses/by/4.0/",
        *(["This video uses only satellite images, with no game footage. "
           "It is not affiliated with or endorsed by the game's makers."] if game else []),
        "",
        "#geography #satellite #geographyquiz #shorts" + (" #unesco" if place.get("unesco") else "")
        + (" #gaming #videogames" if game else ""),
    ]
    tags = ["geography quiz", "satellite", "satellite images", "guess the place", "earth from space", "travel",
            "world heritage", "quiz", "geography", place["name"], place["country"]]
    if game:
        tags += ["video game locations", "real life game locations", *game.split(" and ")]
    desc = _yt("\n".join(lines))[:4900]
    style = video_title(number, place)[1]
    return {
        # 番号を先頭に(スマホの YouTube Studio の一覧でタイトルが切れても番号が見えるように)。
        # 「#15」だとハッシュタグ扱いされることがあるので「[15]」にする
        "title": _yt(f"[{number}] {video_title(number, place)[0]}")[:100],
        "title_style": style,
        "description": desc,
        # 題名と説明の翻訳(日本語・スペイン語・フランス語・ドイツ語・ポルトガル語)
        "localizations": locales.build(style, number, place.get("start"), desc, game=bool(game)),
        "tags": tags,
        "answer": answer,
    }


def site_fields(place, labels, correct):
    return {
        "name": place["name"],
        "country": place["country"],
        "note": place["note"],
        "lon": place["lon"],
        "lat": place["lat"],
        "choices": labels,
        "answer": correct,
    }


# ---------------------------------------------------------------- main


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--history", help="投稿記録 upload_history.json。ここにある場所は選ばない。"
                                      "指定すると、投稿用の out/meta.json(タイトル・説明文など)も書き出す")
    ap.add_argument("--place", help="場所を指定する(places.key の名前、例: venice、mount-fuji)")
    ap.add_argument("--tts", choices=["google", "dummy"], default="google")
    ap.add_argument("--seed", type=int, help="選び方・選択肢の順番の乱数の種(既定は回の番号)")
    ap.add_argument("--out", default="out")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    history = load_history(args.history)
    number = max([h["number"] for h in history], default=0) + 1
    rng = random.Random(args.seed if args.seed is not None else number * 7919)
    if args.place:
        found = [p for p in P.ALL_PLACES if P.key(p) == args.place]
        if not found:
            raise SystemExit(f"場所が見つかりません: {args.place}(候補: {', '.join(P.key(p) for p in P.ALL_PLACES)})")
        place = found[0]
    else:
        place = (number % GAME_EVERY == 0 and choose_game(history, rng)) or choose_place(history, rng)
    labels, correct = choices_for(place, rng)
    print(f"#{number} {place['name']} ({place['country']})  choices: {labels}")

    stem = f"{number:04d}-{P.key(place)}"
    video, seconds, _ = build(place, labels, correct, N.make_tts(args.tts), out, stem, number)
    print(f"{out / video}  {seconds:.1f}s  tiles: {tiles.stats}")

    if args.history:
        meta = {
            "number": number,
            "key": P.key(place),
            "date": datetime.now(TZ).date().isoformat(),
            "video": video,
            "site_image": "site.jpg",
            "ending": "loop_short",    # 最後に冒頭の場面へ戻り、ひとことを読み上げない短い版(2026-11-21〜。stats.md で比べる)
            "seconds": round(seconds, 2),
            "format": "game" if place.get("game") else "place",   # stats.md で、ゲームの舞台の回とふつうの回を比べる
            **({"game": place["game"]} if place.get("game") else {}),
            "site": site_fields(place, labels, correct),
            **youtube_meta(place, labels, correct, number),
        }
        (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
        print(f"meta: {out / 'meta.json'}")


if __name__ == "__main__":
    main()
