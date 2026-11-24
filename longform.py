"""通常動画(横 1920x1080)「Guess From Space Challenge」を作る。週1本、12問。

Shorts と同じ衛星画像(Sentinel-2 cloudless 2016、CC BY 4.0)・場所のリスト・声を使い、横長の画面用に組み直したもの。
右に衛星写真、左の帯に問題・3択・残り時間を出す。

  0:00  導入  「Welcome to the Guess From Space Challenge! 12 places, 5 seconds each. Keep score!」
  各問  「Round N. Where on Earth is this?」→ 3択を読む → 5秒(少しずつ引いてヒントが増える)→ 一気に引いて答え
  最後  「How many did you get right?」と点数の目安

場所・答え・ひとことは places.py のものだけを使う(手で書き足した答えはない)。
チャプターは「Place 1」などにして、答えは書かない(答えは説明欄の下の方にまとめる)。
サムネイル(1280x720)を3種類作る(a は投稿のときに設定、b・c は YouTube Studio の「テストと比較」用)。

使い方:
  python longform.py --tts dummy --rounds 2 --out out_long            試し(仮の声・2問だけ)
  python longform.py --history longform_history.json --out out_long   本番(meta.json も書く)
  python longform.py --upload --dir out_long --privacy unlisted       投稿して longform_history.json に記録
"""
import argparse
import json
import math
import random
import subprocess
import sys
import wave
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
from PIL import Image, ImageDraw

import make_video as V
import narration as N
import places as P
import tiles

ROOT = Path(__file__).resolve().parent
HISTORY = ROOT / "longform_history.json"
SHORTS_HISTORY = ROOT / "upload_history.json"
TZ = ZoneInfo("Asia/Tokyo")
W, H, FPS = 1920, 1080, 30
SR = N.SR
ROUNDS = 12
THINK = 5.0                     # 考える時間(秒)
MIN_CHAPTER = 11.0              # YouTube のチャプターは1つ10秒以上(1つでも短いとチャプター全体が出ない)
PANEL_W = 620                   # 左の文字の帯
AW, AH = W - PANEL_W, H         # 右の衛星写真の範囲
NAVY = (8, 12, 24)
GOLD, WHITE = V.GOLD, V.WHITE
CHANNEL = "https://www.youtube.com/@guess-from-space"
TITLE = "GUESS FROM SPACE CHALLENGE"
RECENT_DAYS = 30                # この日数のうちに Shorts に出た場所は使わない(足りなければ使う)
NATURE_N = 4                    # 12問のうち、自然(山・湖・火山など)の問題の数
MAX_GREY = 1                    # 灰色の街並みばかりの街(places.GREY_CITY)は1問まで
MAX_GAME = 1                    # ゲームの舞台(places.GAME_PLACES)は1問まで


# ---------------------------------------------------------------- 衛星写真(横長)


class Earth(V.Earth):
    """make_video.Earth の横長版(AW×AH の範囲に描く)。"""

    def level_for(self, km):
        f = tiles.MAXZ - math.log2(max(self.px14(km), 1) / (AW / 2))
        return int(min(tiles.MAXZ, math.floor(f)))

    def mosaic(self, z):
        if z not in self.mosaics:
            self.mosaics[z] = tiles.mosaic(self.lon, self.lat, z, AW, AH)
        return self.mosaics[z]

    def render(self, km, size=(AW, AH)):
        z = self.level_for(km)
        m = self.mosaic(z)
        wl = self.px14(km) / 2 ** (tiles.MAXZ - z)
        hl = wl * AH / AW
        cx, cy = m.width / 2, m.height / 2
        return m.resize(size, Image.BICUBIC, box=(cx - wl / 2, cy - hl / 2, cx + wl / 2, cy + hl / 2))


# ---------------------------------------------------------------- 画面の部品


def text(lines, size, fill, bold=True, width=PANEL_W, shadow=200, spacing=1.15):
    return V.text_layer(lines, V.font(V.SANS_BOLD if bold else V.SANS, size), fill, width=width, spacing=spacing,
                        shadow=shadow)


def wrap(s, size, max_w, bold=True, max_lines=3):
    fnt = V.font(V.SANS_BOLD if bold else V.SANS, size)
    words, lines, cur = s.split(), [], ""
    for w in words:
        t = f"{cur} {w}".strip()
        if fnt.getlength(t) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines[:max_lines]


CREDIT = None


def chrome(img, round_no=None, total=ROUNDS):
    """左の帯・回の番号・進み具合・出典(CC BY 4.0 の条件。常に出す)。"""
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, PANEL_W, H], fill=NAVY + (255,))
    d.text((PANEL_W / 2, 64), TITLE, font=V.font(V.SANS_BOLD, 28), fill=GOLD + (255,), anchor="mm")
    if round_no:
        d.text((PANEL_W / 2, 118), f"PLACE {round_no} / {total}", font=V.font(V.SANS_BOLD, 40),
               fill=WHITE + (255,), anchor="mm")
        x0 = PANEL_W / 2 - (total - 1) * 22 / 2
        for k in range(total):
            c = GOLD if k < round_no else (70, 80, 100)
            d.ellipse([x0 + k * 22 - 6, 156 - 6, x0 + k * 22 + 6, 156 + 6], fill=c + (255,))
    img.alpha_composite(CREDIT, (PANEL_W, H - 62))


def countdown(img, t, start, end, y=760):
    if not (start <= t < end + 0.3):
        return
    a = 1 - V.ease((t - end) / 0.3)
    left = max(0.0, end - t)
    d = ImageDraw.Draw(img)
    n = math.ceil(left) if left > 0 else 0
    if n:
        d.text((PANEL_W / 2, y), str(n), font=V.font(V.SANS_BOLD, 130), fill=GOLD + (int(255 * a),), anchor="mm",
               stroke_width=5, stroke_fill=NAVY + (255,))
    x0, x1, yb = 90, PANEL_W - 90, y + 100
    d.rounded_rectangle([x0, yb, x1, yb + 10], radius=5, fill=(255, 255, 255, int(60 * a)))
    frac = left / (end - start)
    if frac > 0:
        col = GOLD if frac > 0.3 else (235, 110, 90)
        d.rounded_rectangle([x0, yb, x0 + max(10, int((x1 - x0) * frac)), yb + 10], radius=5, fill=col + (int(255 * a),))


def ring(img, t, reveal, a):
    """答えの印(中心に広がる輪)。make_video と同じ描き方を、右の範囲の中心に。"""
    if a <= 0:
        return
    cx, cy = PANEL_W + AW / 2, AH / 2
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    pulse = (t - reveal) % 1.2 / 1.2
    for k, rad in enumerate((42, 42 + 60 * pulse)):
        alpha = int(255 * a * (1 if k == 0 else 1 - pulse))
        box = [cx - rad, cy - rad, cx + rad, cy + rad]
        d.ellipse([box[0] - 3, box[1] - 3, box[2] + 3, box[3] + 3], outline=(10, 14, 24, alpha * 2 // 3), width=12)
        d.ellipse(box, outline=GOLD + (alpha,), width=6)
    img.alpha_composite(layer)


def answer_box(img, place, a, y=700):
    if a <= 0:
        return
    big = text(wrap(place["name"], 54, PANEL_W - 110, max_lines=2), 54, GOLD + (255,), shadow=230)
    small = text(wrap(f"{place['country']} · {place['note']}", 28, PANEL_W - 110, bold=False, max_lines=3), 28,
                 (225, 230, 240, 255), bold=False, shadow=200)
    hgt = big.height + small.height + 46
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle([40, y, PANEL_W - 40, y + hgt], radius=22,
                                            fill=(20, 28, 48, int(240 * a)), outline=GOLD + (int(200 * a),), width=3)
    img.alpha_composite(layer)
    img.alpha_composite(V.with_alpha(big, a), (0, y + 16))
    img.alpha_composite(V.with_alpha(small, a), (0, y + 16 + big.height + 4))


# ---------------------------------------------------------------- 1問


def round_place(place, no, total, tts, rng):
    labels, correct = V.choices_for(place, rng)
    start_km = place["start"]
    end_km = place.get("end", P.END_KM)
    hint_km = start_km * 1.7                       # 考えている間に、ここまで少しずつ引く
    earth = Earth(place["lon"], place["lat"])
    earth.prefetch(start_km, end_km)

    lines = {
        "q": f"Round {no}. Where on Earth is this?",
        "c": f"Is it {labels[0]}, {labels[1]}, or {labels[2]}?",
        "ans": f"It's {P.spoken_name(place)}, {P.where(place)}!",
    }
    clips, dur = _say_all(tts, lines)
    at = {"q": 0.3}
    at["c"] = at["q"] + dur["q"] + 0.25
    think = (at["c"] + dur["c"] + 0.2, at["c"] + dur["c"] + 0.2 + THINK)
    reveal = think[1] + 0.1
    zoom = (reveal, reveal + 1.6)
    at["ans"] = reveal + 0.2
    end = max(MIN_CHAPTER, at["ans"] + dur["ans"] + 2.6)     # 答えのあと、ひとことを読める時間
    effects = [(N.sfx_pop(), at["c"])]
    effects += [(N.sfx_tick(), think[0] + k) for k in range(int(THINK))]
    effects += [(N.sfx_whoosh(), zoom[0]), (N.sfx_ding(), reveal)]

    q = text(["Where on Earth", "is this?"], 50, WHITE + (255,), spacing=1.08)
    pills = [V.pill(lb, 440, (16, 18, 22, 230), WHITE, (255, 255, 255, 130)) for lb in labels]
    right = V.pill(labels[correct], 440, GOLD + (255,), (25, 20, 10), None)

    def km_at(t):
        if t < think[1]:
            e = V.ease(t / think[1])
            return math.exp(math.log(start_km) + (math.log(hint_km) - math.log(start_km)) * e)
        e = V.ease((t - zoom[0]) / (zoom[1] - zoom[0]))
        return math.exp(math.log(hint_km) + (math.log(end_km) - math.log(hint_km)) * e)

    def frame(t):
        img = Image.new("RGBA", (W, H), NAVY + (255,))
        img.paste(earth.render(km_at(t)), (PANEL_W, 0))
        r = V.ease((t - reveal) / 0.3)
        ring(img, t, reveal, r)
        chrome(img, no, total)
        img.alpha_composite(q, (0, 210))
        for k, p in enumerate(pills):
            px, py = (PANEL_W - p.width) // 2, 360 + k * 100
            a_in = V.ease((t - at["c"] - 0.3 * k) / 0.3)
            if k == correct and r > 0:
                img.alpha_composite(V.with_alpha(p, 1 - r), (px, py))
                img.alpha_composite(V.with_alpha(right, r), (px, py))
            elif a_in > 0:
                img.alpha_composite(V.with_alpha(p, a_in * (1 - 0.7 * r)), (px, py))
        countdown(img, t, think[0], think[1], y=760)
        answer_box(img, place, V.ease((t - at["ans"] - 0.2) / 0.5), y=700)
        return img

    return dict(clips=clips, at=at, effects=effects, end=end, frame=frame, key=P.key(place), place=place,
                thumb_t=(think[0] + think[1]) / 2,
                answer=f"{place['name']} ({place['country']}) — {place['note'].rstrip('.')}.")


def _say_all(tts, lines):
    clips = {k: tts(t) for k, t in lines.items()}
    return clips, {k: len(v) / SR for k, v in clips.items()}


# ---------------------------------------------------------------- 導入と最後


def world():
    e = Earth(15.0, 25.0)
    e.prefetch(16000, 16000)
    return e.render(16000)


def intro(tts, total, bg):
    lines = {"hi": f"Welcome to the Guess From Space Challenge! {total} famous places, seen from space. "
                   f"You get {int(THINK)} seconds each. Keep score, and let's see how many you can name!"}
    clips, dur = _say_all(tts, lines)
    at = {"hi": 0.4}
    end = max(MIN_CHAPTER, at["hi"] + dur["hi"] + 0.8)
    t1 = text(["GUESS FROM", "SPACE", "CHALLENGE"], 64, GOLD + (255,), spacing=1.05)
    t2 = text([f"{total} places · {int(THINK)} seconds each"], 34, WHITE + (255,), bold=False)
    t3 = text(["Keep score!"], 44, WHITE + (255,))

    def frame(t):
        img = Image.new("RGBA", (W, H), NAVY + (255,))
        img.paste(bg, (PANEL_W, 0))
        chrome(img)
        img.alpha_composite(V.with_alpha(t1, V.ease(t / 0.6)), (0, 280))
        img.alpha_composite(V.with_alpha(t2, V.ease((t - 0.8) / 0.5)), (0, 560))
        img.alpha_composite(V.with_alpha(t3, V.ease((t - 1.6) / 0.5)), (0, 660))
        return img
    return dict(clips=clips, at=at, effects=[(N.sfx_whoosh(), 0.1)], end=end, frame=frame)


def outro(tts, total, bg):
    lines = {"how": "How many did you get right? Tell me your score in the comments! "
                    "And follow for a new place from space every day."}
    clips, dur = _say_all(tts, lines)
    at = {"how": 0.4}
    end = max(MIN_CHAPTER, at["how"] + dur["how"] + 2.5)
    t1 = text(["How many did", "you get right?"], 58, WHITE + (255,), spacing=1.1)
    hi, mid = math.ceil(total * 0.8), math.ceil(total * 0.5)
    tiers = text([f"{hi}–{total}: Satellite expert", f"{mid}–{hi - 1}: World traveler", f"0–{mid - 1}: Space tourist"],
                 36, GOLD + (255,), spacing=1.5)
    t3 = text(["Tell me in the comments!"], 32, WHITE + (255,), bold=False)

    def frame(t):
        img = Image.new("RGBA", (W, H), NAVY + (255,))
        img.paste(bg, (PANEL_W, 0))
        chrome(img)
        img.alpha_composite(V.with_alpha(t1, V.ease(t / 0.5)), (0, 260))
        img.alpha_composite(V.with_alpha(tiers, V.ease((t - 0.8) / 0.5)), (0, 470))
        img.alpha_composite(V.with_alpha(t3, V.ease((t - 1.6) / 0.5)), (0, 760))
        return img
    return dict(clips=clips, at=at, effects=[(N.sfx_ding(), 0.2)], end=end, frame=frame)


# ---------------------------------------------------------------- 場所の選び方


def recent_short_keys(shorts_history, now=None, days=RECENT_DAYS):
    now = now or datetime.now(timezone.utc)
    out = set()
    for h in shorts_history:
        try:
            if (now - datetime.fromisoformat(h["uploaded_at"])).total_seconds() <= days * 86400:
                out.add(h["key"])
        except (KeyError, ValueError):
            continue
    return out


def base_key(p):
    k = P.key(p)
    return k[len("game-"):] if k.startswith("game-") else k


def pick(n, shorts_history, long_history, rng, now=None):
    """n か所を選ぶ。次のものは避ける:
    - 過去の通常動画で出した場所
    - 直近 RECENT_DAYS 日の Shorts に出た場所(足りなければ、この条件をゆるめる)
    - この動画の中で、同じ国・同じ場所(ゲームの舞台と元の場所)
    自然は NATURE_N 問、灰色の街並みの街は MAX_GREY 問まで、ゲームの舞台は MAX_GAME 問まで。並びは自然と街・海岸を混ぜる。"""
    used = {k for h in long_history for k in h.get("keys", [])}
    recent = recent_short_keys(shorts_history, now)
    recent_base = {k[len("game-"):] if k.startswith("game-") else k for k in recent}
    cands = [p for p in P.ALL_PLACES if P.key(p) not in used]
    rng.shuffle(cands)
    cands.sort(key=lambda p: base_key(p) in recent_base)        # 最近 Shorts に出ていない場所を先に
    chosen, countries, bases = [], set(), set()
    n_nature = min(NATURE_N, n // 3)
    counts = {"nature": 0, "grey": 0, "game": 0, "other": 0}
    limits = {"nature": n_nature, "grey": MAX_GREY, "game": MAX_GAME, "other": n}

    def kind(p):
        k = P.key(p)
        return "game" if p.get("game") else "nature" if k in P.NATURE else "grey" if k in P.GREY_CITY else "other"
    for p in cands:
        if len(chosen) >= n:
            break
        kd = kind(p)
        if p["country"] in countries or base_key(p) in bases or counts[kd] >= limits[kd]:
            continue
        if kd == "other" and counts["other"] >= n - n_nature - 1 and counts["nature"] < n_nature:
            continue                                            # 自然の問題の分を空けておく
        chosen.append(p)
        countries.add(p["country"])
        bases.add(base_key(p))
        counts[kd] += 1
    if len(chosen) < n:
        raise SystemExit(f"場所が足りません({len(chosen)}/{n})。places.py に場所を足してください")
    relaxed = sum(1 for p in chosen if base_key(p) in recent_base)
    print(f"直近{RECENT_DAYS}日の Shorts に出た場所: {len(recent)}"
          + (f"(候補が足りず、{relaxed}問はこの条件をゆるめた)" if relaxed else ""), flush=True)
    # 並び: 自然と、それ以外を交互に近くなるように
    nat = [p for p in chosen if kind(p) == "nature"]
    oth = [p for p in chosen if kind(p) != "nature"]
    order, step = [], max(1, round(len(chosen) / max(1, len(nat))))
    for i in range(len(chosen)):
        src = nat if (i % step == step - 1 and nat) or not oth else oth
        order.append(src.pop(0))
    return order


# ---------------------------------------------------------------- 組み立て


def mix(segments):
    total = sum(s["end"] for s in segments)
    n = int(math.ceil(total * SR)) + SR
    voice, fx = np.zeros(n, np.float32), np.zeros(n, np.float32)

    def put(buf, x, t):
        i = int(t * SR)
        x = x[: max(0, n - i)]
        buf[i:i + len(x)] += x
    t0 = 0.0
    for s in segments:
        for k, x in s["clips"].items():
            put(voice, x, t0 + s["at"][k])
        for x, t in s["effects"]:
            put(fx, x, t0 + t)
        t0 += s["end"]
    m = voice / max(1e-6, float(np.abs(voice).max())) * 0.8 + fx * 0.35
    m /= max(1.0, float(np.abs(m).max()) / 0.95)
    return m, total


def write_wav(path, m):
    pcm = (np.clip(np.stack([m, m], 1), -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def starts_of(segments):
    out, t0 = [], 0.0
    for s in segments:
        out.append(t0)
        t0 += s["end"]
    return out


def render(mp4, wav, segments, total):
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", str(wav), "-map", "0:v", "-map", "1:a", "-shortest",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(mp4)], stdin=subprocess.PIPE)
    starts = starts_of(segments)
    try:
        k = 0
        for f in range(int(round(total * FPS))):
            t = f / FPS
            while k + 1 < len(segments) and t >= starts[k + 1]:
                k += 1
            p.stdin.write(segments[k]["frame"](t - starts[k]).convert("RGB").tobytes())
            if f % (FPS * 30) == 0:
                print(f"  {t:.0f}/{total:.0f} 秒", flush=True)
    finally:
        p.stdin.close()
        if p.wait() != 0:
            raise RuntimeError("ffmpeg が失敗しました")


def stamp(sec):
    sec = int(sec)
    return f"{sec // 60}:{sec % 60:02d}"


def check_chapters(starts, total):
    """チャプターの決まり(0:00 から始まる・3つ以上・どれも10秒以上)を満たすか。満たさなければ止める。"""
    ends = starts[1:] + [total]
    short = [(stamp(a), round(b - a, 1)) for a, b in zip(starts, ends) if b - a < 10]
    if len(starts) < 3 or short:
        raise SystemExit(f"チャプターが YouTube の決まりを満たしません(10秒未満: {short})")


def thumbnail(seg, number, total, path, style="a"):
    """サムネイル(1280x720)。問題の途中のコマ(答えはまだ)に、大きな文字を重ねる。
    a = 題名(投稿のときに設定)/ b = 「Where on Earth is this?」/ c = 「Can you get 12/12?」"""
    img = seg["frame"](seg["thumb_t"]).convert("RGBA")
    ImageDraw.Draw(img).rectangle([0, 0, PANEL_W, H], fill=NAVY + (255,))
    if style == "b":
        img.alpha_composite(text(["Where on", "Earth is", "this?"], 96, WHITE + (255,), spacing=1.0, shadow=255), (0, 170))
        img.alpha_composite(text([f"Guess From Space #{number}"], 40, GOLD + (255,), shadow=255), (0, 760))
    elif style == "c":
        img.alpha_composite(text(["Can you get", f"{total}/{total}?"], 100, GOLD + (255,), spacing=1.0, shadow=255),
                            (0, 220))
        img.alpha_composite(text(["Famous places", "seen from space"], 54, WHITE + (255,), spacing=1.08, shadow=255),
                            (0, 600))
    else:
        img.alpha_composite(text(["GUESS FROM", "SPACE"], 82, GOLD + (255,), spacing=1.0, shadow=255), (0, 150))
        img.alpha_composite(text([f"#{number} · {total} places"], 52, WHITE + (255,), shadow=255), (0, 430))
        img.alpha_composite(text(["Can you name", "them all?"], 64, WHITE + (255,), spacing=1.05, shadow=255), (0, 640))
    # 下の出典の行は小さくて読めないので、16:9 のまま下を切る(サムネイルは動画ではないので出典の行は要らない。
    # 説明欄には必ず書く)
    img.convert("RGB").crop((0, 0, W - 112, H - 63)).resize((1280, 720), Image.LANCZOS).save(path, quality=90)


def description(number, rounds, starts, total):
    lines = [
        f"Guess From Space Challenge #{number}: {len(rounds)} famous places seen in satellite images. "
        f"You get {int(THINK)} seconds each. Keep score and tell me how many you got right! 🛰️",
        "",
        "Chapters:",
        f"{stamp(starts[0])} Intro",
    ]
    for i, st in enumerate(starts[1:-1], 1):
        lines.append(f"{stamp(st)} Place {i}")
    lines.append(f"{stamp(starts[-1])} Your score")
    lines += ["", "⬇️ Answers below (spoilers!) ⬇️", ".", ".", "."]
    lines += [f"{i}. {r['answer']}" for i, r in enumerate(rounds, 1)]
    lines += ["", f"A new place from space every day: {CHANNEL}", f"Website: {V.SITE}/",
              "", "Satellite images: " + tiles.ATTRIBUTION, "License: https://creativecommons.org/licenses/by/4.0/",
              "", "#geography #satellite #geographyquiz #earthfromspace"]
    return "\n".join(lines)


def build(args):
    global CREDIT
    CREDIT = text(tiles.ATTRIBUTION_LINES, 20, (210, 215, 225, 235), bold=False, width=AW, shadow=255, spacing=1.1)
    CREDIT.alpha_composite(CREDIT.copy())
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    hp = Path(args.history) if args.history else None
    long_history = json.loads(hp.read_text().strip() or "[]") if hp and hp.exists() else []
    shorts = json.loads(SHORTS_HISTORY.read_text()) if SHORTS_HISTORY.exists() else []
    number = max([h["number"] for h in long_history], default=0) + 1
    rng = random.Random(f"long:{number}:{args.seed or ''}")
    n = args.rounds or ROUNDS
    chosen = pick(n, shorts, long_history, rng)
    tts = N.make_tts(args.tts)
    print(f"#{number}: " + ", ".join(P.key(p) for p in chosen), flush=True)

    bg = world()
    rounds = []
    for i, p in enumerate(chosen, 1):
        print(f"  問題 {i}: {p['name']}  tiles {tiles.stats}", flush=True)
        rounds.append(round_place(p, i, n, tts, rng))
    segments = [intro(tts, n, bg)] + rounds + [outro(tts, n, bg)]
    m, total = mix(segments)
    starts = starts_of(segments)
    check_chapters(starts, total)                  # 書き出す前に確かめる
    wav = out / "audio.wav"
    write_wav(wav, m)
    print(f"動画を書き出しています({total:.0f} 秒)", flush=True)
    render(out / "video.mp4", wav, segments, total)
    wav.unlink()
    thumb_seg = next((r for r in rounds if P.key(r["place"]) not in P.NATURE | P.GREY_CITY), rounds[0])
    thumbnail(thumb_seg, number, n, out / "thumbnail.jpg")
    for style in ("b", "c"):                       # A/B テスト用(Actions の Artifacts からダウンロードする)
        thumbnail(thumb_seg, number, n, out / f"thumbnail_{style}.jpg", style)

    meta = {
        "number": number,
        "keys": [r["key"] for r in rounds],
        "date": datetime.now(TZ).date().isoformat(),
        "video": "video.mp4",
        "thumbnail": "thumbnail.jpg",
        "seconds": round(total, 1),
        "title": f"Guess From Space Challenge #{number}: Can You Name These {n} Places From Space? 🛰️"[:100],
        "description": V._yt(description(number, rounds, starts, total))[:4900],
        "tags": ["geography quiz", "satellite", "satellite images", "guess the place", "earth from space",
                 "geography", "quiz", "world heritage"],
    }
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
    print(f"完了: {out / 'video.mp4'}({total:.0f} 秒)  tiles {tiles.stats}")
    print(meta["description"])


# ---------------------------------------------------------------- 投稿


THUMB_URL = "https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={}"
PUBLISH_WEEKDAY = 6             # 予約投稿の曜日(月曜が 0)。日曜
PUBLISH_TIME = (19, 13)            # 予約投稿の時刻(日本時間)


def scheduled_publish(now=None):
    """定期実行で作った回を公開する時刻(UTC の RFC3339)。GitHub の定期実行は数時間遅れることがあるので、
    早めに作って非公開で上げ、この時刻に YouTube が公開する(publishAt)。もう間に合わなければ None(すぐ公開する)。"""
    from datetime import timedelta
    now = now or datetime.now(TZ)
    if 1 <= (now.weekday() - PUBLISH_WEEKDAY) % 7 <= 2:      # 定期実行が日付をまたいで遅れた: 来週にせず、すぐ公開
        return None
    day = now.date() + timedelta(days=(PUBLISH_WEEKDAY - now.weekday()) % 7)
    target = datetime(day.year, day.month, day.day, *PUBLISH_TIME, tzinfo=TZ)
    if now > target - timedelta(minutes=10):
        return None
    return target.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def upload(args):
    import youtube_upload as Y
    out = Path(args.dir)
    meta = json.loads((out / "meta.json").read_text())
    hist_path = Path(args.history)
    history = json.loads(hist_path.read_text().strip() or "[]") if hist_path.exists() else []
    if any(h["number"] == meta["number"] for h in history):
        raise SystemExit(f"投稿済みの回です: #{meta['number']}")
    token = Y.connect()
    publish_at = scheduled_publish() if args.schedule else None
    if args.schedule and not publish_at:
        print("予約の時刻を過ぎたので、すぐ公開します")
    res = Y.upload(token, out / meta["video"], meta, args.privacy, publish_at)
    vid = res["id"]
    privacy = "public" if publish_at else res.get("status", {}).get("privacyStatus", args.privacy)
    if publish_at:
        print(f"予約投稿: {publish_at} に公開")
    print(f"uploaded: https://youtu.be/{vid} ({privacy})")
    Y.set_output("video_id", vid)
    thumb = out / meta.get("thumbnail", "thumbnail.jpg")
    if thumb.exists():
        try:
            Y.request(THUMB_URL.format(vid), data=thumb.read_bytes(), method="POST",
                      headers={"Authorization": f"Bearer {token}", "Content-Type": "image/jpeg"})
            print("thumbnail ok")
        except Exception as e:
            detail = e.read().decode(errors="replace")[:300] if hasattr(e, "read") else str(e)
            print(f"警告: サムネイルを設定できませんでした(YouTube Studio で設定してください): {detail}", file=sys.stderr)
    history.append({
        "number": meta["number"], "keys": meta["keys"], "date": meta["date"], "title": meta["title"],
        "seconds": meta["seconds"], "video_id": vid, "privacy": privacy, "publish_at": publish_at,
        "uploaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    hist_path.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n")
    import playlists                       # 「Guess From Space Challenge」の再生リストへ(失敗しても投稿は止めない)
    playlists.add_after_upload(token, history[-1])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--history", default=str(HISTORY), help="通常動画の投稿記録")
    ap.add_argument("--tts", choices=["google", "dummy"], default="google")
    ap.add_argument("--rounds", type=int, help=f"問題の数(既定 {ROUNDS}。試しに少なくするとき)")
    ap.add_argument("--seed", help="場所選びの乱数の種に足す文字(試し用)")
    ap.add_argument("--out", default="out_long")
    ap.add_argument("--upload", action="store_true", help="--dir の動画を投稿して記録する")
    ap.add_argument("--dir", default="out_long")
    ap.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    ap.add_argument("--schedule", action="store_true", help="予約投稿にする(定期実行。scheduled_publish の時刻に公開)")
    args = ap.parse_args()
    if args.upload:
        upload(args)
    else:
        build(args)


if __name__ == "__main__":
    main()
