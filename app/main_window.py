import logging
import sys
import time
import tkinter as tk

from app.notification_manager import NotificationManager
from app.ui_components import UIComponents
from service.keyboard_handler import KeyboardHandler
from service.recording_lifecycle import RecordingLifecycle
from utils.app_config import AppConfig
from utils.config_manager import save_config


class VoiceInputManager:
    def __init__(
            self,
            master: tk.Tk,
            config: AppConfig,
            recording_lifecycle: RecordingLifecycle,
            notification_manager: NotificationManager,
            version: str
    ):
        self.master = master
        self.config = config
        self.version = version
        self.notification_manager = notification_manager
        self.recording_lifecycle = recording_lifecycle

        self.ui_components = UIComponents(master, config, {
            'toggle_recording': self.toggle_recording,
            'toggle_punctuation': self.toggle_punctuation,
            'reload_audio': lambda: None,
        })
        self.ui_components.setup_ui(version)

        self.ui_components.update_callbacks({
            'toggle_recording': self.toggle_recording,
            'toggle_punctuation': self.toggle_punctuation,
            'reload_audio': self.ui_components.reload_latest_audio,
        })

        recording_lifecycle.wire_ui_callbacks(
            update_record_button=self.ui_components.update_record_button,
            update_status_label=self.ui_components.update_status_label,
        )

        self.keyboard_handler = KeyboardHandler(
            master,
            config,
            self.toggle_recording,
            self.toggle_punctuation,
            self.ui_components.reload_latest_audio,
            self.close_application,
        )

        self.master.bind('<<LoadAudioFile>>', recording_lifecycle.handle_audio_file)

        if config.start_minimized:
            self.master.iconify()

    def toggle_recording(self) -> None:
        self.recording_lifecycle.toggle_recording()

    def toggle_punctuation(self) -> None:
        use_punctuation = not self.recording_lifecycle.use_punctuation
        self.recording_lifecycle.use_punctuation = use_punctuation
        self.ui_components.update_punctuation_button(use_punctuation)
        logging.info(f"現在句読点: {'あり' if use_punctuation else 'なし'}")
        self.config.use_punctuation = use_punctuation
        self.config.use_comma = use_punctuation
        save_config(self.config.raw_config)

    def close_application(self) -> None:
        try:
            if self.recording_lifecycle:
                self.recording_lifecycle.cleanup()
            if self.keyboard_handler:
                self.keyboard_handler.cleanup()
            if self.notification_manager:
                self.notification_manager.cleanup()
            time.sleep(0.1)
            self.master.quit()

        except Exception as e:
            logging.error(f'アプリケーション終了処理中にエラー: {str(e)}')
            sys.exit(1)
