import logging
import queue
import threading
import tkinter as tk
from typing import Callable


class UIQueueProcessor:
    """スレッドセーフにUIコールバックをスケジュール・実行するクラス"""

    def __init__(self, master: tk.Tk):
        self.master = master
        self._ui_queue: queue.Queue = queue.Queue()
        self._ui_lock = threading.Lock()
        self._is_shutting_down = False

    def start(self):
        """UIキュー処理を開始"""
        if self.is_ui_valid():
            try:
                self.master.after(50, self._process_queue)
            except tk.TclError as e:
                logging.error(f"UIキュー処理開始に失敗: {str(e)}")

    def _process_queue(self):
        if self._is_shutting_down:
            return

        try:
            for _ in range(10):
                try:
                    callback, args = self._ui_queue.get_nowait()
                    try:
                        callback(*args)
                    except tk.TclError as e:
                        logging.warning(f"UIコールバック実行中にTclError: {str(e)}")
                    except Exception as e:
                        logging.error(f"UIコールバック実行中にエラー: {str(e)}")
                except queue.Empty:
                    break
        except Exception as e:
            logging.error(f"UIキュー処理中にエラー: {str(e)}")
        finally:
            if not self._is_shutting_down and self.is_ui_valid():
                try:
                    self.master.after(50, self._process_queue)
                except tk.TclError:
                    pass

    def schedule_callback(self, callback: Callable, *args):
        """スレッドセーフにUIコールバックをスケジュール"""
        if self._is_shutting_down:
            logging.debug("シャットダウン中のためUIコールバックをスキップ")
            return

        try:
            self._ui_queue.put_nowait((callback, args))
        except Exception as e:
            logging.error(f"UIコールバックのキューイングに失敗: {str(e)}")

    def is_ui_valid(self) -> bool:
        """UIが有効かどうかを確認"""
        if self._is_shutting_down:
            return False

        try:
            with self._ui_lock:
                return (self.master is not None and
                        hasattr(self.master, 'winfo_exists') and
                        self.master.winfo_exists())
        except tk.TclError:
            return False
        except Exception:
            return False

    @property
    def is_shutting_down(self) -> bool:
        return self._is_shutting_down

    def shutdown(self):
        """シャットダウンフラグを設定"""
        self._is_shutting_down = True
