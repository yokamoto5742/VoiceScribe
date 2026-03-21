import atexit
import faulthandler
import logging
import signal
from typing import Callable


def setup_process(on_shutdown: Callable[[], None]) -> None:
    """クラッシュログ・シグナル・終了フックを設定する。"""
    crash_log = open('crash_log.txt', 'w', encoding='utf-8')
    faulthandler.enable(file=crash_log, all_threads=True)
    atexit.register(lambda: logging.info('プロセス終了 (atexit)'))

    def _handle_signal(signum, _frame):
        logging.warning(f'シグナル受信: {signum} — アプリを終了します')
        on_shutdown()

    signal.signal(signal.SIGTERM, _handle_signal)
