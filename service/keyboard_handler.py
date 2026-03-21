import logging
import tkinter as tk
from typing import Callable
import keyboard

from utils.app_config import AppConfig


class KeyboardHandler:
    def __init__(
            self,
            master: tk.Tk,
            config: AppConfig,
            toggle_recording_callback: Callable,
            toggle_punctuation_callback: Callable,
            reload_audio_callback: Callable,
            close_application_callback: Callable,
    ):
        self.master = master
        self.config = config
        self._toggle_recording = toggle_recording_callback
        self._toggle_punctuation = toggle_punctuation_callback
        self._reload_audio = reload_audio_callback
        self._close_application = close_application_callback
        self.setup_keyboard_listeners()

    def setup_keyboard_listeners(self):
        try:
            keyboard.on_press_key(
                self.config.toggle_recording_key,
                self._handle_toggle_recording_key
            )

            keyboard.on_press_key(
                self.config.exit_app_key,
                self._handle_exit_key
            )

            keyboard.on_press_key(
                self.config.toggle_punctuation_key,
                self._handle_toggle_punctuation_key
            )

            keyboard.on_press_key(
                self.config.reload_audio_key,
                self._handle_reload_audio_key
            )

        except Exception as e:
            logging.error(f'キーボードリスナーの設定中にエラーが発生しました: {str(e)}')
            raise

    def _handle_toggle_recording_key(self, _: keyboard.KeyboardEvent):
        try:
            self.master.after(0, self._toggle_recording)
        except Exception as e:
            logging.error(f"録音トグルキー処理中にエラー: {e}")

    def _handle_exit_key(self, _: keyboard.KeyboardEvent):
        try:
            self.master.after(0, self._close_application)
        except Exception as e:
            logging.error(f"終了キー処理中にエラー: {e}")

    def _handle_toggle_punctuation_key(self, _: keyboard.KeyboardEvent):
        try:
            self.master.after(0, self._toggle_punctuation)
        except Exception as e:
            logging.error(f"句読点トグルキー処理中にエラー: {e}")

    def _handle_reload_audio_key(self, _: keyboard.KeyboardEvent):
        try:
            self.master.after(0, self._reload_audio)
        except Exception as e:
            logging.error(f"音声リロードキー処理中にエラー: {e}")

    @staticmethod
    def cleanup():
        try:
            keyboard.unhook_all()
        except Exception as e:
            logging.error(f'キーボードリスナーの解放中にエラーが発生しました: {str(e)}')
