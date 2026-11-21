# AutoVideoStudio

Python・VOICEVOX・FFmpegで原稿と静止画から動画を生成するWindows向けツールです。

## 必要環境
- Python 3.11（Windowsの `py` ランチャー）
- [VOICEVOX](https://voicevox.hiroshiba.jp/) を各自インストール
- [FFmpeg](https://ffmpeg.org/download.html) を各自インストール（libx264/AAC対応ビルド）

追加Pythonパッケージは不要です。外部ソフトウェア本体は同梱しません。

## 設定
`config.example.json` を `config.local.json` にコピーし、`voicevox_exe` と `ffmpeg_exe` を実際のパスに変更します。JSONではパス区切りに `/` を使えます。FFmpegがPATHにある場合は `ffmpeg` のままで構いません。ローカル設定はGit管理外です。

## 実行
`run.bat` をダブルクリックすると `sample/scenes.json` を読み、シーンごとにWAVを生成し、1280×720・30fpsのMP4を `sample/output.mp4` に保存します。別プロジェクトのフォルダをBATにドロップすることもできます。

個別実行:
```cmd
py -3.11 generate_audio.py sample
py -3.11 make_video.py sample
```

## シーン形式
UTF-8 JSON配列。各要素は `image`（プロジェクトからの相対パス）と `text`（読み上げ原稿）を持ちます。`script.txt` は参考用で、実行時の原稿は `scenes.json` です。

## 外部素材・ライセンス
自作コードはリポジトリの LICENSE に従います。VOICEVOX・FFmpegはそれぞれの規約に従って利用してください。[FFmpeg legal](https://ffmpeg.org/legal.html) / [VOICEVOX利用規約](https://voicevox.hiroshiba.jp/term/)。既定音声の公開時は `VOICEVOX:ずんだもん` と表示し、[音源規約](https://zunko.jp/con_ongen_kiyaku.html) と [キャラクターガイドライン](https://zunko.jp/guideline.html) を確認してください。サンプル画像はAI生成素材です。第三者の立ち絵・フォント等は同梱していません。

## Roadmap
字幕、立ち絵合成、口パク、まばたき、演出設定。
