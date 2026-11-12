# Guess From Space

衛星写真の場所当て3択クイズを、YouTube Shorts(@guess-from-space)に自動投稿するボット。
仕組みは姉妹チャンネル Painted When?(2000Re/painted-when)と同じで、必要なファイルをコピーして単独で動くようにしてある。

- サイト: https://2000re.github.io/guess-from-space/ (GitHub Pages、`docs/`)
- 動画の中の問い: 「Where on Earth is this?」

## 動画の構成(縦 1080x1920、15〜18秒)

1. 0秒: 衛星写真を寄りで画面いっぱいに。最初のコマから問い・3択(縦に3つ)・残り時間のバー。0秒に効果音、すぐ読み上げ
2. 「Is it A? B? Or C?」に合わせて選択肢が弾み、その間に広い範囲(既定 60km)まで引いていく
3. 「Lock in your answer!」→ 約2秒 → チャイムで正解が金色に。中心に輪の印、「It's Venice, in Italy!」、
   画面上部に場所名・国・ひとこと
4. その場所へもう一度寄り、見出しが「How did you do?」に変わる
- 画面下に衛星画像の出典(ライセンスの条件)を常に表示

## ファイル

| ファイル | 役割 |
|---|---|
| `make_video.py` | 動画を作る。投稿記録にない場所を選び、`out/` に動画・`meta.json`(タイトル・説明文)・サイト用画像を書く |
| `places.py` | クイズに出す場所のリスト(名前・国・経度緯度・寄りと引きの広さ・外れの選択肢・ひとこと) |
| `tiles.py` | 衛星画像タイルの取得とキャッシュ(`tile_cache/`)、出典の文言 |
| `narration.py` | 読み上げ(Google Cloud Text-to-Speech)と効果音 |
| `youtube_upload.py` | YouTube へのアップロード(標準ライブラリのみ)。`upload_history.json` に記録し、サイトにページを足す |
| `posted_today.py` | 定期実行で今投稿してよいか(1日の上限 `MAX_PER_DAY`=2本、間隔 `MIN_GAP_HOURS`=4時間) |
| `site_gen.py` | サイトの一覧ページ・回ごとのページ・sitemap を作る |
| `get_youtube_refresh_token.py` | リフレッシュトークンの取得(ローカル PC で一度だけ) |
| `tools/check_places.py` | 場所のリストの確認用一覧画像(寄りと引きを並べる) |
| `tools/make_branding.py` | チャンネルのアイコン・バナー、サイトの画像 |
| `branding/` | アイコン(800x800)・バナー(2560x1440)・チャンネルの説明文 |
| `.github/workflows/post.yml` | 生成 → 投稿 → 記録のコミット。失敗時は Issue |

## 衛星画像とライセンス

- EOX「Sentinel-2 cloudless」**2016年版**(WMTS の層 `s2cloudless_3857`、Web メルカトル、最大ズーム 14 ≒ 10m/画素)
- ライセンス: **CC BY 4.0**。出典「Sentinel-2 cloudless 2016 by EOX IT Services GmbH (https://s2maps.eu) · Contains modified
  Copernicus Sentinel data 2016」を、動画の画面・説明欄・サイト・チャンネルの説明文に書いている
- 2017年以降の層はライセンスが違うので使わない(`tiles.py` は 2016 年の層しか取りに行かない)
- 画像は2016年の状態。それ以降にできたものは映らない
- 配信元への負荷: タイルは `tile_cache/` に保存して二度取りに行かない。通信は1本ずつ、0.1秒以上あける。
  1本の動画で約150〜300枚(1〜3分)。GitHub Actions では、投稿をやり直すときに前回のタイルを使う(`actions/cache`)

## 場所のリスト(`places.py`)

今は72か所。数km以上の大きな形で見分けられる世界遺産・有名観光地(島・火山・湖・海岸線・人工島・街の形など)。

- 入れないもの: 建物単位の名所(10m/画素では小さくてぼやける)、雪や雲で白くなる場所(エベレスト、ウユニ塩湖、
  ペリト・モレノ氷河、ロライマ山は試して外した)、2016年以降にできたもの
- 外れの選択肢: 同じ地域や似た地形の実在の場所
- ひとこと(`note`)は事実だけ。「UNESCO World Heritage Site」と書くのは実際に登録されている場所だけ
- 1日2本で約5週間分。使い切ると、いちばん前に出した場所から繰り返し、ログに警告を出す。早めに足すこと

場所を足したら、中心と広さを画像で確かめる:

```bash
python tools/check_places.py --only venice,mount-fuji
```

`check/places_1.jpg` に、各場所の冒頭の寄り(左)といちばん引いたところ(右、中心に赤い印)が並ぶ。
1枚目から形が目を引くか、雲や雪で白くないか、印が場所に合っているかを見る。

## ローカルで試す

```bash
pip install -r requirements.txt
```

```bash
python make_video.py --place venice --tts dummy --out out
```

`--tts dummy` は通信なしの仮の声。`--tts google`(既定)は Google Cloud Text-to-Speech を使う
(環境変数 `GOOGLE_TTS_API_KEY`。Claude Code の作業環境では Network secrets で texttospeech.googleapis.com に
`X-Goog-Api-Key` ヘッダーを付ける)。`--history upload_history.json` を付けると、投稿と同じく未投稿の場所を選び、
`out/meta.json` も書く。

## 自動投稿のセットアップ

### 1. Google Cloud(チャンネル専用のアカウント・プロジェクト)

1. チャンネルを持つ Google アカウントで、新しいプロジェクトを作る
2. 「API とサービス」→「ライブラリ」で **YouTube Data API v3** と **Cloud Text-to-Speech API** を有効にする
3. OAuth 同意画面: アプリ名「Guess From Space Uploader」、ホームページ・プライバシーポリシー・利用規約に
   - https://2000re.github.io/guess-from-space/
   - https://2000re.github.io/guess-from-space/privacy.html
   - https://2000re.github.io/guess-from-space/terms.html

   スコープは `youtube.upload` と `youtube.readonly`。公開ステータスを**本番環境**にする
   (「テスト」のままだとリフレッシュトークンが7日で失効する)
4. 認証情報 → OAuth クライアント ID(種類: デスクトップアプリ)を作り、JSON をダウンロード
5. 認証情報 → API キーを作り、Cloud Text-to-Speech API だけに制限する

### 2. リフレッシュトークンの取得(ローカル PC で一度だけ)

```bash
pip install google-auth-oauthlib
```

```bash
python3 get_youtube_refresh_token.py client_secret_xxx.json
```

ブラウザでは必ず Guess From Space のチャンネルを選ぶ。表示された値を次の Secrets に登録する
(値はチャットやコードに貼らない)。

### 3. GitHub の設定

- Settings → Secrets and variables → Actions → **Secrets**:
  `YT_CLIENT_ID`、`YT_CLIENT_SECRET`、`YT_REFRESH_TOKEN`、`YT_CHANNEL_ID`、`GOOGLE_TTS_API_KEY`
- **Variables**: `AUTO_POST` = `true`(定期実行を止めたいときは `false`)
- Settings → Pages: ブランチ `main`、フォルダ `/docs`
- Settings → Actions → General → Workflow permissions: Read and write

### 4. 最初のテスト投稿

Actions → post → Run workflow で、`privacy` を `unlisted` にして手動実行する。
新しい API プロジェクトからの投稿は、YouTube の審査を通るまで**非公開に固定**されることがある。
ログに「公開設定 unlisted を指定しましたが、private になりました」と出たら固定されている
(YouTube API Services の監査フォームから審査を申し込む)。

### 5. 定期実行(cron-job.org)

GitHub の `schedule` は数時間遅れるので使わない。cron-job.org から workflow_dispatch を呼ぶ:

- URL: `https://api.github.com/repos/2000Re/guess-from-space/actions/workflows/post.yml/dispatches`
- メソッド: POST
- ヘッダー: `Authorization: Bearer <Fine-grained token(このリポジトリの Actions: Read and write だけ)>`、
  `Accept: application/vnd.github+json`
- 本文: `{"ref":"main","inputs":{"scheduled":"true"}}`
- 時刻: 1日2本なら、例えば 07:47 と 19:47(JST)。Painted When? の時刻(02:17・07:17・10:17・22:17)とずらす。
  起動が重なっても `posted_today.py` が1日2本・4時間の間隔を守る

失敗すると Issue(ラベル `post-failure`、トークン失効なら `token-invalid`)が立つ。

## チャンネルの設定

- 名前: Guess From Space、ハンドル: @guess-from-space
- アイコン: `branding/icon.png`(アフリカの「サハラの目」に照準の輪)
- バナー: `branding/banner.png`(ヴェネツィア・パーム・ジュメイラ・サントリーニ・ボラボラ・ケープコッドなど)
- 説明文: `branding/description.txt`(出典を含む)
- 作り直すとき: `python tools/make_branding.py`

## Painted When? で得た教訓

- Shorts は冒頭1〜2秒が勝負。最初のコマから3択と問いを出している
- 投稿は cron-job.org から起動する(GitHub の schedule は遅れる)
- API キーや認証情報はコードに直書きしない。チャットにも貼らない
