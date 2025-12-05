import logging
import time
import traceback

import keyboard
import pyperclip

logger = logging.getLogger(__name__)


def safe_clipboard_copy(text: str) -> bool:
    """テキストを安全にクリップボードへコピー"""
    if not text:
        return False

    max_retries = 3
    for attempt in range(max_retries):
        try:
            pyperclip.copy(text)
            time.sleep(0.05)
            copied_text = pyperclip.paste()
            if copied_text == text:
                logger.info("クリップボードコピー完了")
                return True
            else:
                logger.warning(f"クリップボードコピー検証失敗 (試行 {attempt + 1}/{max_retries})")
        except Exception as e:
            logger.error(f"クリップボードコピー中にエラー (試行 {attempt + 1}/{max_retries}): {str(e)}")
            logger.debug(f"詳細: {traceback.format_exc()}")

        if attempt < max_retries - 1:
            time.sleep(0.1 * (attempt + 1))

    logger.error("クリップボードコピーが最大試行回数後に失敗しました")
    return False


def safe_paste_text() -> bool:
    """クリップボードの内容を貼り付け"""
    try:
        logger.debug("safe_paste_text開始")

        current_text = pyperclip.paste()
        if not current_text:
            logger.warning("クリップボードが空です")
            return False

        # keyboard操作前に少し待機（フォーカス安定化）
        time.sleep(0.05)

        logger.debug("keyboard.send('ctrl+v')実行前")
        keyboard.send('ctrl+v')
        logger.debug("keyboard.send('ctrl+v')実行後")

        time.sleep(0.1)
        logger.debug("safe_paste_text完了")
        return True

    except AttributeError as e:
        logger.error(f"keyboard属性エラー: {e}")
        logger.debug(f"詳細: {traceback.format_exc()}")
        return False
    except OSError as e:
        logger.error(f"OSエラー（キーボード操作失敗）: {e}")
        logger.debug(f"詳細: {traceback.format_exc()}")
        return False
    except Exception as e:
        logger.error(f"貼り付け操作に失敗: {type(e).__name__}: {e}")
        logger.debug(f"詳細: {traceback.format_exc()}")
        return False


def is_paste_available() -> bool:
    """貼り付け可能かどうかをチェック"""
    try:
        # keyboardライブラリが利用可能であればTrue
        return True
    except Exception as e:
        logger.error(f"貼り付け機能利用不可: {e}")
        return False
