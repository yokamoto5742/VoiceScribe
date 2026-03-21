import atexit
import faulthandler
import logging
import os
import signal
import sys
import tkinter as tk
import traceback
from tkinter import messagebox

from app import __version__
from app.main_window import VoiceInputManager
from app.notification_manager import NotificationManager
from app.ui_queue_processor import UIQueueProcessor
from external_service.elevenlabs_api import setup_elevenlabs_client
from service.audio_file_manager import AudioFileManager
from service.audio_recorder import AudioRecorder
from service.clipboard_manager import ClipboardManager
from service.recording_lifecycle import RecordingLifecycle
from service.transcription_handler import TranscriptionHandler
from service.text_transformer import load_replacements
from utils.app_config import AppConfig
from utils.config_manager import load_config
from utils.log_rotation import setup_logging, setup_debug_logging


def main():
    config = None
    app = None
    root = None

    # ネイティブクラッシュ（segfault等）のスタックトレースをファイルに出力
    _crash_log = open('crash_log.txt', 'w', encoding='utf-8')
    faulthandler.enable(file=_crash_log, all_threads=True)
    atexit.register(lambda: logging.info('プロセス終了 (atexit)'))

    def _handle_signal(signum, frame):
        logging.warning(f'シグナル受信: {signum} — アプリを終了します')
        if app:
            try:
                app.close_application()
            except Exception:
                pass

    signal.signal(signal.SIGTERM, _handle_signal)

    try:
        raw_config = load_config()
        config = AppConfig(raw_config)
        setup_logging(config.raw_config)
        setup_debug_logging(config.raw_config)

        logging.info('アプリケーションを開始します')

        # 依存オブジェクト生成
        recorder = AudioRecorder(config)
        client = setup_elevenlabs_client()
        logging.info('ElevenLabs APIクライアントを初期化しました')

        replacements = load_replacements(config.replacements_file)
        clipboard_manager = ClipboardManager(config, replacements)
        clipboard_manager.initialize()

        audio_file_manager = AudioFileManager(config)

        root = tk.Tk()
        ui_processor = UIQueueProcessor(root)
        ui_processor.start()

        notification_manager = NotificationManager(root, config)

        transcription_handler = TranscriptionHandler(
            config, client, audio_file_manager, ui_processor, config.use_punctuation
        )

        recording_lifecycle = RecordingLifecycle(
            root, config, recorder, audio_file_manager,
            transcription_handler, clipboard_manager,
            ui_processor, notification_manager.show_timed_message
        )

        app = VoiceInputManager(
            root, config, recording_lifecycle, notification_manager, __version__
        )

        def safe_close():
            try:
                if app:
                    app.close_application()
            except Exception as close_error:
                logging.error(f'終了処理中にエラー: {str(close_error)}')
                logging.debug(f'終了処理エラー詳細: {traceback.format_exc()}')

        root.protocol('WM_DELETE_WINDOW', safe_close)
        root.mainloop()
        logging.info('アプリケーションが正常に終了しました')

    except FileNotFoundError as e:
        error_msg = f'必要なファイルが見つかりません:\n{str(e)}\n\n設定ファイルやリソースファイルを確認してください。'
        logging.error(error_msg)
        logging.debug(f'FileNotFoundError詳細: {traceback.format_exc()}')
        _show_error_dialog(error_msg, 'ファイルエラー')

    except ValueError as e:
        error_msg = f'設定値エラー:\n{str(e)}\n\n設定ファイルや環境変数を確認してください。'
        logging.error(error_msg)
        logging.debug(f'ValueError詳細: {traceback.format_exc()}')
        _show_error_dialog(error_msg, '設定エラー')

    except Exception as e:
        error_msg = f'予期せぬエラーが発生しました:\n{str(e)}\n\n詳細は error_log.txt をご確認ください。'
        logging.error(error_msg)
        logging.error(f'予期せぬエラーの詳細: {traceback.format_exc()}')

        try:
            detailed_error = (
                f'=== VoiceScribe エラーレポート ===\n'
                f'バージョン: {__version__}\n'
                f'エラータイプ: {type(e).__name__}\n'
                f'エラーメッセージ: {str(e)}\n\n'
                f'=== 初期化状況 ===\n'
                f'Config: {"初期化済み" if config else "未初期化"}\n'
                f'Root: {"初期化済み" if root else "未初期化"}\n'
                f'App: {"初期化済み" if app else "未初期化"}\n\n'
                f'=== スタックトレース ===\n'
                f'{traceback.format_exc()}\n'
            )
            with open('error_log.txt', 'w', encoding='utf-8') as f:
                f.write(detailed_error)

            _show_error_dialog(error_msg, '予期せぬエラー')

            try:
                os.startfile('error_log.txt')
            except Exception:
                pass

        except Exception as log_error:
            final_error = f'エラーログの作成に失敗しました:\n{str(log_error)}\n\n元のエラー:\n{str(e)}'
            print(final_error, file=sys.stderr)
            _show_error_dialog(final_error, '重大なエラー')

    finally:
        try:
            if app and hasattr(app, 'close_application'):
                logging.info('最終クリーンアップを実行します')
                app.close_application()
            elif app:
                logging.warning('close_applicationメソッドが見つかりません。代替クリーンアップを実行します')
                _emergency_cleanup(app)
        except Exception as cleanup_error:
            logging.error(f'最終クリーンアップ中にエラー: {str(cleanup_error)}')
            logging.debug(f'クリーンアップエラー詳細: {traceback.format_exc()}')


def _emergency_cleanup(app):
    try:
        logging.info('緊急クリーンアップを開始します')

        cleanup_items = [
            ('recording_lifecycle', getattr(app, 'recording_lifecycle', None)),
            ('keyboard_handler', getattr(app, 'keyboard_handler', None)),
            ('notification_manager', getattr(app, 'notification_manager', None))
        ]

        for name, component in cleanup_items:
            if component and hasattr(component, 'cleanup'):
                try:
                    component.cleanup()
                    logging.info(f'緊急クリーンアップ完了: {name}')
                except Exception as e:
                    logging.error(f'緊急クリーンアップ失敗 ({name}): {str(e)}')

        if hasattr(app, 'master') and app.master:
            try:
                app.master.quit()
                app.master.destroy()
                logging.info('UI緊急終了完了')
            except Exception as e:
                logging.error(f'UI緊急終了中にエラー: {str(e)}')

    except Exception as e:
        logging.critical(f'緊急クリーンアップ中に重大なエラー: {str(e)}')


def _show_error_dialog(message: str, title: str = 'エラー'):
    try:
        try:
            root = tk._default_root
            if root:
                root.withdraw()
        except Exception:
            pass

        error_root = tk.Tk()
        error_root.withdraw()
        messagebox.showerror(title, message)
        error_root.destroy()

    except Exception as dialog_error:
        print(f'{title}: {message}', file=sys.stderr)
        print(f'ダイアログ表示エラー: {str(dialog_error)}', file=sys.stderr)


if __name__ == '__main__':
    main()
