"""
Windows 通知管理模块
"""
import time
import threading
import logging
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# 尝试导入 win10toast
try:
    from win10toast import ToastNotifier
    TOAST_AVAILABLE = True
except ImportError:
    TOAST_AVAILABLE = False
    logger.warning("win10toast 不可用，通知功能将被禁用")


class Notifier:
    """Windows 通知管理器"""

    def __init__(self, cooldown_minutes: int = 15):
        """
        初始化通知管理器

        Args:
            cooldown_minutes: 相同类型通知的冷却时间（分钟）
        """
        self.cooldown = timedelta(minutes=cooldown_minutes)
        self.last_notification: dict = {}
        self._lock = threading.Lock()

        if TOAST_AVAILABLE:
            self.toaster = ToastNotifier()
        else:
            self.toaster = None

    def notify(
            self,
            title: str,
            message: str,
            notification_type: str = "default",
            duration: int = 10,
            force: bool = False
    ) -> bool:
        """
        发送 Windows 通知

        Args:
            title: 通知标题
            message: 通知内容
            notification_type: 通知类型（用于防抖）
            duration: 通知显示时长（秒）
            force: 是否强制发送（忽略冷却）

        Returns:
            是否成功发送通知
        """
        if not self.toaster:
            logger.debug(f"通知（无 toast）: {title} - {message}")
            return False

        with self._lock:
            now = datetime.now()

            # 检查冷却时间
            if not force and notification_type in self.last_notification:
                last_time = self.last_notification[notification_type]
                if now - last_time < self.cooldown:
                    remaining = (self.cooldown - (now - last_time)).total_seconds()
                    logger.debug(f"通知冷却中，剩余 {remaining:.0f} 秒")
                    return False

            # 记录发送时间
            self.last_notification[notification_type] = now

        # 在后台线程发送通知（避免阻塞主线程）
        def send():
            try:
                self.toaster.show_toast(
                    title=title,
                    msg=message,
                    duration=duration,
                    threaded=True
                )
                logger.info(f"通知已发送: {title}")
            except Exception as e:
                logger.error(f"发送通知失败: {e}")

        threading.Thread(target=send, daemon=True).start()
        return True

    def notify_warning(self, percentage: float, remaining_tokens: int) -> bool:
        """
        发送使用率警告通知

        Args:
            percentage: 当前使用百分比
            remaining_tokens: 剩余 token 数量

        Returns:
            是否成功发送
        """
        title = "Claude Code Usage Warning"
        message = (
            f"Usage reached {percentage:.1f}%\n"
            f"Remaining: {remaining_tokens:,} tokens\n"
            f"Consider pausing important tasks"
        )

        return self.notify(
            title=title,
            message=message,
            notification_type="usage_warning",
            duration=10
        )

    def notify_critical(self, percentage: float, remaining_tokens: int) -> bool:
        """
        发送严重警告通知（使用率 > 95%）

        Args:
            percentage: 当前使用百分比
            remaining_tokens: 剩余 token 数量

        Returns:
            是否成功发送
        """
        title = "Claude Code CRITICAL Warning"
        message = (
            f"Usage reached {percentage:.1f}%!\n"
            f"Only {remaining_tokens:,} tokens left\n"
            f"Stop operations immediately!"
        )

        return self.notify(
            title=title,
            message=message,
            notification_type="usage_critical",
            duration=15
        )

    def reset_cooldown(self, notification_type: Optional[str] = None):
        """
        重置通知冷却时间

        Args:
            notification_type: 要重置的通知类型，None 表示重置所有
        """
        with self._lock:
            if notification_type:
                self.last_notification.pop(notification_type, None)
            else:
                self.last_notification.clear()


# 全局通知管理器实例
notifier = Notifier(cooldown_minutes=15)
