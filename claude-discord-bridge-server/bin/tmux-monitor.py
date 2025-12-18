#!/usr/bin/env python3
"""
tmux出力監視スクリプト
Claude Codeの思考過程をDiscordに流す
"""

import subprocess
import time
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.discord_post import post_to_discord
from config.settings import SettingsManager

# 監視対象のパターン
PATTERNS = {
    'tool_start': r'● (Bash|Read|Write|Edit|Grep|Glob|WebSearch|WebFetch|Task)',
    'thinking': r'✶ (Thinking|Bootstrapping|Processing)',
    'error': r'✗|Error:|Failed:',
}

def get_tmux_output(session_name: str, lines: int = 30) -> str:
    """tmuxセッションの出力を取得"""
    try:
        result = subprocess.run(
            ['tmux', 'capture-pane', '-t', session_name, '-p', '-S', f'-{lines}'],
            capture_output=True,
            text=True
        )
        return result.stdout
    except Exception as e:
        return ""

def extract_status(output: str) -> str | None:
    """出力から状態を抽出"""
    lines = output.strip().split('\n')

    for line in reversed(lines[-15:]):
        # ツール実行検出
        match = re.search(r'● (Bash|Read|Write|Edit|Grep|Glob|WebSearch|WebFetch|Task)\(([^)]{0,50})', line)
        if match:
            tool = match.group(1)
            arg = match.group(2)[:30] if match.group(2) else ""
            return f"🔧 {tool}: {arg}..."

        # 思考中検出
        if '✶' in line and ('Thinking' in line or 'Processing' in line):
            return "💭 考え中..."

        # エラー検出
        if '✗' in line or 'Error:' in line:
            return f"⚠️ {line[:50]}"

    return None

def main():
    settings = SettingsManager()
    session_name = sys.argv[1] if len(sys.argv) > 1 else "claude-session-1"
    channel_id = sys.argv[2] if len(sys.argv) > 2 else None

    if not channel_id:
        sessions = settings.list_sessions()
        if sessions:
            channel_id = sessions[0][1]
        else:
            print("No channel configured")
            sys.exit(1)

    print(f"Monitoring {session_name} -> {channel_id}")

    last_status = None
    last_sent_time = 0
    MIN_INTERVAL = 3  # 最低3秒間隔

    while True:
        output = get_tmux_output(session_name)
        status = extract_status(output)

        now = time.time()

        if status and status != last_status and (now - last_sent_time) > MIN_INTERVAL:
            print(f"[Monitor] {status}")
            post_to_discord(channel_id, status)
            last_status = status
            last_sent_time = now

        time.sleep(0.5)

if __name__ == "__main__":
    main()
