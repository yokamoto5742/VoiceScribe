import configparser
import threading
import time
from unittest.mock import Mock, patch

import pytest
import tkinter as tk

from service.transcription_handler import TranscriptionHandler
from service.ui_queue_processor import UIQueueProcessor


class TestTranscriptionHandlerInit:
    """TranscriptionHandler初期化のテストクラス"""

    def setup_method(self):
        """各テストメソッドの前に実行される設定"""
        self.mock_master = Mock(spec=tk.Tk)
        self.mock_master.winfo_exists.return_value = True

        self.mock_config = configparser.ConfigParser()
        self.mock_config['ELEVENLABS'] = {
            'MODEL': 'scribe_v2',
            'LANGUAGE': 'jpn'
        }

        self.mock_client = Mock()
        self.replacements = {"テスト": "試験"}
        self.mock_ui_processor = Mock(spec=UIQueueProcessor)
        self.mock_ui_processor.is_ui_valid.return_value = True

    def test_init_success(self):
        """正常系: TranscriptionHandlerの正常初期化"""
        handler = TranscriptionHandler(
            self.mock_master,
            self.mock_config,
            self.mock_client,
            self.replacements,
            self.mock_ui_processor,
            use_punctuation=True
        )

        assert handler.master == self.mock_master
        assert handler.config == self.mock_config
        assert handler.client == self.mock_client
        assert handler.replacements == self.replacements
        assert handler.ui_processor == self.mock_ui_processor
        assert handler.use_punctuation is True
        assert handler.cancel_processing is False
        assert handler.processing_thread is None

    def test_init_with_punctuation_false(self):
        """正常系: 句読点処理なしで初期化"""
        handler = TranscriptionHandler(
            self.mock_master,
            self.mock_config,
            self.mock_client,
            self.replacements,
            self.mock_ui_processor,
            use_punctuation=False
        )

        assert handler.use_punctuation is False


class TestTranscriptionHandlerTranscribeFrames:
    """TranscriptionHandlerのtranscribe_frames()メソッドのテストクラス"""

    def setup_method(self):
        """各テストメソッドの前に実行される設定"""
        self.mock_master = Mock(spec=tk.Tk)
        self.mock_master.winfo_exists.return_value = True

        self.mock_config = configparser.ConfigParser()
        self.mock_config['ELEVENLABS'] = {
            'MODEL': 'scribe_v2',
            'LANGUAGE': 'jpn'
        }
        self.mock_config['PATHS'] = {'TEMP_DIR': '/test/temp'}

        self.mock_client = Mock()
        self.replacements = {}
        self.mock_ui_processor = Mock(spec=UIQueueProcessor)
        self.mock_ui_processor.is_ui_valid.return_value = True

        self.handler = TranscriptionHandler(
            self.mock_master,
            self.mock_config,
            self.mock_client,
            self.replacements,
            self.mock_ui_processor,
            use_punctuation=False
        )

        self.mock_on_complete = Mock()
        self.mock_on_error = Mock()

    @patch('service.transcription_handler.save_audio')
    @patch('service.transcription_handler.process_punctuation')
    def test_transcribe_frames_success(self, mock_process_punct, mock_save_audio):
        """正常系: 音声フレームの文字起こし成功"""
        frames = [b'audio_data_1', b'audio_data_2']
        sample_rate = 16000
        mock_save_audio.return_value = '/test/temp/audio.wav'
        mock_process_punct.return_value = "文字起こし結果"

        self.handler.transcribe_audio_func = Mock(return_value="文字起こし結果")

        self.handler.transcribe_frames(
            frames,
            sample_rate,
            self.mock_on_complete,
            self.mock_on_error
        )

        mock_save_audio.assert_called_once_with(frames, sample_rate, self.mock_config)
        self.handler.transcribe_audio_func.assert_called_once_with(
            '/test/temp/audio.wav',
            self.mock_config,
            self.mock_client
        )
        mock_process_punct.assert_called_once_with("文字起こし結果", False)
        self.mock_master.after.assert_called_once_with(0, self.mock_on_complete, "文字起こし結果")

    @patch('service.transcription_handler.save_audio')
    def test_transcribe_frames_save_audio_fails(self, mock_save_audio):
        """異常系: 音声ファイル保存失敗"""
        frames = [b'audio_data']
        mock_save_audio.return_value = None

        self.handler.transcribe_frames(
            frames,
            16000,
            self.mock_on_complete,
            self.mock_on_error
        )

        self.mock_master.after.assert_called_once()
        args = self.mock_master.after.call_args[0]
        assert args[0] == 0
        assert args[1] == self.mock_on_error
        assert "音声ファイルの保存に失敗しました" in args[2]

    @patch('service.transcription_handler.save_audio')
    def test_transcribe_frames_transcription_fails(self, mock_save_audio):
        """異常系: 文字起こし失敗"""
        frames = [b'audio_data']
        mock_save_audio.return_value = '/test/temp/audio.wav'
        self.handler.transcribe_audio_func = Mock(return_value=None)

        self.handler.transcribe_frames(
            frames,
            16000,
            self.mock_on_complete,
            self.mock_on_error
        )

        self.mock_master.after.assert_called_once()
        args = self.mock_master.after.call_args[0]
        assert args[0] == 0
        assert args[1] == self.mock_on_error
        assert "音声ファイルの文字起こしに失敗しました" in args[2]

    @patch('service.transcription_handler.save_audio')
    def test_transcribe_frames_cancelled_before_save(self, mock_save_audio):
        """異常系: 保存前にキャンセル"""
        frames = [b'audio_data']
        self.handler.cancel_processing = True

        self.handler.transcribe_frames(
            frames,
            16000,
            self.mock_on_complete,
            self.mock_on_error
        )

        mock_save_audio.assert_not_called()
        self.mock_master.after.assert_not_called()

    @patch('service.transcription_handler.save_audio')
    def test_transcribe_frames_cancelled_after_save(self, mock_save_audio):
        """異常系: 保存後にキャンセル"""
        frames = [b'audio_data']
        mock_save_audio.return_value = '/test/temp/audio.wav'

        # transcribe_audio_funcがNoneを返す場合、エラーコールバックが呼ばれる
        self.handler.transcribe_audio_func = Mock(return_value=None)
        self.handler.cancel_processing = True

        self.handler.transcribe_frames(
            frames,
            16000,
            self.mock_on_complete,
            self.mock_on_error
        )

        # cancel_processingがTrueなので、最初のチェックで処理が中断される
        mock_save_audio.assert_not_called()
        self.mock_master.after.assert_not_called()

    @patch('service.transcription_handler.process_punctuation')
    @patch('service.transcription_handler.save_audio')
    def test_transcribe_frames_cancelled_before_ui_update(self, mock_save_audio, mock_process_punct):
        """異常系: UI更新前にキャンセル"""
        frames = [b'audio_data']
        mock_save_audio.return_value = '/test/temp/audio.wav'
        mock_process_punct.return_value = "結果"
        self.handler.transcribe_audio_func = Mock(return_value="結果")

        def cancel_after_transcribe(*args):
            self.handler.cancel_processing = True

        self.handler.transcribe_audio_func.side_effect = lambda *args: (
            cancel_after_transcribe(args),
            "結果"
        )[1]

        self.handler.transcribe_frames(
            frames,
            16000,
            self.mock_on_complete,
            self.mock_on_error
        )

        # キャンセルされても結果は返されない
        self.mock_master.after.assert_not_called()

    @patch('service.transcription_handler.save_audio')
    def test_transcribe_frames_with_exception(self, mock_save_audio):
        """異常系: 処理中に例外発生"""
        frames = [b'audio_data']
        mock_save_audio.side_effect = Exception("保存エラー")

        self.handler.transcribe_frames(
            frames,
            16000,
            self.mock_on_complete,
            self.mock_on_error
        )

        self.mock_master.after.assert_called_once()
        args = self.mock_master.after.call_args[0]
        assert args[0] == 0
        assert args[1] == self.mock_on_error

    @patch('service.transcription_handler.save_audio')
    def test_transcribe_frames_master_after_fails(self, mock_save_audio):
        """異常系: master.afterが失敗"""
        frames = [b'audio_data']
        mock_save_audio.return_value = '/test/temp/audio.wav'
        self.handler.transcribe_audio_func = Mock(return_value="結果")
        self.mock_master.after.side_effect = Exception("after error")

        self.handler.transcribe_frames(
            frames,
            16000,
            self.mock_on_complete,
            self.mock_on_error
        )

        # 例外が発生しても処理は続行


class TestTranscriptionHandlerHandleAudioFile:
    """TranscriptionHandlerのhandle_audio_file()メソッドのテストクラス"""

    def setup_method(self):
        """各テストメソッドの前に実行される設定"""
        self.mock_master = Mock(spec=tk.Tk)
        self.mock_config = configparser.ConfigParser()
        self.mock_client = Mock()
        self.mock_ui_processor = Mock(spec=UIQueueProcessor)

        self.handler = TranscriptionHandler(
            self.mock_master,
            self.mock_config,
            self.mock_client,
            {},
            self.mock_ui_processor,
            use_punctuation=False
        )

        self.mock_on_complete = Mock()
        self.mock_on_error = Mock()

    @patch('service.transcription_handler.process_punctuation')
    def test_handle_audio_file_success(self, mock_process_punct):
        """正常系: 音声ファイル処理成功"""
        self.handler.transcribe_audio_func = Mock(return_value="文字起こし結果")
        mock_process_punct.return_value = "処理済み結果"

        self.handler.handle_audio_file(
            '/test/audio.wav',
            self.mock_on_complete,
            self.mock_on_error
        )

        self.handler.transcribe_audio_func.assert_called_once_with(
            '/test/audio.wav',
            self.mock_config,
            self.mock_client
        )
        mock_process_punct.assert_called_once_with("文字起こし結果", False)
        self.mock_on_complete.assert_called_once_with("処理済み結果")

    def test_handle_audio_file_transcription_fails(self):
        """異常系: 文字起こし失敗"""
        self.handler.transcribe_audio_func = Mock(return_value=None)

        self.handler.handle_audio_file(
            '/test/audio.wav',
            self.mock_on_complete,
            self.mock_on_error
        )

        self.mock_on_error.assert_called_once_with('音声ファイルの処理に失敗しました')

    def test_handle_audio_file_with_exception(self):
        """異常系: 処理中に例外発生"""
        self.handler.transcribe_audio_func = Mock(side_effect=Exception("処理エラー"))

        self.handler.handle_audio_file(
            '/test/audio.wav',
            self.mock_on_complete,
            self.mock_on_error
        )

        self.mock_on_error.assert_called_once_with('処理エラー')


class TestTranscriptionHandlerCopyAndPaste:
    """TranscriptionHandlerのcopy_and_paste()メソッドのテストクラス"""

    def setup_method(self):
        """各テストメソッドの前に実行される設定"""
        self.mock_master = Mock(spec=tk.Tk)
        self.mock_config = configparser.ConfigParser()
        self.mock_client = Mock()
        self.mock_ui_processor = Mock(spec=UIQueueProcessor)
        self.mock_ui_processor.is_shutting_down = False
        self.mock_ui_processor.is_ui_valid.return_value = True

        self.handler = TranscriptionHandler(
            self.mock_master,
            self.mock_config,
            self.mock_client,
            {},
            self.mock_ui_processor,
            use_punctuation=False
        )

    @patch('threading.Thread')
    def test_copy_and_paste_starts_thread(self, mock_thread):
        """正常系: コピー&ペーストスレッド開始"""
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        self.handler.copy_and_paste("テキスト")

        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()

    def test_copy_and_paste_when_shutting_down(self):
        """異常系: シャットダウン中は処理しない"""
        self.mock_ui_processor.is_shutting_down = True

        with patch('threading.Thread') as mock_thread:
            self.handler.copy_and_paste("テキスト")

            mock_thread.assert_not_called()

    def test_copy_and_paste_when_ui_invalid(self):
        """異常系: UI無効時は処理しない"""
        self.mock_ui_processor.is_ui_valid.return_value = False

        with patch('threading.Thread') as mock_thread:
            self.handler.copy_and_paste("テキスト")

            mock_thread.assert_not_called()

    @patch('threading.Thread', side_effect=RuntimeError("thread error"))
    def test_copy_and_paste_thread_creation_fails(self, mock_thread):
        """異常系: スレッド作成失敗"""
        self.handler.copy_and_paste("テキスト")

        # エラーをログに記録するが例外は発生しない

    @patch('threading.Thread', side_effect=Exception("unexpected error"))
    def test_copy_and_paste_unexpected_exception(self, mock_thread):
        """異常系: 予期しない例外"""
        self.handler.copy_and_paste("テキスト")

        # エラーをログに記録するが例外は発生しない


class TestTranscriptionHandlerSafeCopyAndPaste:
    """TranscriptionHandlerの_safe_copy_and_paste()メソッドのテストクラス"""

    def setup_method(self):
        """各テストメソッドの前に実行される設定"""
        self.mock_master = Mock(spec=tk.Tk)
        self.mock_config = configparser.ConfigParser()
        self.mock_client = Mock()
        self.mock_ui_processor = Mock(spec=UIQueueProcessor)
        self.mock_ui_processor.is_shutting_down = False

        self.handler = TranscriptionHandler(
            self.mock_master,
            self.mock_config,
            self.mock_client,
            {"テスト": "試験"},
            self.mock_ui_processor,
            use_punctuation=False
        )

    @patch('service.transcription_handler.copy_and_paste_transcription')
    def test_safe_copy_and_paste_success(self, mock_copy_paste):
        """正常系: コピー&ペースト成功"""
        self.handler._safe_copy_and_paste("テキスト")

        mock_copy_paste.assert_called_once_with("テキスト", {"テスト": "試験"}, self.mock_config)

    @patch('service.transcription_handler.copy_and_paste_transcription')
    def test_safe_copy_and_paste_when_shutting_down(self, mock_copy_paste):
        """異常系: シャットダウン中は中断"""
        self.mock_ui_processor.is_shutting_down = True

        self.handler._safe_copy_and_paste("テキスト")

        mock_copy_paste.assert_not_called()

    @patch('service.transcription_handler.copy_and_paste_transcription', side_effect=RuntimeError("runtime error"))
    def test_safe_copy_and_paste_runtime_error(self, mock_copy_paste):
        """異常系: RuntimeError発生"""
        self.handler._safe_copy_and_paste("テキスト")

        # エラーをログに記録するが例外は発生しない

    @patch('service.transcription_handler.copy_and_paste_transcription', side_effect=OSError("os error"))
    def test_safe_copy_and_paste_os_error(self, mock_copy_paste):
        """異常系: OSError発生"""
        self.handler._safe_copy_and_paste("テキスト")

        # エラーをログに記録するが例外は発生しない

    @patch('service.transcription_handler.copy_and_paste_transcription', side_effect=Exception("general error"))
    def test_safe_copy_and_paste_general_exception(self, mock_copy_paste):
        """異常系: 一般的な例外発生"""
        self.handler.set_error_callback(Mock())

        self.handler._safe_copy_and_paste("テキスト")

        # エラーコールバックがスケジュールされる
        self.mock_ui_processor.schedule_callback.assert_called_once()

    @patch('service.transcription_handler.copy_and_paste_transcription', side_effect=Exception("error"))
    def test_safe_copy_and_paste_exception_while_shutting_down(self, mock_copy_paste):
        """異常系: シャットダウン中に例外発生"""
        self.mock_ui_processor.is_shutting_down = True
        self.handler.set_error_callback(Mock())

        self.handler._safe_copy_and_paste("テキスト")

        # シャットダウン中はエラーコールバックをスケジュールしない
        self.mock_ui_processor.schedule_callback.assert_not_called()


class TestTranscriptionHandlerSetErrorCallback:
    """TranscriptionHandlerのset_error_callback()メソッドのテストクラス"""

    def test_set_error_callback(self):
        """正常系: エラーコールバック設定"""
        mock_master = Mock(spec=tk.Tk)
        mock_config = configparser.ConfigParser()
        mock_ui_processor = Mock(spec=UIQueueProcessor)

        handler = TranscriptionHandler(
            mock_master,
            mock_config,
            Mock(),
            {},
            mock_ui_processor,
            use_punctuation=False
        )

        mock_callback = Mock()
        handler.set_error_callback(mock_callback)

        assert handler._error_callback == mock_callback


class TestTranscriptionHandlerWaitForProcessing:
    """TranscriptionHandlerのwait_for_processing()メソッドのテストクラス"""

    def setup_method(self):
        """各テストメソッドの前に実行される設定"""
        self.mock_master = Mock(spec=tk.Tk)
        self.mock_config = configparser.ConfigParser()
        self.mock_ui_processor = Mock(spec=UIQueueProcessor)

        self.handler = TranscriptionHandler(
            self.mock_master,
            self.mock_config,
            Mock(),
            {},
            self.mock_ui_processor,
            use_punctuation=False
        )

    def test_wait_for_processing_no_thread(self):
        """正常系: 処理スレッドなし"""
        result = self.handler.wait_for_processing()

        assert result is True

    def test_wait_for_processing_thread_completes(self):
        """正常系: 処理スレッドが完了"""
        mock_thread = Mock()
        mock_thread.is_alive.return_value = False
        self.handler.processing_thread = mock_thread

        result = self.handler.wait_for_processing()

        assert result is True
        mock_thread.join.assert_not_called()

    def test_wait_for_processing_thread_alive(self):
        """正常系: 処理スレッドが実行中"""
        mock_thread = Mock()
        mock_thread.is_alive.side_effect = [True, False]
        self.handler.processing_thread = mock_thread

        result = self.handler.wait_for_processing(timeout=1.0)

        mock_thread.join.assert_called_once_with(timeout=1.0)
        assert result is True

    def test_wait_for_processing_timeout(self):
        """異常系: タイムアウト"""
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        self.handler.processing_thread = mock_thread

        result = self.handler.wait_for_processing(timeout=0.1)

        mock_thread.join.assert_called_once_with(timeout=0.1)
        assert result is False


class TestTranscriptionHandlerCancelAndReset:
    """TranscriptionHandlerのcancel()とreset_cancel()のテストクラス"""

    def test_cancel(self):
        """正常系: 処理をキャンセル"""
        mock_master = Mock(spec=tk.Tk)
        mock_config = configparser.ConfigParser()
        mock_ui_processor = Mock(spec=UIQueueProcessor)

        handler = TranscriptionHandler(
            mock_master,
            mock_config,
            Mock(),
            {},
            mock_ui_processor,
            use_punctuation=False
        )

        assert handler.cancel_processing is False

        handler.cancel()

        assert handler.cancel_processing is True

    def test_reset_cancel(self):
        """正常系: キャンセルフラグをリセット"""
        mock_master = Mock(spec=tk.Tk)
        mock_config = configparser.ConfigParser()
        mock_ui_processor = Mock(spec=UIQueueProcessor)

        handler = TranscriptionHandler(
            mock_master,
            mock_config,
            Mock(),
            {},
            mock_ui_processor,
            use_punctuation=False
        )

        handler.cancel_processing = True
        handler.reset_cancel()

        assert handler.cancel_processing is False
