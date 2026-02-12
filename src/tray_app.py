"""
系统托盘应用主类
"""
import threading
import time
import logging
from typing import Optional

import pystray
from pystray import MenuItem as Item

from config import config_manager, PLANS
from usage_calculator import UsageCalculator, UsageStats
from icon_generator import IconGenerator
from notifier import Notifier
from file_watcher import FileWatcher

logger = logging.getLogger(__name__)


class TrayApp:
    """系统托盘应用"""

    def __init__(self):
        self.config = config_manager.get()
        self.calculator = UsageCalculator()
        self.icon_generator = IconGenerator(size=64)
        self.notifier = Notifier(cooldown_minutes=self.config.notification_cooldown)
        self.file_watcher: Optional[FileWatcher] = None

        self.icon: Optional[pystray.Icon] = None
        self.current_stats: Optional[UsageStats] = None

        self._running = False
        self._refresh_thread: Optional[threading.Thread] = None
        self._last_warning_level = 0  # 0: 正常, 1: 警告(90%), 2: 严重(95%)

    def _create_plan_menu_items(self):
        """创建订阅计划菜单项"""
        items = []
        for plan_name, plan_info in PLANS.items():
            # 使用闭包捕获 plan_name
            def make_handler(name):
                return lambda icon, item: self._on_plan_select(name)

            # 当前选中的计划显示勾选标记
            items.append(Item(
                plan_info["description"],
                make_handler(plan_name),
                checked=lambda item, name=plan_name: self.config.plan == name
            ))
        return items

    def _on_plan_select(self, plan_name: str):
        """处理订阅计划选择"""
        if plan_name != self.config.plan:
            config_manager.update(plan=plan_name)
            self.config = config_manager.get()
            # 重新创建计算器以使用新配置
            self.calculator = UsageCalculator()
            self._refresh_stats()
            # 更新菜单
            if self.icon:
                self.icon.menu = self._create_menu()
            logger.info(f"Switched to plan: {plan_name}")

    def _create_menu(self):
        """创建右键菜单"""
        return pystray.Menu(
            Item('Refresh', self._on_refresh),
            Item('Plan', pystray.Menu(*self._create_plan_menu_items())),
            Item('Settings', pystray.Menu(
                Item(f'Threshold: {self.config.warning_threshold:.0f}%', None, enabled=False),
                Item(f'Interval: {self.config.refresh_interval}s', None, enabled=False),
            )),
            pystray.Menu.SEPARATOR,
            Item('Exit', self._on_quit)
        )

    def _get_tooltip(self) -> str:
        """生成托盘图标的悬停提示文本"""
        if not self.current_stats:
            return "Claude Monitor\nLoading..."

        stats = self.current_stats

        # 格式化数字
        def format_tokens(n: int) -> str:
            if n >= 1_000_000:
                return f"{n / 1_000_000:.2f}M"
            elif n >= 1_000:
                return f"{n / 1_000:.1f}K"
            return str(n)

        lines = [
            "Claude Code Monitor",
            f"Used: {format_tokens(stats.total_tokens)} / {format_tokens(stats.token_limit)}",
            f"Usage: {stats.percentage:.1f}%",
            f"Reset in: {stats.format_remaining_time()}",
            f"Status: {stats.status}",
        ]

        return "\n".join(lines)

    def _update_icon(self):
        """更新托盘图标"""
        if not self.icon:
            return

        percentage = self.current_stats.percentage if self.current_stats else 0

        # 生成新图标
        new_image = self.icon_generator.create_icon(percentage, show_text=True)

        # 更新图标和提示文本
        self.icon.icon = new_image
        self.icon.title = self._get_tooltip()

    def _check_and_notify(self):
        """检查使用率并发送通知"""
        if not self.current_stats:
            return

        stats = self.current_stats
        percentage = stats.percentage

        # 严重警告 (>= 95%)
        if percentage >= 95:
            if self._last_warning_level < 2:
                self.notifier.notify_critical(percentage, stats.remaining_tokens)
                self._last_warning_level = 2
        # 普通警告 (>= 90%)
        elif percentage >= self.config.warning_threshold:
            if self._last_warning_level < 1:
                self.notifier.notify_warning(percentage, stats.remaining_tokens)
                self._last_warning_level = 1
        # 恢复正常
        else:
            if self._last_warning_level > 0:
                self._last_warning_level = 0
                self.notifier.reset_cooldown()

    def _refresh_stats(self):
        """刷新使用统计"""
        try:
            self.current_stats = self.calculator.calculate()
            self._update_icon()
            self._check_and_notify()
            logger.debug(f"统计已刷新: {self.current_stats.percentage:.1f}%")
        except Exception as e:
            logger.error(f"刷新统计失败: {e}")

    def _on_refresh(self, icon=None, item=None):
        """刷新菜单项点击事件"""
        self._refresh_stats()

    def _on_quit(self, icon=None, item=None):
        """退出菜单项点击事件"""
        self.stop()

    def _refresh_loop(self):
        """后台刷新循环"""
        while self._running:
            self._refresh_stats()
            time.sleep(self.config.refresh_interval)

    def _on_file_changed(self):
        """文件变化回调"""
        logger.debug("检测到文件变化，刷新统计...")
        self._refresh_stats()

    def run(self):
        """运行托盘应用"""
        self._running = True

        # 初始刷新
        self._refresh_stats()

        # 创建初始图标
        percentage = self.current_stats.percentage if self.current_stats else 0
        initial_icon = self.icon_generator.create_icon(percentage, show_text=True)

        # 创建托盘图标
        self.icon = pystray.Icon(
            name="claude-monitor",
            icon=initial_icon,
            title=self._get_tooltip(),
            menu=self._create_menu()
        )

        # 启动文件监控
        self.file_watcher = FileWatcher(self._on_file_changed)
        self.file_watcher.start()

        # 启动后台刷新线程
        self._refresh_thread = threading.Thread(target=self._refresh_loop, daemon=True)
        self._refresh_thread.start()

        logger.info("托盘应用已启动")

        # 运行托盘图标（阻塞）
        self.icon.run()

    def stop(self):
        """停止托盘应用"""
        self._running = False

        # 停止文件监控
        if self.file_watcher:
            self.file_watcher.stop()

        # 停止托盘图标
        if self.icon:
            self.icon.stop()

        logger.info("托盘应用已停止")
