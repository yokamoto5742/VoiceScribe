# VoiceScribe

Windows デスクトップアプリケーションで、ElevenLabs Speech-to-Text API を使用して音声をテキストに変換します。グローバルキーボードショートカットで簡単に音声録音を操作でき、他のアプリケーションへの自動テキスト貼り付けをサポートしています。

**現在のバージョン**: 1.0.4

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
| F10 | 置換エディターを表示 |

### 基本的な使用フロー

1. Pause キーを押して音声録音を開始
2. マイクに向かって話す (最大 60 秒間自動で終了)
3. Pause キーを押して録音を終了
4. テキストが自動的に他のアプリケーションに貼り付けられます

### テキスト置換機能

置換ルールは `service/replacements.txt` に定義されます (パイプ区切り形式)。アプリケーション内の置換エディターから直接編集することも可能です。

**ファイル形式例:**

```
ありがとうございます。|ありがとうございます
こんにちは|こんにちは
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
|----------|------|
| `[AUDIO]` | サンプリングレート 16000 Hz、モノラル (1ch) |
| `[ELEVENLABS]` | モデル (scribe_v2)、言語 (jpn) |
| `[FORMATTING]` | 句読点 (`use_punctuation`) と句点設定 (`use_comma`) |
| `[KEYS]` | キーボードショートカット割り当て |
| `[RECORDING]` | 自動停止タイマー (デフォルト 60 秒) |
| `[CLIPBOARD]` | テキスト貼り付けの遅延・フォールバック設定 |
| `[PATHS]` | 置換ファイル、バックアップ、テンポラリーディレクトリ |
| `[LOGGING]` | ログレベル、保持期間、デバッグモード |

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
├── main.py                    # アプリケーション エントリーポイント
├── requirements.txt           # Python 依存パッケージ
├── build.py                   # PyInstaller ビルドスクリプト
│
├── app/                       # UI層 (Tkinter)
│   ├── main_window.py         # メインウィンドウ、コンポーネント統合
│   └── ui_components.py       # UI ウィジェット、レイアウト
│
├── service/                   # ビジネスロジック層
│   ├── recording_controller.py       # 録音フロー制御
│   ├── audio_recorder.py             # PyAudio による音声キャプチャ
│   ├── keyboard_handler.py           # グローバルキーボードショートカット
│   ├── transcription_handler.py      # 文字起こし処理、テキスト貼り付け
│   ├── text_processing.py            # テキスト置換、句読点処理
│   ├── safe_paste_sendinput.py       # SendInput API による安全な貼り付け
│   ├── notification.py               # Windows トースト通知
│   ├── replacements_editor.py        # 置換ルール編集 UI
│   ├── recording_timer.py            # 自動停止タイマー管理
│   ├── ui_queue_processor.py         # UI 更新キュー処理 (スレッドセーフ)
│   └── replacements.txt              # カスタム置換ルール
│
├── external_service/          # 外部サービス連携
│   └── elevenlabs_api.py      # ElevenLabs Speech-to-Text API クライアント
│
├── utils/                     # ユーティリティ
│   ├── config.ini             # アプリケーション設定ファイル
│   ├── config_manager.py      # 設定ファイル読み込み・保存
│   ├── env_loader.py          # .env ファイル読み込み
│   └── log_rotation.py        # ログ出力設定、ファイル回転
│
├── tests/                     # テストスイート (pytest)
├── scripts/                   # ビルド・管理スクリプト
├── assets/                    # リソース (アイコンなど)
├── logs/                      # アプリケーション ログ (Git 除外)
└── docs/
    ├── README.md              # このファイル
    └── CHANGELOG.md           # 変更履歴 (Keep a Changelog 形式)
```

### アーキテクチャ

**処理フロー:**

```
[音声録音] → [WAV 保存] → [ElevenLabs API] → [テキスト取得]
    ↓
[テキスト置換] → [句読点処理] → [クリップボード] → [SendInput 貼り付け]
```

**スレッド設計:**

- **RecordingController**: 音声処理をバックグラウンドスレッドで実行
- **UIQueueProcessor**: スレッドセーフなキュー経由で UI 更新を処理
- **RecordingTimer**: 自動停止タイマー (デフォルト 60 秒)
- **TranscriptionHandler**: 文字起こしと後処理を非同期実行

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

- [ElevenLabs ダッシュボード](https://elevenlabs.io) から API キーを確認
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

## ライセンス

このプロジェクトのライセンス情報についてはLICENSE ファイルを参照してください
