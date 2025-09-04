#!/usr/bin/env python3
"""
マーカーファイル方式のプロセス管理 - 技術検証（PoC）
このPoCで以下を検証:
1. マーカーファイルの作成・削除
2. PID記録と読み込み
3. 既存プロセスのクリーンアップ
4. Discord Bridge関連プロセスのみの管理
"""

import os
import sys
import time
import glob
import signal
import subprocess
from pathlib import Path

class ProcessMarkerManager:
    """プロセスマーカー管理システム"""
    
    def __init__(self):
        # マーカーファイルのベースディレクトリ
        self.marker_dir = Path("/tmp")
        self.marker_prefix = "claude-discord-bridge"
        self.marker_pattern = f"{self.marker_prefix}-*.pid"
        
    def create_marker(self, process_type="main"):
        """マーカーファイル作成とPID記録"""
        timestamp = int(time.time())
        marker_file = self.marker_dir / f"{self.marker_prefix}-{process_type}-{timestamp}.pid"
        
        # 現在のPIDを記録
        pid = os.getpid()
        marker_file.write_text(str(pid))
        
        print(f"✅ Created marker: {marker_file}")
        print(f"   PID: {pid}")
        return marker_file
    
    def find_old_markers(self):
        """既存のマーカーファイル検索"""
        pattern = str(self.marker_dir / self.marker_pattern)
        markers = glob.glob(pattern)
        
        print(f"\n🔍 Found {len(markers)} existing markers:")
        for marker in markers:
            print(f"   - {marker}")
        
        return markers
    
    def cleanup_old_processes(self):
        """古いマーカーファイルのプロセスをクリーンアップ"""
        old_markers = self.find_old_markers()
        
        if not old_markers:
            print("✅ No old processes to clean up")
            return
        
        print("\n🧹 Cleaning up old processes:")
        
        for marker_path in old_markers:
            try:
                # PID読み込み
                with open(marker_path, 'r') as f:
                    pid = int(f.read().strip())
                
                # プロセス存在確認
                try:
                    os.kill(pid, 0)  # プロセス存在チェック
                    print(f"   Found process PID {pid} from {Path(marker_path).name}")
                    
                    # プロセス終了
                    os.kill(pid, signal.SIGTERM)
                    print(f"   ✅ Terminated PID {pid}")
                    
                except ProcessLookupError:
                    print(f"   ⚠️  PID {pid} already gone")
                
                # マーカーファイル削除
                os.remove(marker_path)
                print(f"   ✅ Removed marker {Path(marker_path).name}")
                
            except Exception as e:
                print(f"   ❌ Error processing {marker_path}: {e}")
    
    def cleanup_discord_bridge_processes(self):
        """Discord Bridge関連プロセスの追加クリーンアップ"""
        print("\n🔍 Looking for Discord Bridge related processes:")
        
        # tmuxセッションのクリーンアップ
        tmux_sessions = [
            "claude-discord-bridge",
            "claude-session-1",
            "claude-session-2", 
            "claude-session-3",
            "claude-session-4"
        ]
        
        for session in tmux_sessions:
            result = subprocess.run(
                f"tmux has-session -t {session} 2>/dev/null",
                shell=True,
                capture_output=True
            )
            if result.returncode == 0:
                subprocess.run(f"tmux kill-session -t {session}", shell=True)
                print(f"   ✅ Killed tmux session: {session}")
        
        # discord_bot.py プロセスのクリーンアップ
        result = subprocess.run(
            "pgrep -f discord_bot.py",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    subprocess.run(f"kill -TERM {pid}", shell=True)
                    print(f"   ✅ Killed discord_bot.py (PID {pid})")
        
        # 古いClaude Codeプロセス（作業ディレクトリベース）のクリーンアップ
        result = subprocess.run(
            "ps aux | grep claude | grep '/workspaces/002--claude-test' | grep -v grep",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                parts = line.split()
                if len(parts) > 1:
                    pid = parts[1]
                    subprocess.run(f"kill -TERM {pid} 2>/dev/null", shell=True)
                    print(f"   ✅ Killed Claude process (PID {pid})")

def main():
    """技術検証メイン処理"""
    print("=" * 60)
    print("🚀 Discord Bridge Process Marker PoC")
    print("=" * 60)
    
    manager = ProcessMarkerManager()
    
    print("\n### Phase 1: Cleanup old processes ###")
    manager.cleanup_old_processes()
    manager.cleanup_discord_bridge_processes()
    
    print("\n### Phase 2: Create new marker ###")
    marker = manager.create_marker("poc-test")
    
    print("\n### Phase 3: Verify marker creation ###")
    if marker.exists():
        print(f"✅ Marker file exists: {marker}")
        print(f"   Content: {marker.read_text()}")
    else:
        print("❌ Marker creation failed!")
        sys.exit(1)
    
    print("\n### Phase 4: Test cleanup detection ###")
    print("Searching for our own marker...")
    markers = manager.find_old_markers()
    our_marker = str(marker) in [str(m) for m in markers]
    if our_marker:
        print("✅ Our marker is detectable")
    else:
        print("❌ Our marker not found!")
    
    print("\n### Phase 5: Cleanup test marker ###")
    marker.unlink()
    print(f"✅ Removed test marker: {marker}")
    
    print("\n" + "=" * 60)
    print("✅ PoC completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()