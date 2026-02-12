"""
Claude Code Rate Limit Monitor - Windows 系统托盘应用

用于监控 Claude Code 的 token 使用情况，当接近速率限制时发出警告。
"""
import sys
import os
import logging
from pathlib import Path

# 确保可以导入同目录下的模块
sys.path.insert(0, str(Path(__file__).parent))

from tray_app import TrayApp


def setup_logging():
    """配置日志"""
    log_dir = Path.home() / ".claude-monitor" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "monitor.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def main():
    """主函数"""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 50)
    logger.info("Claude Code Rate Limit Monitor 启动")
    logger.info("=" * 50)

    try:
        app = TrayApp()
        app.run()
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在退出...")
    except Exception as e:
        logger.exception(f"应用运行出错: {e}")
        sys.exit(1)

    logger.info("应用已退出")


if __name__ == "__main__":
    main()
