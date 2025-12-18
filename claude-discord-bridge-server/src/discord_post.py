#!/usr/bin/env python3
"""
Discord Post実装
メッセージをDiscordに投稿する + TTS音声再生
"""

import os
import sys
import json
import requests
import re
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import SettingsManager
from src.session_manager import SessionManager

def send_to_tts(text: str, session_num: int = 1):
    """Send text to Voice Bot TTS API for audio playback (non-blocking)"""
    import threading

    # セッション番号に応じたポートを選択（Session 1=3001, Session 2=3002, ...）
    tts_port = 3000 + session_num

    def _send_tts_async(clean_text: str):
        """Background thread for TTS request"""
        try:
            response = requests.post(
                f"http://localhost:{tts_port}/speak",
                json={"text": clean_text},
                timeout=5
            )
            if response.status_code == 200:
                print(f"[TTS] Queued: {clean_text[:50]}...")
            else:
                print(f"[TTS] Failed: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("[TTS] Voice Bot not running")
        except Exception as e:
            print(f"[TTS] Error: {e}")

    # TTS用にテキストをクリーンアップ
    clean_text = re.sub(r'<@\d+>\s*', '', text).strip()
    clean_text = re.sub(r'```[\s\S]*?```', '', clean_text)  # コードブロック除去
    clean_text = re.sub(r'`[^`]+`', '', clean_text)  # インラインコード除去
    clean_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean_text)  # 太字マークダウン除去
    clean_text = re.sub(r'\n+', '。', clean_text)  # 改行を句点に
    clean_text = clean_text.strip()

    if not clean_text or len(clean_text) < 2:
        return

    # 音声入力の文字起こし（🎤で始まる）はTTS不要
    if clean_text.startswith('🎤'):
        return

    # ツール通知（🔧で始まる）はTTS不要
    if clean_text.startswith('🔧'):
        return

    # 長すぎる場合は切り詰め（TTS用）- 省略メッセージは付けない
    if len(clean_text) > 200:
        clean_text = clean_text[:200]

    # TTS送信（同期で実行 - dpコマンドが終了する前に完了させる）
    _send_tts_async(clean_text)

def post_to_discord_raw(channel_id: str, message: str):
    """Post a message to Discord channel without TTS (for logging only)"""
    settings = SettingsManager()

    token = settings.get_token()
    if not token:
        return False

    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    payload = {"content": message}

    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.status_code == 200
    except:
        return False

def post_to_discord(channel_id: str, message: str, session_num: int = 1):
    """Post a message to Discord channel"""
    settings = SettingsManager()

    # Get bot token
    token = settings.get_token()
    if not token:
        print("Error: Discord bot token not configured")
        sys.exit(1)

    # Discord API endpoint
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"

    # Headers
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }

    # メンションパターンを完全除去（<@数字>）
    clean_message = re.sub(r'<@\d+>\s*', '', message).strip()

    # Payload
    payload = {
        "content": clean_message
    }

    try:
        # Send request
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            # TTS送信（Discord送信成功時のみ）- セッション番号でポート切り替え
            send_to_tts(clean_message, session_num)
            return True
        else:
            print(f"Error: Discord API returned status {response.status_code}")
            if response.status_code == 401:
                print("Invalid bot token")
            elif response.status_code == 403:
                print("Bot doesn't have permission to send messages in this channel")
            elif response.status_code == 404:
                print("Channel not found")
            else:
                print(f"Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("Error: Failed to connect to Discord API")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Main function for command line usage (multi-session support)"""
    settings = SettingsManager()
    session_manager = SessionManager()

    # Check for --notify flag
    notify_mode = '--notify' in sys.argv
    if notify_mode:
        sys.argv.remove('--notify')

    # Check for --from flag (source session)
    from_session = 1  # default
    if '--from' in sys.argv:
        from_idx = sys.argv.index('--from')
        if from_idx + 1 < len(sys.argv):
            from_session = int(sys.argv[from_idx + 1])
            sys.argv.pop(from_idx + 1)
            sys.argv.pop(from_idx)

    # Check if stdin has data
    if not sys.stdin.isatty():
        message = sys.stdin.read().strip()

        # Check if channel ID is provided as argument
        if len(sys.argv) > 1:
            channel_arg = sys.argv[1]
        else:
            # Use default session
            channel_arg = str(session_manager.get_default_session())
        
        # Determine if it's a session number or channel ID
        session_num = 1  # デフォルト
        if channel_arg.isdigit() and len(channel_arg) < 5:
            # It's a session number - use SessionManager with validation
            session_id = int(channel_arg)
            session_num = session_id  # TTSポート切り替え用に保持

            # Validate session number range (1-9999)
            if session_id < 1 or session_id > 9999:
                print(f"Error: Invalid session number {session_id} (must be 1-9999)")
                sys.exit(1)

            # Get channel ID from SessionManager
            channel_id = session_manager.get_channel_by_session(session_id)
            if not channel_id:
                # Provide helpful error with available sessions
                configured_sessions = settings.list_sessions()
                if configured_sessions:
                    session_list = ", ".join([str(num) for num, _ in configured_sessions])
                    print(f"Error: Session {session_id} not configured")
                    print(f"Available sessions: {session_list}")
                else:
                    print(f"Error: No sessions configured. Run './bin/vai add-session <channel_id>' to add a session.")
                sys.exit(1)
        else:
            # It's a channel ID - validate format
            if not channel_arg.isdigit() or len(channel_arg) < 10:
                print(f"Error: Invalid channel ID format '{channel_arg}'")
                print("Channel ID should be a long number (e.g., 1234567890123456)")
                sys.exit(1)
            channel_id = channel_arg

        # If notify mode, send to both channels with [A→B] format
        if notify_mode:
            # セッション番号をアルファベットに変換 (1=A, 2=B, 3=C, ...)
            from_letter = chr(ord('A') + from_session - 1)
            to_letter = chr(ord('A') + session_num - 1)

            # Format: [A→B] メッセージ session=X (シンプル形式)
            formatted_msg = f"[{from_letter}→{to_letter}] {message}"
            notify_trigger = f"session={from_session}"

            # 1. 送信元チャンネルに履歴として投稿（TTSなし）
            from_channel_id = session_manager.get_channel_by_session(from_session)
            if from_channel_id:
                post_to_discord_raw(from_channel_id, formatted_msg)

            # 2. 送信先チャンネルに投稿（Claudeが反応する）
            full_msg = f"{formatted_msg} {notify_trigger}"
            if post_to_discord(channel_id, full_msg, session_num):
                pass
            else:
                sys.exit(1)
        else:
            # Post message with session number for TTS routing
            if post_to_discord(channel_id, message, session_num):
                # Success - no output
                pass
            else:
                sys.exit(1)
    else:
        print("Usage: echo 'message' | discord_post.py [session_number or channel_id] [--notify]")
        sys.exit(1)

if __name__ == "__main__":
    main()