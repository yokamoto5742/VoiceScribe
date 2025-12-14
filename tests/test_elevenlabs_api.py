import configparser
import os
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

from external_service.elevenlabs_api import (
    convert_response_to_text,
    setup_elevenlabs_client,
    transcribe_audio,
    validate_audio_file,
)


class TestSetupElevenLabsClient:
    """ElevenLabsクライアント設定のテストクラス"""

    @patch('external_service.elevenlabs_api.load_env_variables')
    @patch('external_service.elevenlabs_api.ElevenLabs')
    def test_setup_client_success(self, mock_elevenlabs, mock_load_env):
        """正常系: APIキーが設定されている場合"""
        mock_load_env.return_value = {"ELEVENLABS_API_KEY": "test_api_key"}
        mock_client = Mock()
        mock_elevenlabs.return_value = mock_client

        result = setup_elevenlabs_client()

        assert result == mock_client
        mock_elevenlabs.assert_called_once_with(api_key="test_api_key")

    @patch('external_service.elevenlabs_api.load_env_variables')
    def test_setup_client_no_api_key(self, mock_load_env):
        """異常系: APIキーが未設定の場合"""
        mock_load_env.return_value = {}

        with pytest.raises(ValueError, match="ELEVENLABS_API_KEYが未設定です"):
            setup_elevenlabs_client()

    @patch('external_service.elevenlabs_api.load_env_variables')
    def test_setup_client_empty_api_key(self, mock_load_env):
        """異常系: APIキーが空文字列の場合"""
        mock_load_env.return_value = {"ELEVENLABS_API_KEY": ""}

        with pytest.raises(ValueError, match="ELEVENLABS_API_KEYが未設定です"):
            setup_elevenlabs_client()


class TestValidateAudioFile:
    """音声ファイル検証のテストクラス"""

    def test_validate_empty_path(self):
        """異常系: ファイルパスが空文字列"""
        is_valid, error_msg = validate_audio_file("")

        assert is_valid is False
        assert error_msg == "音声ファイルパスが未指定です"

    def test_validate_none_path(self):
        """異常系: ファイルパスがNone"""
        is_valid, error_msg = validate_audio_file(None)

        assert is_valid is False
        assert error_msg == "音声ファイルパスが未指定です"

    @patch('external_service.elevenlabs_api.os.path.exists')
    def test_validate_file_not_exists(self, mock_exists):
        """異常系: ファイルが存在しない"""
        mock_exists.return_value = False
        file_path = "/test/path/audio.wav"

        is_valid, error_msg = validate_audio_file(file_path)

        assert is_valid is False
        assert error_msg == f"音声ファイルが存在しません: {file_path}"

    @patch('external_service.elevenlabs_api.os.path.getsize')
    @patch('external_service.elevenlabs_api.os.path.exists')
    def test_validate_zero_size_file(self, mock_exists, mock_getsize):
        """異常系: ファイルサイズが0バイト"""
        mock_exists.return_value = True
        mock_getsize.return_value = 0

        is_valid, error_msg = validate_audio_file("/test/audio.wav")

        assert is_valid is False
        assert error_msg == "音声ファイルサイズが0バイトです"

    @patch('external_service.elevenlabs_api.os.path.getsize')
    @patch('external_service.elevenlabs_api.os.path.exists')
    def test_validate_success(self, mock_exists, mock_getsize):
        """正常系: 有効なファイル"""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        is_valid, error_msg = validate_audio_file("/test/audio.wav")

        assert is_valid is True
        assert error_msg is None


class TestConvertResponseToText:
    """APIレスポンス変換のテストクラス"""

    def test_convert_none_response(self):
        """異常系: レスポンスがNone"""
        result = convert_response_to_text(None)
        assert result is None

    def test_convert_string_response(self):
        """正常系: 文字列レスポンス"""
        result = convert_response_to_text("テスト文字列")
        assert result == "テスト文字列"

    def test_convert_object_with_text_attribute(self):
        """正常系: textアトリビュートを持つオブジェクト"""
        mock_response = Mock()
        mock_response.text = "文字起こし結果"

        result = convert_response_to_text(mock_response)
        assert result == "文字起こし結果"

    def test_convert_object_with_none_text(self):
        """異常系: textがNoneのオブジェクト"""
        mock_response = Mock()
        mock_response.text = None

        result = convert_response_to_text(mock_response)
        # textがNoneの場合、hasattr(response, '__str__')でTrueになり、str(response)が呼ばれる
        assert result is not None

    def test_convert_object_with_str_method(self):
        """正常系: __str__メソッドを持つオブジェクト"""
        class CustomResponse:
            def __str__(self):
                return "カスタムレスポンス"

        result = convert_response_to_text(CustomResponse())
        assert result == "カスタムレスポンス"

    def test_convert_invalid_response_type(self):
        """異常系: 予期しないレスポンス形式"""
        # Mockオブジェクトは常に__str__を持つため、str()が呼ばれる
        # textアトリビュートがない場合のテスト
        mock_response = Mock(spec=['other_attribute'])

        result = convert_response_to_text(mock_response)
        # str(mock_response)が呼ばれるため、結果は文字列になる
        assert result is not None

    def test_convert_exception_during_conversion(self):
        """異常系: 変換中に例外が発生"""
        # textプロパティにアクセスすると例外が発生するケース
        mock_response = Mock()
        type(mock_response).text = property(lambda self: 1/0)

        result = convert_response_to_text(mock_response)
        assert result is None


class TestTranscribeAudio:
    """音声文字起こしのテストクラス"""

    def setup_method(self):
        """各テストメソッドの前に実行される設定"""
        self.mock_config = configparser.ConfigParser()
        self.mock_config['ELEVENLABS'] = {
            'MODEL': 'scribe_v2',
            'LANGUAGE': 'jpn'
        }
        self.mock_client = Mock()

    def test_transcribe_empty_file_path(self):
        """異常系: ファイルパスが空"""
        result = transcribe_audio("", self.mock_config, self.mock_client)
        assert result is None

    @patch('external_service.elevenlabs_api.os.path.exists')
    def test_transcribe_file_not_exists(self, mock_exists):
        """異常系: ファイルが存在しない"""
        mock_exists.return_value = False

        result = transcribe_audio("/test/nonexistent.wav", self.mock_config, self.mock_client)
        assert result is None

    @patch('external_service.elevenlabs_api.os.path.getsize')
    @patch('external_service.elevenlabs_api.os.path.exists')
    def test_transcribe_zero_size_file(self, mock_exists, mock_getsize):
        """異常系: ファイルサイズが0バイト"""
        mock_exists.return_value = True
        mock_getsize.return_value = 0

        result = transcribe_audio("/test/empty.wav", self.mock_config, self.mock_client)
        assert result is None

    @patch('builtins.open', new_callable=mock_open, read_data=b'audio_data')
    @patch('external_service.elevenlabs_api.os.path.getsize')
    @patch('external_service.elevenlabs_api.os.path.exists')
    def test_transcribe_success(self, mock_exists, mock_getsize, mock_file):
        """正常系: 文字起こし成功"""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        mock_response = Mock()
        mock_response.text = "文字起こし結果"
        self.mock_client.speech_to_text.convert.return_value = mock_response

        result = transcribe_audio("/test/audio.wav", self.mock_config, self.mock_client)

        assert result == "文字起こし結果"
        self.mock_client.speech_to_text.convert.assert_called_once()

    @patch('builtins.open', new_callable=mock_open, read_data=b'audio_data')
    @patch('external_service.elevenlabs_api.os.path.getsize')
    @patch('external_service.elevenlabs_api.os.path.exists')
    def test_transcribe_empty_result(self, mock_exists, mock_getsize, mock_file):
        """正常系: 文字起こし結果が空文字列"""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        mock_response = Mock()
        mock_response.text = ""
        self.mock_client.speech_to_text.convert.return_value = mock_response

        result = transcribe_audio("/test/audio.wav", self.mock_config, self.mock_client)

        assert result == ""

    @patch('builtins.open', new_callable=mock_open, read_data=b'audio_data')
    @patch('external_service.elevenlabs_api.os.path.getsize')
    @patch('external_service.elevenlabs_api.os.path.exists')
    def test_transcribe_api_returns_none(self, mock_exists, mock_getsize, mock_file):
        """異常系: APIがNoneを返す"""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024
        self.mock_client.speech_to_text.convert.return_value = None

        result = transcribe_audio("/test/audio.wav", self.mock_config, self.mock_client)

        assert result is None

    @patch('builtins.open', side_effect=FileNotFoundError("ファイルが見つかりません"))
    @patch('external_service.elevenlabs_api.os.path.getsize')
    @patch('external_service.elevenlabs_api.os.path.exists')
    def test_transcribe_file_not_found_error(self, mock_exists, mock_getsize, mock_file):
        """異常系: ファイル読み込みでFileNotFoundError"""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        result = transcribe_audio("/test/audio.wav", self.mock_config, self.mock_client)

        assert result is None

    @patch('builtins.open', side_effect=PermissionError("アクセス拒否"))
    @patch('external_service.elevenlabs_api.os.path.getsize')
    @patch('external_service.elevenlabs_api.os.path.exists')
    def test_transcribe_permission_error(self, mock_exists, mock_getsize, mock_file):
        """異常系: ファイル読み込みでPermissionError"""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        result = transcribe_audio("/test/audio.wav", self.mock_config, self.mock_client)

        assert result is None

    @patch('builtins.open', side_effect=OSError("OS関連エラー"))
    @patch('external_service.elevenlabs_api.os.path.getsize')
    @patch('external_service.elevenlabs_api.os.path.exists')
    def test_transcribe_os_error(self, mock_exists, mock_getsize, mock_file):
        """異常系: ファイル読み込みでOSError"""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        result = transcribe_audio("/test/audio.wav", self.mock_config, self.mock_client)

        assert result is None

    @patch('builtins.open', new_callable=mock_open, read_data=b'audio_data')
    @patch('external_service.elevenlabs_api.os.path.getsize')
    @patch('external_service.elevenlabs_api.os.path.exists')
    def test_transcribe_api_exception(self, mock_exists, mock_getsize, mock_file):
        """異常系: API呼び出しで例外発生"""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024
        self.mock_client.speech_to_text.convert.side_effect = Exception("API エラー")

        result = transcribe_audio("/test/audio.wav", self.mock_config, self.mock_client)

        assert result is None
