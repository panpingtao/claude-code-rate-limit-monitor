"""
JSONL 文件监控模块
"""
import time
import threading
import logging
from pathlib import Path
from typing import Callable, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent

from config import config_manager

logger = logging.getLogger(__name__)


class JSONLEventHandler(FileSystemEventHandler):
    """JSONL 文件变化事件处理器"""

    def __init__(self, callback: Callable[[], None], debounce_seconds: float = 0.5):
        """
        初始化事件处理器

        Args:
            callback: 文件变化时调用的回调函数
            debounce_seconds: 防抖延迟（秒）
        """
        super().__init__()
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()

    def on_modified(self, event):
        """文件修改事件"""
        if not event.is_directory and event.src_path.endswith('.jsonl'):
            self._schedule_callback()

    def on_created(self, event):
        """文件创建事件"""
        if not event.is_directory and event.src_path.endswith('.jsonl'):
            self._schedule_callback()

    def _schedule_callback(self):
        """调度回调（带防抖）"""
        with self._lock:
            # 取消之前的定时器
            if self._timer:
                self._timer.cancel()

            # 创建新的定时器
            self._timer = threading.Timer(self.debounce_seconds, self._execute_callback)
            self._timer.daemon = True
            self._timer.start()

    def _execute_callback(self):
        """执行回调"""
        try:
            self.callback()
        except Exception as e:
            logger.error(f"执行回调失败: {e}")


class FileWatcher:
    """JSONL 文件监控器"""

    def __init__(self, callback: Callable[[], None]):
        """
        初始化文件监控器

        Args:
            callback: 文件变化时调用的回调函数
        """
        self.config = config_manager.get()
        self.callback = callback
        self.observer: Optional[Observer] = None
        self._running = False

    def start(self):
        """启动文件监控"""
        if self._running:
            return

        watch_path = Path(self.config.claude_dir)
        if not watch_path.exists():
            logger.warning(f"监控目录不存在: {watch_path}")
            return

        try:
            self.observer = Observer()
            event_handler = JSONLEventHandler(self.callback)

            # 递归监控目录
            self.observer.schedule(
                event_handler,
                str(watch_path),
                recursive=True
            )

            self.observer.start()
            self._running = True
            logger.info(f"开始监控目录: {watch_path}")
        except Exception as e:
            logger.error(f"启动文件监控失败: {e}")

    def stop(self):
        """停止文件监控"""
        if self.observer and self._running:
            self.observer.stop()
            self.observer.join(timeout=5)
            self._running = False
            logger.info("文件监控已停止")

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._running
