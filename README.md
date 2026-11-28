# Guess From Space

衛星写真の場所当て3択クイズを、YouTube Shorts(@guess-from-space)に自動投稿するボット。
仕組みは姉妹チャンネル Painted When?(2000Re/painted-when)と同じで、必要なファイルをコピーして単独で動くようにしてある。

- サイト: https://2000re.github.io/guess-from-space/ (GitHub Pages、`docs/`)
- 動画の中の問い: 「Where on Earth is this?」
- YouTube の題名: 「[番号] 」のあとに12の型を番号順に回し、毎回ちがう題名にする(#7 から。`make_video.py` の `TITLES`)。
  例:「Where on Earth is this? 🌍 Satellite Quiz」(classic。#6 まではすべてこれ)、「Can you name this place from space? 🛰️」、
  「This photo is only 3 km wide. Where on Earth is it? 🛰️」(冒頭の写真の幅 = places.py の start)、「Geography pros: where on Earth is this? 🌍」。
  答えのヒントになる地域名は入れない。型は `upload_history.json` の `title_style` に残り、`stats.md` で比べられる

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
| `locales.py` | 題名と説明の翻訳(日本語・スペイン語・フランス語・ドイツ語・ポルトガル語。題名の型ごとの訳。AI は使わない)。投稿のときに一緒に送り、断られたら翻訳なしで投稿する |
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

今は108か所。数km以上の大きな形で見分けられる世界遺産・有名観光地(島・火山・湖・海岸線・人工島・街の形など)。

- 選び方: まだ出していない場所から選ぶ。直前と同じ国は避ける。**内陸の自然(山・火山・湖・クレーター・峡谷・砂漠・滝など、
  `places.NATURE` の45か所)は3割**(`make_video.NATURE_SHARE`)、残りは街・海岸・島の形から選ぶ。2026-11-21 の時点で、
  街・海岸の回(リスボン 1,224、ケープコッド 1,192 など)が、山・湖の回(キリマンジャロ 389、タウポ湖 265 など)より見られていたため

- 入れないもの: 建物単位の名所(10m/画素では小さくてぼやける)、雪や雲で白くなる場所(エベレスト、ウユニ塩湖、
  ペリト・モレノ氷河、ロライマ山は試して外した)、2016年以降にできたもの
- 外れの選択肢: 同じ地域や似た地形の実在の場所
- ひとこと(`note`)は事実だけ。「UNESCO World Heritage Site」と書くのは実際に登録されている場所だけ
- 1日2本で約8週間分。使い切ると、いちばん前に出した場所から繰り返し、ログに警告を出す。早めに足すこと

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
- 時刻: **15:04 と 18:04(JST)**、取りこぼし用に30分後の 15:34・18:34(cron 式 `04,34 15,18 * * *`、タイムゾーン Asia/Tokyo。
  2026-11-22 に 12:47・19:47 から変更。先の回が成功していれば、予備の回は posted_today.py が止める)。
  2026-11-17 に 07:47 から 12:47 に変えた。19時台の回の平均 946回に対して、7時台は 502回だったため(`stats.md`)。
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

## 毎日の確認(`.github/workflows/daily-check.yml`)

毎日 03:13 JST ごろ(GitHub の schedule なので遅れることがある)に動く。手動では Actions → daily-check → Run workflow。

- **投稿が止まっていないか**(`watchdog.py`): 最後の投稿から30時間以上たっていたら Issue(ラベル `post-stalled`)を立てる。
  cron-job.org のトークン切れなどで post が起動されなかったときは post.yml 自身では何も残らないので、その見張り。
  投稿が再開すると次の確認で自動で閉じる。変数 `AUTO_POST` が `true` でないときは調べない
- **再生数の記録**(`stats.py`): 全動画の再生数・高評価・コメント数を YouTube Data API で取り、`stats.json` に残す。
  比べやすいよう、投稿から1日・3日・7日の時点の値を固定して残す(この仕組みより前の動画は最新の値だけ)。
  `stats.md` に、`upload_history.json` の項目(題名の型・版・カテゴリ・形式・美術館など、あるもの)と投稿の時間帯ごとの
  3日目の再生数の平均・中央値をまとめる。使う Secrets は投稿と同じ(`YT_CLIENT_ID`・`YT_CLIENT_SECRET`・`YT_REFRESH_TOKEN`)
- **共通ファイルのずれ**(`sync_check.py`): 4つのリポジトリの main を読み比べ、同じであるべきファイル
  (`stats.py`・`watchdog.py`・`sync_check.py`・`daily-check.yml`)が違えば sync ジョブを失敗にする。
  似ているファイル(`youtube_upload.py`・`posted_today.py` など)は、違う行数を Summary に並べる。
  1つで不具合を直したら、ほかの3つにも同じ直しが要るかを見る。中身は `python sync_check.py --diff youtube_upload.py`
- `stats.py`・`watchdog.py`・`sync_check.py` は4チャンネル(Painted When?、Guess From Space、Wait, That Big?、Too Close to Tell)で同じファイル

## 説明欄のリンク(2026-11-21〜)

上級者向け機能で説明欄のリンクがクリックできるようになったので、説明欄の終わりに姉妹チャンネル
(Wait, That Big?・Painted When?・Too Close to Tell)へのリンクを入れる(`make_video.SISTERS`。2026-11-21 から Too Close to Tell も入れた)。

## YouTube Analytics の数字(2026-11-21〜、`stats.py`)

`stats.md` に、動画ごとの平均視聴割合・登録者の増加と、日別の流入元(ショート フィードからの再生の割合)も出すようにした
(YouTube Analytics API。数字は2〜3日遅れ)。使うには、次の作業が1回だけ要る。それまでは、この部分だけ飛ばして今までどおり動く。

1. Google Cloud Console(このチャンネルのプロジェクト)で、「API とサービス」→「ライブラリ」→ **YouTube Analytics API** を有効にする
2. OAuth 同意画面の「データアクセス」に、スコープ `https://www.googleapis.com/auth/yt-analytics.readonly` を追加する
3. ローカル PC で `python3 get_youtube_refresh_token.py client_secret_xxx.json` を実行し直す(スコープに yt-analytics.readonly が加わった)
4. 表示された `YT_REFRESH_TOKEN` で、GitHub の Secrets を更新する(ほかの値は変わらない)

## 最後の終わり方(2026-11-21〜)

Shorts は最後まで見られると頭からくり返される。くり返し再生につなげやすいよう、最後の読み上げのあとの間を短くした
(Painted When?・Guess From Space は、最後に冒頭と同じ拡大した場面へ戻る)。どちらの終わり方かは
`upload_history.json` の `ending` に残り、`stats.md` で比べられる。

## 短くした(2026-11-21〜)

平均視聴割合(YouTube Analytics)が、Wait, That Big? のほとんど 90〜101% に対して、このチャンネルはほとんど 68〜77% だった。
答えが出たあと(国名とひとことの読み上げ)で離れる人が多いとみて、次のように短くした(約17秒 → 約12秒)。

- ひとこと(`note`)は読み上げず、画面に出すだけ
- 問い・選択肢・「Lock in your answer!」の間を詰め、答えまでの待ち時間を 2.0 → 1.5 秒
- 投稿記録の `ending` は `loop_short`(それまでの `loop` と、`stats.md` で比べられる)

あわせて、寄りの写真が灰色の街並みばかりの街(`places.GREY_CITY`: モスクワ・ソウル・東京など10か所)は1割
(`make_video.GREY_CITY_SHARE`)だけにした。パリ(295)・ストックホルム(394)が、海岸や川の形がはっきりした回
(リスボン 1,225・ケープコッド 1,194)より見られていなかったため。内陸の自然は今までどおり3割、残りの6割は街・海岸・島の形から選ぶ。

## ゲームの舞台の回(2026-11-21〜)

番号が7の倍数の回(`make_video.GAME_EVERY`)は、有名なゲームの舞台、またはモデルになった実在の場所
(`places.GAME_PLACES`、15か所)から出す。見出しの上は「GAME WORLD · REAL PLACE」、問いの読み上げと題名
(`make_video.GAME_TITLES`、翻訳つき)もゲーム向けになる。ゲーム名は題名に書かず、答えのあとに画面と説明欄に出す。

- 画像はふつうの回と同じ Sentinel-2 cloudless 2016(約10m/画素)。「High Resolution」とは書かない。
  建物単位の名所(渋谷の交差点など)は見分けられないので入れない(ギザのピラミッドは三角の形が見えるので入れた)
- ゲームの画面・ロゴ・キャラクター・アイコンは使わない。ゲーム名を文字で書くだけ。説明欄に
  「ゲームの映像は使っておらず、ゲームの制作会社とは関係がない」と書く
- GTA のように架空の街のときは「舞台」ではなく「モデルになった街」(The model for Los Santos …)と書く
- 投稿記録の `format` は `game`(ふつうの回は `place`)、`game` にゲーム名が残り、`stats.md` で比べられる
- 15か所を出し終えたら、ふつうの回だけに戻る。足すときは `python tools/check_places.py --only game-…` で形を確かめる

## 再生リスト(2026-11-22〜、`playlists.py`・`playlist_rules.py`)

投稿するたびに、合う再生リストへ自動で入れる(なければ公開で作る)。どの再生リストに入れるかは `playlist_rules.py`。
`python playlists.py --show` で、これまでの回がどこに入るかを確かめられる(通信なし)。

- 再生リストの操作には、リフレッシュトークンに `youtube` スコープが要る(`get_youtube_refresh_token.py` に追加済み)。
  権限のないトークンのままでも投稿は止まらず、ログに警告が出るだけ
- 取り直し: Google Cloud Console の OAuth 同意画面(データアクセス)に `.../auth/youtube` を足してから、
  `python get_youtube_refresh_token.py client_secret.json` を実行し、Secrets の `YT_REFRESH_TOKEN` を新しい値にする
- これまでの動画は、Actions の「playlists」を手動で1回動かすとまとめて入る(入っている動画は入れ直さない)
- `playlists.py` と `.github/workflows/playlists.yml` は4チャンネルで同じファイル(`sync_check.py` で確かめる)

## 通常動画「Guess From Space Challenge」(2026-11-23〜、`longform.py`)

横長(1920x1080)、12問・約3分40秒、週1本。右に衛星写真、左の帯に問題・3択・5秒のカウントダウン。
考えている間に少しずつ引き、答えで一気に引いて、中心に輪の印と場所の名前・国・ひとことを出す。

- 場所は places.py から選ぶ(自然4問、灰色の街並みの街とゲームの舞台は1問まで、同じ国は1問だけ)。
  過去の通常動画で出した場所は出さない。直近30日の Shorts に出た場所は後回し(足りなければ使う)。
  Shorts の場所選びには影響しない(通常動画と Shorts で同じ場所が出ることはある)
- チャプターは「Place 1」などにして、答えは書かない。答えは説明欄の下の方にまとめる。
  チャプターはどれも10秒以上(`check_chapters`。満たさなければ書き出す前に止める)
- 出典(CC BY 4.0)は動画の右下に常に出し、説明欄にも書く。タイルは Shorts と同じ tile_cache を使い回す
- サムネイル: `thumbnail.jpg`(a、投稿のときに設定)、`thumbnail_b.jpg`(Where on Earth is this?)、
  `thumbnail_c.jpg`(Can you get 12/12?)。b・c は Actions の Artifacts からダウンロードして「テストと比較」に使う
- 投稿は `.github/workflows/longform.yml`。毎週日曜 10:13 UTC(19:13 JST)ごろの定期実行は、リポジトリ変数
  `LONGFORM_AUTO` が `true` のときだけ動く。手動実行の既定は限定公開(unlisted)
- 投稿すると「Guess From Space Challenge: Full Quizzes」の再生リストに入り、Shorts の説明欄にもいちばん新しい回のリンクが出る
- 試す: `python longform.py --tts dummy --rounds 3 --out out_long`

## 投稿時刻(2026-11-24〜)

4チャンネルで1日8本を3時間おきに割り振った(各チャンネルの2本は12時間離す。予備は30分後。タイムゾーン Asia/Tokyo):

| チャンネル | 投稿 | cron 式 |
|---|---|---|
| Painted When? | 0:17・12:17 | `17,47 0,12 * * *` |
| Too Close to Tell | 3:08・15:08 | `08,38 3,15 * * *` |
| Guess From Space | 6:04・18:04 | `04,34 6,18 * * *` |
| Wait, That Big? | 9:23・21:23 | `23,53 9,21 * * *` |

(2026-11-24 に、上の表から1時間ずつ早めた。以前は 1:17・4:08・7:04・10:23 からの3時間おき)

上に書かれた以前の時刻は経緯として残している。先の回が成功していれば、予備の回は posted_today.py が止める。

## 通常動画の予告編の Short(2026-11-24〜、`make_video.teaser_plan`)

通常動画(Guess From Space Challenge)を投稿してから3日以内の最初の Shorts の回を、その通常動画の予告編にする(週1本。本数は増やさない)。
Wait, That Big? と同じ仕組み。

- 通常動画の問題から1問(最初の2問と、Shorts に出したものは避ける)を、いつもの Shorts と同じ形で答えまで見せる
- 最後の約2秒、上に「Place 3 of 12 · Guess From Space Challenge #1 / Play all 12 places!」の帯を重ね、最後の一言は「That was place N. Want M more? Tap the link to play the full challenge!」
- 説明欄の1行目に通常動画のリンク。投稿記録の `teaser` に通常動画の番号が入る(同じ回の予告編は1本だけ)
- **YouTube Studio で、その Short の「関連動画」に通常動画を設定する**(API ではできない。画面にタップできるリンクが出る)

## 通常動画の予約投稿(2026-11-24〜、`longform.scheduled_publish`)

2026-11-26 から、作るのを前日の土曜 10:13 UTC(19:13 JST)ごろに早めた(11/25 の Painted When? #2 は、定期実行が8時間半遅れて予約の20分前にやっと上がったため)。公開は今までどおり当日 19:13 JST。

GitHub の定期実行は数時間遅れることがあるので、通常動画は日曜 1:13 UTC(10:13 JST)ごろに作って非公開で上げ、
日曜 19:13 JST に YouTube が公開する(YouTube Data API の `publishAt`)。

- 定期実行が遅れて、公開の時刻の10分前を過ぎていたら、すぐ公開する。日付をまたいで遅れたときも、来週にはせずすぐ公開する
- 投稿記録(`longform_history.json`)の `publish_at` に公開の時刻が入る。Shorts の説明欄のリンクと予告編の Short は、
  公開の時刻を過ぎてから(公開前の動画を案内しない)
- 手動実行は今までどおり、選んだ公開設定ですぐ上げる(予約しない)

通常動画の公開は、2026-11-28 から日曜 8:13 JST(アメリカ東部の前日の夜 18:13)。作るのは前日の土曜 1:13 UTC(10:13 JST)ごろ。
