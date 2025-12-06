# 変更履歴

このプロジェクトのすべての重要な変更は、このファイルに記録されます。

フォーマットは [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に基づいており、
バージョン番号は [Semantic Versioning](https://semver.org/lang/ja/) に従っています。

## [Unreleased]

## [1.0.1] - 2025-12-07

### 追加

- `notification.py` に `show_timed_message()` 関数のデフォルト引数を追加

### 変更

- `recording_controller.py` で punctuation 設定をインスタンス変数に格納して、状態管理を改善
- ペースト遅延のデフォルト値を更新
- UI のウィンドウサイズをデフォルトで 300x350 に変更
- README と ドキュメントの簡潔化

### 修正

- `text_processing.py` の `get_replacements_path()` で `_MEIPASS` がない場合のフォールバック処理を追加し、PyInstaller でのビルド時の互換性を向上
- 置換ルール設定で不要な置換ペアを削除

## [0.0.1] - 2025-12-06

### 追加

- VoiceScribe の初版リリース
- ElevenLabs Speech-to-Text API を使用した音声文字起こし機能
- グローバルキーボードショートカット（Ctrl+E で録音開始/停止、Esc で終了、F8 で再読み込み）
- 自動テキスト置換機能（replacements.txt で設定可能）
- 句読点の自動処理（設定可能）
- Windows クリップボードへのコピーと SendInput API による自動ペースト
- Windows トースト通知機能
- 録音時間の自動停止（デフォルト 60 秒）
- 設定ファイル（config.ini）による各種設定
- ロギング機能と ログファイルのローテーション

### 変更

- プロジェクト名を VoiceScribe に統一
- API プロバイダーを ElevenLabs に統一
- 外部 API 呼び出しの改善とログ強化
- UI レイアウトの最適化

### 削除

- 旧 elevenlabs_api.py を削除

[Unreleased]: https://github.com/yourusername/VoiceScribe/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/yourusername/VoiceScribe/compare/v0.0.1...v1.0.1
[0.0.1]: https://github.com/yourusername/VoiceScribe/releases/tag/v0.0.1
