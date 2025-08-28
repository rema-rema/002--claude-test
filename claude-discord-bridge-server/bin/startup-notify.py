#!/usr/bin/env python3
"""
Claude-Discord Bridge スタートアップ通知スクリプト
起動時に各セッションに起動報告を送信し、応答を確認する
"""

import subprocess
import time
import json
import sys
from pathlib import Path

# ANSI colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
YELLOW = '\033[0;33m'
NC = '\033[0m'  # No Color

def get_sessions():
    """設定済みのセッション情報を取得"""
    sessions_file = Path(__file__).parent.parent / 'sessions.json'
    
    if not sessions_file.exists():
        return {}
    
    with open(sessions_file, 'r') as f:
        data = json.load(f)
        # sessions.jsonの形式に対応
        if isinstance(data, dict) and 'sessions' not in data:
            # {"1": "channel_id", "2": "channel_id", ...} 形式
            sessions = {}
            for session_num, channel_id in data.items():
                if channel_id:  # 空でないチャンネルIDのみ
                    sessions[f"session_{session_num}"] = {
                        'channel_id': channel_id
                    }
            return sessions
        else:
            return data.get('sessions', {})

def send_startup_message(session_id, channel_id):
    """各セッションに起動メッセージを送信"""
    message = f"🚀 Claude Code Session {session_id} 起動完了\\n\\n"
    message += f"✅ システムチェック完了\\n"
    message += f"📍 セッション {session_id}\\n"
    message += f"💻 作業準備完了\\n\\n"
    message += f"応答確認: 'OK' で返信してください"
    
    # dpコマンドを使用して送信
    dp_path = Path(__file__).parent / 'dp'
    cmd = [str(dp_path), str(session_id), message]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except Exception as e:
        print(f"{RED}❌ Session {session_id} への送信失敗: {e}{NC}")
        return False

def check_all_sessions():
    """全セッションの起動確認と通知"""
    sessions = get_sessions()
    
    if not sessions:
        print(f"{YELLOW}⚠️  設定されたセッションがありません{NC}")
        return False
    
    print(f"{BLUE}📡 起動通知を送信中...{NC}")
    print("=" * 50)
    
    all_success = True
    results = {}
    
    # 各セッションに通知を送信
    for session_id, info in sessions.items():
        channel_id = info.get('channel_id', '')
        if not channel_id:
            continue
            
        session_num = session_id.replace('session_', '')
        print(f"\n{BLUE}Session {session_num}:{NC}")
        print(f"  Channel: {channel_id}")
        print(f"  送信中...", end='', flush=True)
        
        success = send_startup_message(session_num, channel_id)
        results[session_num] = success
        
        if success:
            print(f"\r  {GREEN}✅ 送信完了{NC}")
        else:
            print(f"\r  {RED}❌ 送信失敗{NC}")
            all_success = False
        
        # セッション間の待機
        time.sleep(2)
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print(f"{BLUE}📊 起動通知結果:{NC}")
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    if all_success:
        print(f"{GREEN}✅ 全セッション ({success_count}/{total_count}) への通知完了{NC}")
        print(f"\n{GREEN}💬 各チャンネルで 'OK' と返信して準備完了を確認してください{NC}")
    else:
        print(f"{YELLOW}⚠️  一部のセッション ({success_count}/{total_count}) への通知が完了{NC}")
        failed = [k for k, v in results.items() if not v]
        print(f"{RED}   失敗したセッション: {', '.join(failed)}{NC}")
    
    return all_success

def wait_for_responses(timeout=60):
    """応答確認の待機（手動確認用のメッセージ表示）"""
    print(f"\n{BLUE}⏳ 応答待機中...{NC}")
    print(f"   各セッションのClaude Codeが 'OK' で応答するまでお待ちください")
    print(f"   （最大 {timeout} 秒）")
    
    # プログレスバー表示
    for i in range(timeout):
        progress = '█' * (i * 30 // timeout)
        remaining = '░' * (30 - (i * 30 // timeout))
        print(f"\r   [{progress}{remaining}] {i}/{timeout}秒", end='', flush=True)
        time.sleep(1)
    
    print(f"\n{GREEN}✅ 待機完了{NC}")

def main():
    """メイン処理"""
    print(f"{BLUE}🚀 Claude-Discord Bridge 起動通知システム{NC}")
    print("=" * 50)
    
    # vai statusで起動確認
    print(f"{BLUE}📊 システム状態確認中...{NC}")
    status_result = subprocess.run(['./bin/vai', 'status'], capture_output=True, text=True)
    
    if "Discord Bot: ✅ Running" not in status_result.stdout:
        print(f"{RED}❌ Discord Botが起動していません{NC}")
        print(f"   先に ./start-bridge.sh でサービスを起動してください")
        return 1
    
    # 各セッションへの通知
    success = check_all_sessions()
    
    if success:
        # 応答待機
        wait_for_responses(30)
        
        print("\n" + "=" * 50)
        print(f"{GREEN}🎉 起動通知プロセス完了！{NC}")
        print(f"{GREEN}   全セッションで会話を開始できます{NC}")
        return 0
    else:
        print(f"\n{YELLOW}⚠️  一部のセッションへの通知に失敗しました{NC}")
        print(f"   ./bin/vai recover <session_id> で復旧を試みてください")
        return 1

if __name__ == '__main__':
    sys.exit(main())