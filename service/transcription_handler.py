"""音声文字起こし処理を提供するモジュール"""
import configparser
import logging
import threading
import tkinter as tk
import traceback
from typing import Any, Callable, Dict, List, Optional

from external_service.elevenlabs_api import transcribe_audio
from service.audio_recorder import save_audio
from service.text_processing import copy_and_paste_transcription, process_punctuation
from service.ui_queue_processor import UIQueueProcessor


class TranscriptionHandler:
    """音声の文字起こしとペースト処理を担当するクラス"""

    def __init__(
            self,
            master: tk.Tk,
            config: configparser.ConfigParser,
            client: Any,
            replacements: Dict[str, str],
            ui_processor: UIQueueProcessor,
            use_punctuation: bool
    ):
        self.master = master
        self.config = config
        self.client = client
        self.replacements = replacements
        self.ui_processor = ui_processor
        self.use_punctuation = use_punctuation

        self.cancel_processing = False
        self.processing_thread: Optional[threading.Thread] = None
        self.transcribe_audio_func = transcribe_audio

    def transcribe_frames(
            self,
            frames: List[bytes],
            sample_rate: int,
            on_complete: Callable[[str], None],
            on_error: Callable[[str], None]
    ):
        """音声フレームを文字起こし処理（別スレッドで実行）"""
        try:
            logging.info("音声フレーム処理開始")

            if self.cancel_processing:
                logging.info("処理がキャンセルされました")
                return

            temp_audio_file = save_audio(frames, sample_rate, self.config)
            if not temp_audio_file:
                raise ValueError("音声ファイルの保存に失敗しました")

            if self.cancel_processing:
                logging.info("処理がキャンセルされました")
                return

            logging.info("文字起こし開始")
            transcription = self.transcribe_audio_func(
                temp_audio_file,
                self.config,
                self.client
            )

            if not transcription:
                raise ValueError("音声ファイルの文字起こしに失敗しました")

            logging.debug(f"句読点処理開始: use_punctuation={self.use_punctuation}")
            transcription = process_punctuation(transcription, self.use_punctuation)
            logging.debug("句読点処理完了")

            if self.cancel_processing:
                logging.info("処理がキャンセルされました")
                return

            logging.debug("UI更新をスケジュール")
            try:
                self.master.after(0, on_complete, transcription)
            except Exception:
                pass
            logging.debug("UI更新スケジュール完了")

        except Exception as e:
            logging.error(f"文字起こし処理中にエラー: {str(e)}")
            logging.debug(f"詳細: {traceback.format_exc()}")
            try:
                self.master.after(0, on_error, str(e))
            except Exception:
                pass

    def handle_audio_file(
            self,
            file_path: str,
            on_complete: Callable[[str], None],
            on_error: Callable[[str], None]
    ):
        """音声ファイルを処理"""
        try:
            transcription = self.transcribe_audio_func(
                file_path,
                self.config,
                self.client
            )
            if transcription:
                transcription = process_punctuation(transcription, self.use_punctuation)
                on_complete(transcription)
            else:
                raise ValueError('音声ファイルの処理に失敗しました')
        except Exception as e:
            on_error(str(e))

    def copy_and_paste(self, text: str):
        """UI スレッドから呼び出される。新しいスレッドで貼り付け処理を実行"""
        try:
            logging.debug(f"copy_and_paste開始: text長={len(text)}")

            if self.ui_processor.is_shutting_down:
                logging.info("シャットダウン中のためcopy_and_pasteをスキップ")
                return

            if not self.ui_processor.is_ui_valid():
                logging.warning("UIが無効なためcopy_and_pasteをスキップ")
                return

            thread = threading.Thread(
                target=self._safe_copy_and_paste,
                args=(text,),
                daemon=True,
                name="CopyPasteThread"
            )
            thread.start()
            logging.debug("CopyPasteThreadを開始しました")

        except RuntimeError as e:
            logging.error(f"スレッド作成中にRuntimeError: {str(e)}")
        except Exception as e:
            logging.error(f"コピー&ペースト開始中にエラー: {str(e)}")
            logging.debug(f"詳細: {traceback.format_exc()}")

    def _safe_copy_and_paste(self, text: str):
        """バックグラウンドスレッドで実行される貼り付け処理"""
        try:
            logging.debug("_safe_copy_and_paste開始")

            if self.ui_processor.is_shutting_down:
                logging.info("シャットダウン中のため_safe_copy_and_pasteを中断")
                return

            copy_and_paste_transcription(text, self.replacements, self.config)
            logging.debug("_safe_copy_and_paste完了")

        except RuntimeError as e:
            logging.error(f"_safe_copy_and_paste RuntimeError: {str(e)}")
            logging.debug(f"詳細: {traceback.format_exc()}")
        except OSError as e:
            logging.error(f"_safe_copy_and_paste OSError: {str(e)}")
            logging.debug(f"詳細: {traceback.format_exc()}")
        except Exception as e:
            logging.error(f"コピー&ペースト実行中にエラー: {type(e).__name__}: {str(e)}")
            logging.debug(f"詳細: {traceback.format_exc()}")
            if not self.ui_processor.is_shutting_down:
                self.ui_processor.schedule_callback(
                    self._error_callback,
                    f"コピー&ペースト中にエラー: {str(e)}"
                )

    def set_error_callback(self, callback: Callable[[str], None]):
        """エラーコールバックを設定"""
        self._error_callback = callback

    def wait_for_processing(self, timeout: float = 5.0) -> bool:
        """処理スレッドの完了を待機"""
        if self.processing_thread and self.processing_thread.is_alive():
            logging.info("処理スレッドの完了を待機中...")
            self.processing_thread.join(timeout=timeout)
            return not self.processing_thread.is_alive()
        return True

    def cancel(self):
        """処理をキャンセル"""
        self.cancel_processing = True

    def reset_cancel(self):
        """キャンセルフラグをリセット"""
        self.cancel_processing = False
