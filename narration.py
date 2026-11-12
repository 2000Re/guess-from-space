"""読み上げ(英語)と効果音。Painted When?(2000Re/painted-when)の narration.py から、音声合成と効果音の部分を移したもの。

音声合成:
  google … Google Cloud Text-to-Speech。API キーは環境変数 GOOGLE_TTS_API_KEY(GitHub Actions など)か、
           Claude Code のクラウド環境の「Network secrets」(texttospeech.googleapis.com への通信に
           X-Goog-Api-Key ヘッダーを自動で付ける。この場合キーはプログラムからは見えない)で渡す。
           声は GFS_TTS_VOICE(既定 en-US-Chirp3-HD-Charon)、速さは GFS_TTS_RATE(既定 1.1)で変えられる
  dummy  … 通信なし。文の長さから見積もった長さの仮の音(タイミング確認用)
"""
import base64
import io
import json
import os
import urllib.error
import urllib.request
import wave

import numpy as np

SR = 48000
DEFAULT_VOICE = "en-US-Chirp3-HD-Charon"
DEFAULT_RATE = 1.1          # 少し速めに読ませる(Shorts のテンポ)
TTS_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"


# ---------------------------------------------------------------- 音声合成


def read_wav(raw):
    if raw[:4] != b"RIFF":    # ヘッダーなしの 16bit モノラル PCM(要求した SR)
        return np.frombuffer(raw[: len(raw) // 2 * 2], dtype=np.int16).astype(np.float32) / 32768
    with wave.open(io.BytesIO(raw)) as w:
        sr, ch, n = w.getframerate(), w.getnchannels(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    if sr != SR:
        t = np.arange(int(len(x) * SR / sr)) / SR
        x = np.interp(t, np.arange(len(x)) / sr, x).astype(np.float32)
    return x


def trim(x, thresh=0.01):
    """前後の無音を削る(場面の時刻を声に合わせるため)。"""
    idx = np.nonzero(np.abs(x) > thresh)[0]
    if len(idx) == 0:
        return x
    a, b = max(0, idx[0] - int(0.02 * SR)), min(len(x), idx[-1] + int(0.06 * SR))
    return x[a:b]


class GoogleTTS:
    name = "google"

    def __init__(self, api_key=None, voice=None, rate=None):
        # キーがなければヘッダーを付けずに送る(途中の proxy がキーを付ける環境のため)
        self.key = api_key or os.environ.get("GOOGLE_TTS_API_KEY")
        self.voice = voice or os.environ.get("GFS_TTS_VOICE") or DEFAULT_VOICE
        self.rate = rate or float(os.environ.get("GFS_TTS_RATE") or DEFAULT_RATE)

    def __call__(self, text):
        body = {
            "input": {"text": text},
            "voice": {"languageCode": "-".join(self.voice.split("-")[:2]), "name": self.voice},
            "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": SR, "speakingRate": self.rate},
        }
        # キーは URL ではなくヘッダーで渡す(ログに残りにくい)
        headers = {"Content-Type": "application/json"}
        if self.key:
            headers["X-Goog-Api-Key"] = self.key
        req = urllib.request.Request(TTS_URL, data=json.dumps(body).encode(), method="POST", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read())
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            hint = "" if self.key else "(GOOGLE_TTS_API_KEY がなく、キーを付けずに送りました)"
            raise RuntimeError(f"Text-to-Speech が {e.code} を返しました{hint}: {detail}") from None
        return trim(read_wav(base64.b64decode(data["audioContent"])))


class DummyTTS:
    """通信なしの仮の声。1語あたり約0.32秒の、音節ごとに区切れた柔らかい音。"""
    name = "dummy"

    def __call__(self, text):
        words = text.replace("?", " ").replace("!", " ").replace(",", " ").split()
        syll = sum(max(1, len(w) // 3) for w in words)
        dur = 0.15 + 0.32 * len(words) + 0.03 * syll
        n = int(dur * SR)
        t = np.arange(n) / SR
        env = 0.5 - 0.5 * np.cos(2 * np.pi * np.clip(t * syll / dur, 0, None))
        f0 = 170 + 25 * np.sin(2 * np.pi * 0.8 * t)
        x = (np.sin(2 * np.pi * np.cumsum(f0) / SR) * env * 0.25).astype(np.float32)
        fade = np.minimum(1, np.minimum(t / 0.02, (dur - t) / 0.05))
        return x * fade


def make_tts(name):
    return {"google": GoogleTTS, "dummy": DummyTTS}[name]()


# ---------------------------------------------------------------- 効果音


def _env(n, attack, decay):
    t = np.arange(n) / SR
    return np.minimum(1, t / attack) * np.exp(-t / decay)


def sfx_pop():
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    f = 900 * np.exp(-t * 18) + 500
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.002, 0.03) * 0.5).astype(np.float32)


def sfx_tick():
    n = int(0.05 * SR)
    noise = np.random.default_rng(0).standard_normal(n)
    noise = np.convolve(noise, [1, -1], mode="same")      # 高い音だけ残す
    return (noise * _env(n, 0.0005, 0.006) * 0.25).astype(np.float32)


def sfx_ding():
    n = int(1.4 * SR)
    t = np.arange(n) / SR
    x = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / d)
            for f, a, d in [(1046.5, 0.5, 0.6), (1568.0, 0.3, 0.45), (2093.0, 0.15, 0.3), (2637.0, 0.08, 0.2)])
    return (x * np.minimum(1, t / 0.003) * 0.6).astype(np.float32)


def sfx_whoosh():
    """冒頭の「シュッ」。高い方へ抜けるノイズ。"""
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    noise = np.random.default_rng(1).standard_normal(n)
    # 時間とともに明るくなるよう、なめらかにする幅を狭めていく
    out = np.empty(n)
    acc, alpha0 = 0.0, 0.02
    for i in range(n):
        a = alpha0 + 0.5 * (t[i] / t[-1]) ** 2
        acc += a * (noise[i] - acc)
        out[i] = noise[i] - acc
    env = np.sin(np.pi * np.clip(t / 0.35, 0, 1)) ** 1.5
    return (out * env * 0.35).astype(np.float32)


def write_wav(path, stereo):
    pcm = (np.clip(stereo, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
