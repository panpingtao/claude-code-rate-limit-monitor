"""
Token 使用量计算模块
"""
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
import logging

from config import config_manager

logger = logging.getLogger(__name__)


@dataclass
class UsageStats:
    """使用统计数据"""
    total_tokens: int = 0
    token_limit: int = 0
    percentage: float = 0.0
    window_start: Optional[datetime] = None
    window_end: Optional[datetime] = None
    remaining_tokens: int = 0
    remaining_time: Optional[timedelta] = None
    oldest_message_time: Optional[datetime] = None

    @property
    def status(self) -> str:
        """获取状态描述"""
        if self.percentage >= 90:
            return "CRITICAL"
        elif self.percentage >= 70:
            return "WARNING"
        else:
            return "OK"

    @property
    def status_color(self) -> str:
        """获取状态颜色"""
        if self.percentage >= 90:
            return "red"
        elif self.percentage >= 70:
            return "yellow"
        else:
            return "green"

    def format_remaining_time(self) -> str:
        """格式化剩余时间"""
        if not self.remaining_time:
            return "N/A"

        total_seconds = int(self.remaining_time.total_seconds())
        if total_seconds <= 0:
            return "Resetting"

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"


class UsageCalculator:
    """Token 使用量计算器"""

    def __init__(self):
        self.config = config_manager.get()

    def calculate(self) -> UsageStats:
        """计算当前 5 小时窗口内的 token 使用量"""
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(hours=self.config.window_hours)

        total_tokens = 0
        oldest_message_time = None
        messages_in_window = []

        # 扫描所有 JSONL 文件
        claude_dir = Path(self.config.claude_dir)
        if not claude_dir.exists():
            logger.warning(f"Claude 目录不存在: {claude_dir}")
            return UsageStats(token_limit=self.config.token_limit)

        for jsonl_file in claude_dir.rglob("*.jsonl"):
            try:
                tokens, oldest = self._parse_jsonl_file(jsonl_file, window_start)
                total_tokens += tokens
                if oldest:
                    if oldest_message_time is None or oldest < oldest_message_time:
                        oldest_message_time = oldest
            except Exception as e:
                logger.debug(f"解析文件失败 {jsonl_file}: {e}")
                continue

        # 计算剩余时间
        remaining_time = None
        if oldest_message_time:
            # 窗口重置时间 = 最老消息时间 + 5小时
            reset_time = oldest_message_time + timedelta(hours=self.config.window_hours)
            remaining_time = reset_time - now
            if remaining_time.total_seconds() < 0:
                remaining_time = timedelta(0)

        # 计算百分比
        percentage = (total_tokens / self.config.token_limit * 100) if self.config.token_limit > 0 else 0
        remaining_tokens = max(0, self.config.token_limit - total_tokens)

        return UsageStats(
            total_tokens=total_tokens,
            token_limit=self.config.token_limit,
            percentage=min(percentage, 100.0),
            window_start=window_start,
            window_end=now,
            remaining_tokens=remaining_tokens,
            remaining_time=remaining_time,
            oldest_message_time=oldest_message_time
        )

    def _parse_jsonl_file(self, file_path: Path, window_start: datetime) -> tuple:
        """
        解析 JSONL 文件，返回窗口内的 token 数和最老消息时间
        """
        total_tokens = 0
        oldest_time = None

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # 检查是否有 usage 数据
                message = entry.get('message', {})
                usage = message.get('usage', {})

                if not usage:
                    continue

                # 解析时间戳
                timestamp_str = entry.get('timestamp')
                if not timestamp_str:
                    continue

                try:
                    # 处理 ISO 8601 格式时间戳
                    msg_time = datetime.fromisoformat(
                        timestamp_str.replace('Z', '+00:00')
                    )
                except ValueError:
                    continue

                # 检查是否在时间窗口内
                if msg_time >= window_start:
                    # 计算所有 token 类型的总和（与 ccusage 保持一致）
                    input_tokens = usage.get('input_tokens', 0)
                    output_tokens = usage.get('output_tokens', 0)
                    cache_creation = usage.get('cache_creation_input_tokens', 0)
                    cache_read = usage.get('cache_read_input_tokens', 0)

                    message_tokens = input_tokens + output_tokens + cache_creation + cache_read
                    total_tokens += message_tokens

                    # 记录最老消息时间
                    if oldest_time is None or msg_time < oldest_time:
                        oldest_time = msg_time

        return total_tokens, oldest_time


# 全局计算器实例
calculator = UsageCalculator()
