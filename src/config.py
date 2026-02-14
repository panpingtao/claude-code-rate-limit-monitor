"""
配置管理模块
"""
import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional


# 订阅计划配置
PLANS = {
    "Pro": {
        "token_limit": 8_744_628,
        "description": "Pro ($20/month)"
    },
    "Max 5x": {
        "token_limit": 100_000_000,  # ~100M tokens based on actual limit testing
        "description": "Max 5x ($100/month)"
    },
    "Max 20x": {
        "token_limit": 400_000_000,  # ~400M tokens (estimated 4x of Max 5x)
        "description": "Max 20x ($200/month)"
    }
}


@dataclass
class Config:
    """应用配置"""
    # 当前订阅计划
    plan: str = "Max 5x"

    # 时间窗口 (小时)
    window_hours: int = 5

    @property
    def token_limit(self) -> int:
        """根据订阅计划返回 token 限制"""
        return PLANS.get(self.plan, PLANS["Pro"])["token_limit"]

    # 警告阈值 (百分比)
    warning_threshold: float = 90.0

    # 刷新间隔 (秒)
    refresh_interval: int = 30

    # 通知防抖时间 (分钟)
    notification_cooldown: int = 15

    # Claude 日志目录
    claude_dir: str = ""

    def __post_init__(self):
        if not self.claude_dir:
            self.claude_dir = str(Path.home() / ".claude" / "projects")


class ConfigManager:
    """配置管理器"""

    def __init__(self):
        self.config_dir = Path.home() / ".claude-monitor"
        self.config_file = self.config_dir / "config.json"
        self.config = self._load_config()

    def _load_config(self) -> Config:
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return Config(**data)
            except (json.JSONDecodeError, TypeError):
                pass
        return Config()

    def save_config(self):
        """保存配置到文件"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.config), f, indent=2, ensure_ascii=False)

    def get(self) -> Config:
        """获取当前配置"""
        return self.config

    def update(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save_config()


# 全局配置管理器实例
config_manager = ConfigManager()
