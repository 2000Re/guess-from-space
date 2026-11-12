# 依頼: 衛星写真の場所当てクイズ「Guess From Space」の YouTube Shorts 自動投稿ボット

## 経緯
- チャンネル: Guess From Space(@guess-from-space)。リポジトリ: 2000Re/guess-from-space
- 別チャンネル「Painted When?」(名画の制作年当てクイズ、リポジトリ 2000Re/painted-when)を運用中。
  同じ仕組みで、衛星写真の場所当てクイズのチャンネルを新しく作りたい。
- 前のチャットでサンプル動画を3本作り、方向性は OK。テーマは世界遺産・有名観光地。
  動画の中の問いは「Where on Earth is this?」(チャンネル名とは別)。
- サンプルのコードは `sample/woe.py`(動画生成)と `sample/tiles.py`(衛星画像タイルの取得)。
  `woe.py` は painted-when の quiz.py・narration.py・art_shorts.py を `/home/user/painted-when` から import している。

## 動画の構成(サンプルで作ったもの。縦 1080x1920、15〜17秒)
1. 0秒: 衛星写真を最大まで寄せて画面いっぱいに。最初のコマから問い「Where on Earth is this?」・3択(縦に3つ)・
   残り時間のバーを出す。0秒に効果音、すぐ読み上げ開始
2. 読み上げ「Is it A? B? Or C?」に合わせて選択肢が弾み、その間に約80km四方まで引いていく
3. 「Lock in your answer!」→ 約2秒 → チャイムで正解が金色に光り、中心に輪の印、「It's Venice, in Italy!」
   画面上部に場所名・国・「A UNESCO World Heritage Site」
4. 答えのあと、その場所へもう一度寄る → 最後に見出しが「How did you do?」に変わる
- 画面下に衛星画像の出典を表示(ライセンスの条件)

## 衛星画像(確認済み)
- EOX「Sentinel-2 cloudless」2016年版。WMTS の層名 s2cloudless_3857(Web メルカトル)
  タイル: https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless_3857/default/g/{z}/{y}/{x}.jpg
- ライセンス: CC BY 4.0(配信元の説明で確認)。出典は
  「Sentinel-2 cloudless 2016 by EOX (https://s2maps.eu) · Contains modified Copernicus Sentinel data 2016」
- 2017年以降の層はライセンスが別なので使わない
- 最大ズーム 14(約10m/画素)。タイルは取得したらキャッシュして、同じタイルを何度も取りに行かない
- Claude Code の作業環境では tiles.maps.eox.at を通信の許可先に追加済み(GitHub Actions では制限なし)

## サンプルでわかったこと
- 向いている: 数km以上の大きな形で見分けられる場所(ヴェネツィア、富士山、島、湖、海岸線、パーム・ジュメイラ、
  グランド・キャニオン、ウルル、マンハッタンなど)。寄りの1コマ目から目を引く
- 向いていない: 建物単位の名所(エッフェル塔、タージ・マハル、ピラミッド)。10m では小さくてぼやける。
  アンコール・ワットもやや苦しい
- 画像は2016年のもの(それ以降の建設は映らない)
- 1本目はタイルの取得で約3分(以降はキャッシュで速い)

## Painted When? から流用するもの
- 読み上げ: Google Cloud Text-to-Speech、声 en-US-Chirp3-HD-Charon、1.1倍速(無料枠内)。
  キーは GitHub Actions では Secret GOOGLE_TTS_API_KEY、Claude Code の作業環境では Network secrets
  (texttospeech.googleapis.com、ヘッダー X-Goog-Api-Key、プレフィックスなし)
- 効果音(シュッ・ポン・コチコチ・チャイム)、選択肢の見た目、文字の影など
- 自動投稿の仕組み: youtube_upload.py(標準ライブラリのみ)、posted_today.py(1日の上限と間隔)、
  get_youtube_refresh_token.py、.github/workflows/post.yml(cron-job.org から workflow_dispatch で起動、
  scheduled=true と変数 AUTO_POST で制御、失敗時に Issue)、サイト生成 site_gen.py(GitHub Pages に問題ページ)
- このリポジトリには必要なファイルをコピーして、painted-when に依存しない形にする

## 次にやること
1. サンプルのコードと流用ファイルを整理して入れる
2. 場所のリストを作る(世界遺産・有名観光地で、衛星写真で大きな形が見える場所。名前・国・経度緯度・
   冒頭の寄りの広さ・ひとこと)。外れの選択肢は、同じ地域や似た地形のものから選ぶと面白い
3. 毎日の自動投稿(場所を重複なく選ぶ、投稿記録、YouTube へのアップロード、サイト)
4. アイコン・バナー・説明欄・ホームページ/プライバシーポリシー/利用規約

## Painted When? で得た教訓
- Shorts では冒頭1〜2秒が勝負(Painted When? は「視聴を継続」35%で苦戦)。最初のコマから3択と問いを出す
- GitHub の定期実行(schedule)は数時間遅れるので使わず、cron-job.org から起動する
- Google Cloud はチャンネル専用のアカウント・プロジェクトにまとめる(OAuth 同意画面は本番環境に公開、
  ホームページ・プライバシーポリシー・利用規約の URL が必要)。新しいプロジェクトからの投稿が非公開に固定されないか、
  最初のテスト投稿で確かめる
- API キーや認証情報はコードに直書きしない。チャットにも貼らない

## 守ってほしいこと
- 使う画像は、ライセンスを確認したものだけ(今は Sentinel-2 cloudless 2016、CC BY 4.0)。出典を動画と説明欄に必ず書く
- タイルの配信元に負荷をかけない(キャッシュ、取得の間隔をあける)
- 地名・国名などの事実は正確に。世界遺産と書くなら実際に登録されているものだけ
