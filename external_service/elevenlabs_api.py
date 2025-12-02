import logging
import os
import traceback
from typing import Optional

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()


def setup_elevenlabs_client() -> ElevenLabs:
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEYの環境変数が未設定です")
    return ElevenLabs(api_key=api_key)


def transcribe_audio(
        audio_file_path: str,
        use_punctuation: bool,
        use_comma: bool,
        config: dict,
        client: ElevenLabs
) -> Optional[str]:
    if not audio_file_path:
        logging.warning("音声ファイルパスが未指定")
        return None

    try:
        logging.info("文字起こし開始")

        if not os.path.exists(audio_file_path):
            logging.error(f"音声ファイルが存在しません: {audio_file_path}")
            return None

        file_size = os.path.getsize(audio_file_path)
        logging.info(f"音声ファイルサイズ: {file_size} bytes")

        if file_size == 0:
            logging.error("音声ファイルのサイズが0バイトです")
            return None

        logging.info("ファイル読み込み開始")
        with open(audio_file_path, "rb") as file:
            logging.info(f"ファイル読み込み完了")

            transcription = client.speech_to_text.convert(
                file=file,
                model_id=config['ELEVENLABS']['MODEL_ID'],
                language_code=config['ELEVENLABS']['LANGUAGE']
            )

        text_result = None
        try:
            logging.info(f"APIレスポンスのタイプ: {type(transcription)}")

            if transcription and hasattr(transcription, 'text'):
                text_result = transcription.text
                logging.info("レスポンスオブジェクトからtextプロパティを取得しました")
            else:
                logging.error(f"予期しないレスポンス形式、またはテキストが含まれていません: {type(transcription)}")
                logging.error(f"レスポンス内容: {transcription}")
                return None

        except Exception as response_error:
            logging.error(f"レスポンス処理中の予期しないエラー: {str(response_error)}")
            logging.debug(f"レスポンス処理エラー詳細: {traceback.format_exc()}")
            return None

        char_count = len(text_result) if text_result else 0
        logging.info(f"文字起こし結果の文字数: {char_count}")

        if char_count == 0:
            logging.warning("文字起こし結果が空です")
            return ""

        original_text = text_result

        try:
            if not use_punctuation and isinstance(text_result, str):
                text_result = text_result.replace('。', '')

            if not use_comma and isinstance(text_result, str):
                text_result = text_result.replace('、', '')

        except Exception as punctuation_error:
            logging.error(f"句読点処理中に予期しないエラー: {str(punctuation_error)}")
            text_result = original_text

        final_char_count = len(text_result) if text_result else 0
        logging.info(f"文字起こし完了: {final_char_count}文字")

        if text_result:
            preview_text = text_result[:20] + "..." if len(text_result) > 20 else text_result

        return text_result

    except FileNotFoundError as e:
        logging.error(f"ファイルが見つかりません: {str(e)}")
        logging.debug(f"詳細: {traceback.format_exc()}")
        return None
    except PermissionError as e:
        logging.error(f"ファイルアクセス権限エラー: {str(e)}")
        logging.debug(f"詳細: {traceback.format_exc()}")
        return None
    except OSError as e:
        logging.error(f"OS関連エラー: {str(e)}")
        logging.debug(f"詳細: {traceback.format_exc()}")
        return None
    except Exception as e:
        logging.error(f"文字起こしエラー: {str(e)}")
        logging.error(f"エラーのタイプ: {type(e).__name__}")
        logging.debug(f"詳細: {traceback.format_exc()}")

        try:
            logging.error(f"音声ファイルパス: {audio_file_path}")
            logging.error(f"use_punctuation: {use_punctuation}")
            logging.error(f"use_comma: {use_comma}")
            logging.error(f"設定ファイル MODEL_ID: {config.get('ELEVENLABS', {}).get('MODEL_ID', 'NOT_SET')}")
            logging.error(f"設定ファイル LANGUAGE: {config.get('ELEVENLABS', {}).get('LANGUAGE', 'NOT_SET')}")
        except Exception as debug_error:
            logging.error(f"デバッグ情報取得エラー: {str(debug_error)}")

        return None
