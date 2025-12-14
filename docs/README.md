# VoiceScribe

Windows デスクトップアプリケーション。ElevenLabs Speech-to-Text API を使用して音声をテキストに変換します。

**現在のバージョン**: 1.0.2

## 主な機能

- 音声録音と ElevenLabs Speech-to-Text API による自動テキスト変換
- グローバルキーボードショートカット (Pause キーで録音開始/停止)
- カスタムテキスト置換機能 (replacements.txt で任意の単語を自動変換)
- 句読点の自動挿入機能 (トグル可能)
- 他のアプリケーションへの自動テキスト貼り付け

## システム要件

- Windows 11 以上
- Python 3.12 以上
- オーディオ入力デバイス (マイク)

## インストール

### 1. リポジトリをクローン

```bash
git clone https://github.com/your-repo/VoiceScribe.git
cd VoiceScribe
```

### 2. 仮想環境を作成と有効化

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. 依存パッケージをインストール

```bash
pip install -r requirements.txt
```

### 4. ElevenLabs API キーを設定

プロジェクトルートに `.env` ファイルを作成します

```bash
ELEVENLABS_API_KEY=your_api_key_here
```

[ElevenLabs](https://elevenlabs.io) から API キーを取得できます

### 5. アプリケーション実行

```bash
python main.py
```

アプリケーションはデフォルトで最小化状態で起動します

## 使用方法

### キーボードショートカット

| キー | 機能 |
|------|------|
| Pause | 録音開始/停止 |
| Esc | アプリケーション終了 |
| F8 | 最新の音声ファイルを再ロード |
| F9 | 句読点機能の有効/無効を切り替え |

### 基本的な使用フロー

1. Pause キーを押して音声録音を開始
2. マイクに向かって話す (最大 60 秒間自動で終了)
3. Pause キーを押して録音を終了
4. テキストが自動的に他のアプリケーションに貼り付けられます

### テキスト置換機能

`service/replacements.txt` にカスタム置換ルールを定義します

**ファイル形式** (パイプ区切り)

```
元のテキスト|置換後のテキスト
ありがとうございます。|ありがとうございます
こんにちは|こんにちは
```

アプリケーション内の置換エディター (F10 キーでアクセス可能) からも編集できます

## 設定

### .env ファイル

プロジェクトルートに `.env` ファイルを作成し、ElevenLabs API キーを設定します

```
ELEVENLABS_API_KEY=your_api_key_here
```

### utils/config.ini

アプリケーションの詳細設定は `utils/config.ini` で管理されます

**主要な設定セクション:**

- `[AUDIO]`: サンプリングレート (16000 Hz)、チャンネル数 (1 = モノラル)
- `[ELEVENLABS]`: モデル (scribe_v2)、言語 (jpn = 日本語)
- `[KEYS]`: キーボードショートカットの割り当て
- `[RECORDING]`: 自動停止タイマー (秒)
- `[CLIPBOARD]`: テキスト貼り付けの遅延設定
- `[FORMATTING]`: 句読点機能の設定
- `[LOGGING]`: ログレベルと保持期間

詳細はファイルのコメントを参照してください

## 開発者向け情報

### テストの実行

```bash
# すべてのテストを実行
python -m pytest tests/ -v --tb=short

# カバレッジレポート付き
python -m pytest tests/ -v --tb=short --cov=. --cov-report=html

# 特定のテストファイル
python -m pytest tests/test_audio_recorder.py -v
```

### 型チェック

```bash
# ソースコードの型チェック
pyright app service utils
```

### 実行可能ファイルのビルド

```bash
python build.py
```

実行可能ファイルは `dist/VoiceScribe.exe` に出力されます。ビルド時にバージョンが自動的にインクリメントされます

### プロジェクト構造

```
VoiceScribe/
├── main.py                         # エントリーポイント
├── requirements.txt                # 依存パッケージ
├── build.py                        # ビルドスクリプト
├── .env                            # API キー (Git 除外)
│
├── app/                            # UI レイヤー
│   ├── __init__.py                 # バージョン情報
│   ├── main_window.py              # メインウィンドウ
│   └── ui_components.py            # UI コンポーネント
│
├── service/                        # ビジネスロジック
│   ├── recording_controller.py     # 録音フロー制御
│   ├── audio_recorder.py           # 音声キャプチャ
│   ├── keyboard_handler.py         # キーボード入力処理
│   ├── text_processing.py          # テキスト処理
│   ├── transcription_handler.py    # 文字起こし処理
│   ├── safe_paste_sendinput.py     # 安全な貼り付け
│   ├── notification.py             # Windows 通知
│   ├── replacements_editor.py      # 置換エディター UI
│   ├── recording_timer.py          # 録音タイマー管理
│   ├── ui_queue_processor.py       # UI キュー処理
│   └── replacements.txt            # カスタム置換ルール
│
├── external_service/               # API クライアント
│   └── elevenlabs_api.py           # ElevenLabs API
│
├── utils/                          # ユーティリティ
│   ├── config.ini                  # 設定ファイル
│   ├── config_manager.py           # 設定管理
│   ├── env_loader.py               # 環境変数読み込み
│   └── log_rotation.py             # ログ設定
│
├── tests/                          # テストスイート
│   ├── test_audio_recorder.py
│   ├── test_text_processing.py
│   └── ...
│
├── scripts/                        # ビルドスクリプト
│   └── version_manager.py          # バージョン管理
│
├── assets/                         # リソースファイル
│   └── VoiceScribe.ico
│
├── logs/                           # ログファイル (Git 除外)
└── docs/                           # ドキュメント
    └── README.md                   # このファイル
```

### アーキテクチャ

**データフロー:**

```
音声録音 → WAV ファイル保存 → ElevenLabs API → テキスト変換
→ テキスト置換 → 句読点処理 → クリップボード格納 → SendInput で貼り付け
```

**スレッド処理:**

- RecordingController は音声処理をスレッド上で実行
- UI 更新はスレッドセーフなキューを経由して実行
- タイマー機能による自動停止 (デフォルト 60 秒)

## 主要な依存パッケージ

- **elevenlabs** (2.25.0): Speech-to-Text API クライアント
- **PyAudio** (0.2.14): 音声録音
- **keyboard** (0.13.5): グローバルキーボードショートカット
- **pyperclip** (1.9.0): クリップボード操作
- **python-dotenv** (1.1.1): 環境変数管理
- **pywin32-ctypes** (0.2.3): Windows API インターフェース

詳細は `requirements.txt` を参照してください

## トラブルシューティング

### API キーエラー

`.env` ファイルが存在し、`ELEVENLABS_API_KEY` が正しく設定されていることを確認してください

```bash
cat .env
```

### 音声が録音されない

1. Windows の設定でマイクが有効か確認
2. PyAudio が正しくインストール済みか確認
   ```bash
   python -c "import pyaudio; print('OK')"
   ```
3. 別のアプリケーションがマイクを占有していないか確認

### テキスト貼り付けが機能しない

1. `utils/config.ini` で `use_sendinput = True` に設定
2. アプリケーションを管理者権限で実行を試す
3. 対象アプリケーションがテキスト入力に対応しているか確認

## ライセンス

このプロジェクトのライセンス情報についてはLICENSE ファイルを参照してください
