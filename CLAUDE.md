# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## House Rules:
- 文章ではなくパッチの差分を返す。
- コードの変更範囲は最小限に抑える。
- コードの修正は直接適用する。
- Pythonのコーディング規約はPEP8に従います。
- KISSの原則に従い、できるだけシンプルなコードにします。
- 可読性を優先します。一度読んだだけで理解できるコードが最高のコードです。
- Pythonのコードのimport文は以下の適切な順序に並べ替えてください。
標準ライブラリ
サードパーティライブラリ
カスタムモジュール 
それぞれアルファベット順に並べます。importが先でfromは後です。

## クリーンコードガイドライン
- 関数のサイズ：関数は50行以下に抑えることを目標にしてください。関数の処理が多すぎる場合は、より小さな関数に分割してください。
- 単一責任：各関数とモジュールには明確な目的が1つあるようにします。無関係なロジックをまとめないでください。
- 命名：説明的な名前を使用してください。`tmp` 、`data`、`handleStuff`のような一般的な名前は避けてください。例えば、`doCalc`よりも`calculateInvoiceTotal` の方が適しています。
- DRY原則：コードを重複させないでください。類似のロジックが2箇所に存在する場合は、共有関数にリファクタリングしてください。それぞれに独自の実装が必要な場合はその理由を明確にしてください。
- コメント:分かりにくいロジックについては説明を加えます。説明不要のコードには過剰なコメントはつけないでください。
- コメントとdocstringは必要最小限に日本語で記述します。
- このアプリのUI画面で表示するメッセージはすべて日本語にします。

## What This Project Is

VoiceScribe is a Windows desktop application that records audio via hotkey, transcribes it using the ElevenLabs Scribe API, and pastes the result into the active window. It is built with Python + Tkinter and packaged with PyInstaller.

## Commands

```bash
# Run the application
python main.py

# Run all tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=html

# Run a single test file
pytest tests/service/test_transcription_handler.py

# Run a single test by name
pytest tests/service/test_transcription_handler.py::TestClass::test_method

# Type checking
pyright

# Build the executable
python build.py
```

## Architecture

The app follows a layered dependency injection pattern. `main.py` constructs all objects and wires them together — there is no service locator or global state.

### Layer breakdown

- **`utils/`** — Configuration only. `AppConfig` wraps a `ConfigParser` and exposes typed properties. `config.ini` holds all defaults. A `.env` file holds secrets (`ELEVENLABS_API_KEY`).

- **`external_service/`** — Thin wrapper around the ElevenLabs API. `elevenlabs_api.py` exposes `setup_elevenlabs_client()` and `transcribe_audio()`.

- **`service/`** — Business logic, no UI imports.
  - `RecordingLifecycle` — orchestrates the full record→transcribe→paste pipeline; owns `AudioRecorder`, `TranscriptionHandler`, `ClipboardManager`, `AudioFileManager`.
  - `TranscriptionHandler` — submits audio frames to ElevenLabs and handles async result delivery via `UIQueueProcessor`.
  - `ClipboardManager` — copies transcribed text to clipboard and triggers paste via `paste_backend`.
  - `KeyboardHandler` — registers global hotkeys using the `keyboard` library.
  - `TextTransformer` — applies text replacements (`replacements.txt`) and punctuation normalization.

- **`app/`** — Tkinter UI layer.
  - `VoiceInputManager` — main window (`tk.Frame`), owns `KeyboardHandler`, delegates recording to `RecordingLifecycle`.
  - `UIQueueProcessor` — thread-safe bridge; other threads call `schedule_callback(fn)` to run UI updates on the main thread.
  - `NotificationManager` — timed overlay messages.
  - `ReplacementsEditor` — in-app editor for `replacements.txt`.

### Key data flows

1. User presses the toggle key → `KeyboardHandler` → `RecordingLifecycle.toggle_recording()`
2. Recording stops → `AudioFileManager` saves frames → `TranscriptionHandler.transcribe_frames()` (background thread)
3. ElevenLabs returns text → `TextTransformer.replace_text()` → `ClipboardManager.copy_and_paste()`
4. Paste is dispatched via `paste_backend` using Win32 `SendInput`; fallback to `pyperclip`

### Threading model

- All UI mutations must go through `UIQueueProcessor.schedule_callback()` — never call Tkinter from a background thread directly.
- `RecordingLifecycle` manages a `_check_process_thread` that polls the transcription future and delivers results.

## Configuration

`utils/config.ini` is the primary config file. Key sections:

| Section | Notable keys |
|---------|-------------|
| `[KEYS]` | `toggle_recording`, `exit_app`, `toggle_punctuation` |
| `[ELEVENLABS]` | `model` (default `scribe_v2`), `language` (default `jpn`) |
| `[PATHS]` | `replacements_file`, `temp_dir` |
| `[RECORDING]` | `auto_stop_timer` (seconds) |

`ELEVENLABS_API_KEY` must be set in `.env`.

## Tests

Tests mirror the source tree under `tests/`. `tests/conftest.py` provides `dict_to_app_config()` — a helper that builds an `AppConfig` from a plain dict without reading `config.ini`, used throughout service-layer tests.

UI tests (under `tests/app/`) mock Tkinter. External API tests (under `tests/external_service/`) mock the ElevenLabs client.
