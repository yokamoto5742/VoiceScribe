# VoiceScribe

Windows デスクトップアプリケーションで、ElevenLabs Speech-to-Text API を使用して音声をテキストに変換します。グローバルキーボードショートカットで簡単に音声録音を操作でき、他のアプリケーションへの自動テキスト貼り付けをサポートしています。

## 主な機能

- **リアルタイム音声認識**: ElevenLabs Speech-to-Text API による自動テキスト変換
- **グローバルキーボードショートカット**: Pause キーで録音開始/停止、F8 で再ロード、F9 で句読点切り替え
- **句読点と句点設定**: 句読点挿入機能 (トグル可能)
- **自動テキスト貼り付け**: Windows SendInput API による他のアプリケーションへの安全な貼り付け
- **置換辞書バックアップ**: 設定で指定したバックアップ先に自動保存

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
| F8 | 最新の音声ファイルを再ロード/再変換 |
| F9 | 句読点機能の有効/無効を切り替え |

### 基本的な使用フロー

1. Pause キーを押して音声録音を開始
2. マイクに向かって話す (最大 60 秒間自動で終了)
3. Pause キーを押して録音を終了
4. テキストが自動的に他のアプリケーションに貼り付けられます

### テキスト置換機能

置換ルールは `data/replacements.txt` に定義されます (カンマ区切り形式)。アプリケーション内の置換エディターから直接編集することも可能です。

**ファイル形式例:**

```
ありがとうございます,ありがとうございます
こんにちわ,こんにちは
```

置換ルールは記号や特殊文字にも対応しており、置換エディターから リアルタイムで編集・テストできます。

## 設定

### 環境変数 (.env)

プロジェクトルートに `.env` ファイルを作成し、ElevenLabs API キーを設定します

```
ELEVENLABS_API_KEY=your_api_key_here
```

### 設定ファイル (utils/config.ini)

主要な設定セクション:

| セクション | 説明 |
|----------|-----|
| `[AUDIO]` | サンプリングレート (16000 Hz)、チャンネル (1ch)、チャンク |
| `[ELEVENLABS]` | モデル (`scribe_v2`)、言語 (`jpn`)、オーディオイベントタグ |
| `[FORMATTING]` | 句読点機能 (`use_punctuation`) と句点設定 (`use_comma`) |
| `[KEYS]` | キーボードショートカット割り当て (pause, esc, f8, f9) |
| `[RECORDING]` | 自動停止タイマー (デフォルト 60 秒) |
| `[CLIPBOARD]` | テキスト貼り付けの遅延設定と SendInput/pyperclip フォールバック |
| `[PATHS]` | 置換ファイル、バックアップ先、一時ディレクトリ |
| `[LOGGING]` | ログレベル、保持期間、デバッグモード |
| `[OPTIONS]` | 起動時の最小化設定 |
| `[WINDOW]` | ウィンドウサイズ |
| `[EDITOR]` | 置換エディターのフォントサイズ、寸法 |

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
├── app/                          # Tkinter UI レイヤー
│   ├── main_window.py            # メインウィンドウ
│   ├── ui_components.py          # UI コンポーネント
│   ├── ui_queue_processor.py      # スレッドセーフ UI キュー
│   ├── notification.py           # 通知表示
│   └── replacements_editor.py    # テキスト置換エディタ
│
├── service/                      # ビジネスロジック層
│   ├── recording_lifecycle.py    # 記録→変換→貼り付けパイプライン
│   ├── audio_recorder.py         # 音声キャプチャ
│   ├── audio_file_manager.py     # WAV ファイル管理
│   ├── transcription_handler.py  # 非同期文字起こし処理
│   ├── text_transformer.py       # テキスト置換・句読点処理
│   ├── clipboard_manager.py      # クリップボード操作
│   ├── keyboard_handler.py       # グローバルキーボードショートカット
│   ├── paste_backend.py          # テキスト貼り付けバックエンド
│   └── recording_timer.py        # 自動停止タイマー
│
├── external_service/             # ElevenLabs API ラッパー層
│   └── elevenlabs_api.py         # Speech-to-Text API クライアント
│
├── utils/                        # 設定・ユーティリティ層
│   ├── app_config.py             # 設定クラス
│   ├── config_manager.py         # 設定管理
│   ├── env_loader.py             # 環境変数読み込み
│   └── config.ini                # デフォルト設定
│
├── tests/                        # テストスイート
│   ├── conftest.py               # テスト共通設定
│   └── (各レイヤーのテスト)
│
├── main.py                       # エントリーポイント
├── build.py                      # PyInstaller ビルドスクリプト
├── requirements.txt              # 依存パッケージ
├── .env                          # 環境変数 (Git 除外)
├── CLAUDE.md                     # 開発指示
└── README.md                     # このファイル
```

### アーキテクチャ

**レイヤー構成:**

- **`utils/`**: 設定のみ。`AppConfig` が `ConfigParser` をラップし、型安全なプロパティを公開
- **`external_service/`**: ElevenLabs API の薄いラッパー
- **`service/`**: UI を持たないビジネスロジック。各コンポーネント責務：
  - `RecordingLifecycle`: 全体のパイプライン統合（`AudioRecorder`、`TranscriptionHandler`、`ClipboardManager`、`AudioFileManager` を管理）
  - `AudioRecorder`: マイクキャプチャ
  - `TranscriptionHandler`: ElevenLabs へ送信し、`UIQueueProcessor` 経由で結果を配信
  - `TextTransformer`: 置換と句読点正規化
  - `ClipboardManager`: クリップボード操作と貼り付け実行
  - `KeyboardHandler`: グローバルキーボード登録
- **`app/`**: Tkinter UI レイヤー。`VoiceInputManager` がメインウィンドウ、`RecordingLifecycle` へ委譲

**データフロー:**

```
ユーザーのキー入力
    ↓
KeyboardHandler
    ↓
RecordingLifecycle.toggle_recording()
    ↓
AudioRecorder (バックグラウンドスレッド で音声キャプチャ)
    ↓
AudioFileManager (WAV ファイル保存)
    ↓
TranscriptionHandler (ElevenLabs API へ非同期送信)
    ↓
TextTransformer (置換・句読点処理)
    ↓
ClipboardManager (クリップボード操作)
    ↓
paste_backend (Win32 SendInput または pyperclip で貼り付け)
```

**スレッド設計:**

- UI の更新は必ず `UIQueueProcessor.schedule_callback()` 経由で実行
- バックグラウンドスレッドから Tkinter を直接呼び出さない
- `RecordingLifecycle` が `_check_process_thread` で文字起こしの完了をポーリング

## 主要な依存パッケージ

| パッケージ | バージョン | 用途 |
|-----------|----------|------|
| elevenlabs | 2.25.0 | Speech-to-Text API クライアント |
| PyAudio | 0.2.14 | 音声録音・キャプチャ |
| keyboard | 0.13.5 | グローバルキーボードショートカット |
| pyperclip | 1.9.0 | クリップボード操作 |
| python-dotenv | 1.1.1 | 環境変数読み込み |
| pywin32-ctypes | 0.2.3 | Windows API インターフェース |
| pytest | 8.4.1 | テスト実行 |
| pyright | 1.1.407 | 型チェック |
| pyinstaller | 6.14.2 | 実行可能ファイル生成 |

詳細は `requirements.txt` を参照してください

## トラブルシューティング

### API キーエラーが表示される

`.env` ファイルをプロジェクトルートに配置し、`ELEVENLABS_API_KEY` が正しく設定されていることを確認してください

```bash
type .env
```

**解決策:**

- [ElevenLabs](https://elevenlabs.io) から API キーを確認
- `.env` ファイルが Git に含まれていないことを確認 (`.gitignore` で除外)

### 音声が録音されない

**チェックリスト:**

1. Windows の設定でマイクが有効か確認
2. 別のアプリケーションがマイクを占有していないか確認
3. PyAudio が正しくインストール済みか確認: `python -c "import pyaudio; print('OK')"`

### テキスト貼り付けが機能しない

1. `utils/config.ini` で `use_sendinput = True` に設定されていることを確認
2. アプリケーションを管理者権限で実行を試す
3. テスト対象アプリケーションが標準的なテキスト入力に対応しているか確認 (例: メモ帳、Word)

## バージョン情報

- **現在のバージョン**: 2.0.2
- **最終更新日**: 2026年03月22日

## ライセンス

このプロジェクトのライセンス情報については、 [LICENSE](docs/LICENSE) を参照してください。

## 更新履歴

更新履歴は [CHANGELOG.md](docs/CHANGELOG.md) を参照してください。
