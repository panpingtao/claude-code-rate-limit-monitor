# Claude Code Rate Limit Monitor

A lightweight Windows system tray application for monitoring Claude Code token usage in real-time. Get notified before you hit the rate limit!

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Features

- **System Tray Icon** - Shows usage status at a glance with color-coded icons:
  - 🟢 Green: < 70% usage
  - 🟡 Yellow: 70% - 90% usage
  - 🔴 Red: > 90% usage

- **Hover Tooltip** - View detailed usage information by hovering over the tray icon:
  - Current tokens used / Total limit
  - Usage percentage
  - Time until window reset
  - Current status

- **Smart Notifications** - Get Windows toast notifications when:
  - Usage reaches 90% (warning)
  - Usage reaches 95% (critical)
  - 15-minute cooldown prevents notification spam

- **Plan Selection** - Switch between subscription plans via right-click menu:
  - Pro ($20/month)
  - Max 5x ($100/month)
  - Max 20x ($200/month)

- **Real-time Updates** - Automatically refreshes every 30 seconds and detects JSONL file changes

## Screenshot

```
Claude Code Monitor
Used: 22.82M / 43.72M
Usage: 52.2%
Reset in: 3h 30m
Status: OK
```

## Installation

### Prerequisites

- Python 3.9 or higher
- Windows 10/11

### Install Dependencies

```bash
pip install pystray Pillow win10toast watchdog
```

### Download

```bash
git clone https://github.com/YOUR_USERNAME/claude-code-rate-limit-monitor.git
cd claude-code-rate-limit-monitor
```

## Usage

### Start the Monitor

**Option 1: Double-click the batch file**
```
start.bat
```

**Option 2: Run from command line**
```bash
cd src
python main.py
```

**Option 3: Run silently (no console window)**
```bash
cd src
pythonw main.py
```

### Tray Icon Menu (Right-click)

- **Refresh** - Manually refresh usage data
- **Plan** - Select your Claude subscription plan
- **Settings** - View current settings (threshold, refresh interval)
- **Exit** - Close the application

## Configuration

Configuration is stored at `~/.claude-monitor/config.json`:

```json
{
  "plan": "Max 5x",
  "window_hours": 5,
  "warning_threshold": 90.0,
  "refresh_interval": 30,
  "notification_cooldown": 15
}
```

| Setting | Description | Default |
|---------|-------------|---------|
| `plan` | Subscription plan (Pro, Max 5x, Max 20x) | Max 5x |
| `window_hours` | Rolling window duration | 5 |
| `warning_threshold` | Percentage to trigger warning | 90.0 |
| `refresh_interval` | Auto-refresh interval in seconds | 30 |
| `notification_cooldown` | Minutes between repeated notifications | 15 |

## How It Works

1. Scans Claude Code JSONL log files at `~/.claude/projects/`
2. Parses messages within the 5-hour rolling window
3. Calculates total token usage (input + output + cache tokens)
4. Compares against your plan's token limit
5. Updates the tray icon and triggers notifications as needed

## Project Structure

```
claude-code-rate-limit-monitor/
├── src/
│   ├── main.py              # Entry point
│   ├── tray_app.py          # System tray application
│   ├── usage_calculator.py  # Token usage calculation
│   ├── icon_generator.py    # Dynamic icon generation
│   ├── notifier.py          # Windows notifications
│   ├── file_watcher.py      # JSONL file monitoring
│   └── config.py            # Configuration management
├── start.bat                # Quick start script
├── requirements.txt         # Python dependencies
├── LICENSE                  # MIT License
└── README.md               # This file
```

## Building Executable (Optional)

To create a standalone `.exe` file:

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name="ClaudeMonitor" src/main.py
```

The executable will be created in the `dist/` folder.

## Troubleshooting

### Icon not showing in system tray
- Check if Windows is hiding the icon - click the "^" arrow in the taskbar
- Right-click taskbar → Taskbar settings → Select which icons appear

### Usage shows 0%
- Ensure Claude Code has been used recently (within 5 hours)
- Check that JSONL files exist at `~/.claude/projects/`

### Notifications not working
- Ensure Windows notifications are enabled for Python
- Check Windows Settings → System → Notifications

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by [ccusage](https://github.com/ryoppippi/ccusage) for token calculation logic
- Built for the Claude Code community

## Related Tools

- [ccusage](https://github.com/ryoppippi/ccusage) - CLI tool for Claude Code usage analysis
- [claude-monitor](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor) - Terminal-based monitor
