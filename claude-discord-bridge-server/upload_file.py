#!/usr/bin/env python3
"""
ファイルアップロード機能
Playwright動画ファイルをDiscordにアップロード
"""

import os
import sys
import requests
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import SettingsManager
from src.session_manager import SessionManager

def upload_file_to_discord(file_path: str, message: str = "", session_num: int = 1):
    """ファイルをDiscordにアップロード"""
    
    # ファイル存在確認
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False
    
    # 設定取得
    settings = SettingsManager()
    session_manager = SessionManager()
    
    # チャンネルID取得
    sessions = settings.list_sessions()
    channel_id = None
    
    for s_id, c_id in sessions:
        if s_id == session_num:
            channel_id = c_id
            break
    
    if not channel_id:
        # デフォルトチャンネル使用
        channel_id = settings.get_default_channel_id()
        if not channel_id:
            print("Error: No channel ID configured")
            return False
    
    # Bot Token取得
    token = settings.get_token()
    if not token:
        print("Error: Discord bot token not configured")
        return False
    
    # Discord API endpoint
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    
    # Headers
    headers = {
        "Authorization": f"Bot {token}"
    }
    
    # ファイル読み込み
    try:
        with open(file_path, 'rb') as f:
            files = {
                'file': (os.path.basename(file_path), f, 'video/webm')
            }
            
            # データペイロード
            data = {}
            if message:
                data['content'] = message
            
            # アップロード実行
            response = requests.post(url, headers=headers, files=files, data=data)
            
            if response.status_code == 200:
                print(f"✅ File uploaded successfully: {os.path.basename(file_path)}")
                return True
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python upload_file.py <file_path> [message] [session_num]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    message = sys.argv[2] if len(sys.argv) > 2 else ""
    session_num = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    
    success = upload_file_to_discord(file_path, message, session_num)
    sys.exit(0 if success else 1)