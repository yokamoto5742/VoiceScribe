import configparser
import glob
import logging
import os
import threading
import time
import tkinter as tk
from datetime import datetime, timedelta
from typing import Any, Callable, Dict

from service.recording_timer import RecordingTimer
from service.transcription_handler import TranscriptionHandler
from service.ui_queue_processor import UIQueueProcessor
from utils.config_manager import get_config_value


class RecordingController:

    def __init__(
            self,
            master: tk.Tk,
            config: configparser.ConfigParser,
            recorder: Any,
            client: Any,
            replacements: Dict[str, str],
            ui_callbacks: Dict[str, Callable],
            notification_callback: Callable
    ):
        self.master = master
        self.config = config
        self.recorder = recorder
        self.ui_callbacks = ui_callbacks
        self.show_notification = notification_callback

        self.temp_dir = config['PATHS']['TEMP_DIR']
        self.cleanup_minutes = int(config['PATHS']['CLEANUP_MINUTES'])
        os.makedirs(self.temp_dir, exist_ok=True)

        self.ui_processor = UIQueueProcessor(master)
        self.ui_processor.start()

        # 文字起こしテキストの処理
        use_punctuation = get_config_value(config, 'WHISPER', 'USE_PUNCTUATION', True)
        self.transcription_handler = TranscriptionHandler(
            master, config, client, replacements, self.ui_processor, use_punctuation
        )
        self.transcription_handler.set_error_callback(self._safe_error_handler)

        # タイマー管理
        self.recording_timer = RecordingTimer(
            master, config, self.ui_processor,
            notification_callback,
            lambda: self.recorder.is_recording,
            self._stop_recording_process
        )

        self._cleanup_temp_files()

    def _cleanup_temp_files(self):
        """古い一時ファイルを削除"""
        try:
            current_time = datetime.now()
            pattern = os.path.join(self.temp_dir, "*.wav")

            for file_path in glob.glob(pattern):
                file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                if current_time - file_modified > timedelta(minutes=self.cleanup_minutes):
                    try:
                        os.remove(file_path)
                        logging.info(f"古い音声ファイルを削除しました: {file_path}")
                    except Exception as e:
                        logging.error(f"ファイル削除中にエラーが発生しました: {file_path}, {e}")
        except Exception as e:
            logging.error(f"クリーンアップ処理中にエラーが発生しました: {e}")

    def _handle_error(self, error_msg: str):
        """エラーを処理してUIに反映"""
        try:
            if self.ui_processor.is_ui_valid():
                self.show_notification("エラー", error_msg)
                self.ui_callbacks['update_status_label'](
                    f"{self.config['KEYS']['TOGGLE_RECORDING']}キーで音声入力開始/停止"
                )
                self.ui_callbacks['update_record_button'](False)
                if self.recorder.is_recording:
                    self.recorder.stop_recording()
        except Exception as e:
            logging.error(f"エラーハンドリング中にエラー: {str(e)}")

    def _safe_error_handler(self, error_msg: str):
        """スレッドセーフなエラーハンドラ"""
        try:
            if self.ui_processor.is_ui_valid():
                self._handle_error(error_msg)
            else:
                logging.error(f"UI無効時のエラー: {error_msg}")
        except Exception as e:
            logging.error(f"エラーハンドリング中にエラー: {str(e)}")

    def toggle_recording(self):
        """録音の開始/停止を切り替え"""
        if not self.recorder.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        if (self.transcription_handler.processing_thread and
                self.transcription_handler.processing_thread.is_alive()):
            raise RuntimeError("前回の処理が完了していません")

        self.transcription_handler.reset_cancel()
        self.recorder.start_recording()
        self.ui_callbacks['update_record_button'](True)
        self.ui_callbacks['update_status_label'](
            f"音声入力中... ({self.config['KEYS']['TOGGLE_RECORDING']}キーで停止)"
        )

        recording_thread = threading.Thread(target=self._safe_record, daemon=False)
        recording_thread.start()

        self.recording_timer.start()

    def _safe_record(self):
        try:
            self.recorder.record()
        except Exception as e:
            logging.error(f"録音中にエラーが発生しました: {str(e)}")
            try:
                self.master.after(0, self._safe_error_handler,
                                  f"録音中にエラーが発生しました: {str(e)}")
            except Exception:
                pass

    def stop_recording(self):
        try:
            self.recording_timer.cancel()
            self._stop_recording_process()
        except Exception as e:
            self._safe_error_handler(f"録音の停止中にエラーが発生しました: {str(e)}")

    def _stop_recording_process(self):
        """録音停止後の処理"""
        try:
            frames, sample_rate = self.recorder.stop_recording()
            logging.info("音声データを取得しました")

            self.ui_callbacks['update_record_button'](False)
            self.ui_callbacks['update_status_label']("テキスト出力中...")

            self.transcription_handler.processing_thread = threading.Thread(
                target=self.transcription_handler.transcribe_frames,
                args=(frames, sample_rate, self._safe_ui_update, self._safe_error_handler),
                daemon=False
            )
            self.transcription_handler.processing_thread.start()

            if self.ui_processor.is_ui_valid():
                self.master.after(
                    100,
                    self._check_process_thread,
                    self.transcription_handler.processing_thread
                )
        except Exception as e:
            logging.error(f"録音停止処理中にエラー: {str(e)}")
            self._safe_error_handler(f"録音停止処理中にエラー: {str(e)}")

    def _check_process_thread(self, thread: threading.Thread):
        """処理スレッドの完了をチェック"""
        try:
            if not thread.is_alive():
                self.ui_callbacks['update_status_label'](
                    f"{self.config['KEYS']['TOGGLE_RECORDING']}キーで音声入力開始/停止"
                )
                self.transcription_handler.processing_thread = None
                return

            self.ui_callbacks['update_status_label']("テキスト出力中...")
            if self.ui_processor.is_ui_valid():
                self.master.after(100, self._check_process_thread, thread)
        except Exception as e:
            logging.error(f"処理スレッドチェック中にエラー: {str(e)}")

    def handle_audio_file(self, event):
        """音声ファイルを処理"""
        try:
            file_path = self.master.clipboard_get()
            if not os.path.exists(file_path):
                self.show_notification('エラー', '音声ファイルが見つかりません')
                return

            self.ui_callbacks['update_status_label']('音声ファイル処理中...')

            self.transcription_handler.handle_audio_file(
                file_path,
                self._safe_ui_update,
                lambda e: self.show_notification('エラー', e)
            )
        except Exception as e:
            self.show_notification('エラー', str(e))
        finally:
            self.ui_callbacks['update_status_label'](
                f"{self.config['KEYS']['TOGGLE_RECORDING']}キーで音声入力開始/停止"
            )

    def _safe_ui_update(self, text: str):
        """スレッドセーフなUI更新"""
        try:
            logging.debug(f"_safe_ui_update開始: text長={len(text)}")
            if self.ui_processor.is_ui_valid():
                self.ui_update(text)
            else:
                logging.warning("UIが無効なため、UI更新をスキップします")
        except Exception as e:
            logging.error(f"UI更新中にエラー: {str(e)}")
            import traceback
            logging.debug(f"詳細: {traceback.format_exc()}")

    def ui_update(self, text: str):
        """UIを更新してペースト処理をスケジュール"""
        try:
            logging.debug(f"ui_update開始: text長={len(text)}")
            paste_delay = int(float(self.config['CLIPBOARD'].get('PASTE_DELAY', 0.3)) * 1000)
            if self.ui_processor.is_ui_valid():
                self.master.after(
                    paste_delay,
                    self.transcription_handler.copy_and_paste,
                    text
                )
                logging.debug(f"copy_and_pasteをスケジュール: delay={paste_delay}ms")
        except Exception as e:
            logging.error(f"UI更新中にエラー: {str(e)}")
            import traceback
            logging.debug(f"詳細: {traceback.format_exc()}")

    def cleanup(self):
        """リソースをクリーンアップ"""
        try:
            logging.info("RecordingController クリーンアップ開始")
            self.ui_processor.shutdown()
            self.transcription_handler.cancel()

            if self.recorder.is_recording:
                self.stop_recording()

            if (self.transcription_handler.processing_thread and
                    self.transcription_handler.processing_thread.is_alive()):
                logging.info("処理スレッドの完了を待機中...")
                for _ in range(50):
                    if not self.transcription_handler.processing_thread.is_alive():
                        break
                    time.sleep(0.1)

                if self.transcription_handler.processing_thread.is_alive():
                    logging.warning("処理スレッドが強制終了されました")
                    self.transcription_handler.processing_thread.join(1.0)

            self.recording_timer.cleanup()
            self._cleanup_temp_files()

        except Exception as e:
            logging.error(f"クリーンアップ処理中にエラーが発生しました: {str(e)}")
