#!/usr/bin/env python3
"""
Auto Recovery System - セッション自動復旧システム

このモジュールは以下の責任を持つ：
1. 全Claudeセッションの死活監視
2. 障害検出時の自動復旧
3. 指数バックオフによるリトライ制御
4. 復旧履歴の記録・管理
5. Discord通知による運用通知

拡張性のポイント：
- カスタム復旧戦略の実装
- 複雑な障害パターンの検出
- 機械学習による障害予測
- 外部監視システムとの連携
"""

import os
import sys
import json
import time
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from threading import Thread, Event

# パッケージルートの追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.session_manager import SessionManager
from src.tmux_manager import TmuxManager
from config.settings import SettingsManager

try:
    import requests
except ImportError:
    print("Error: requests not installed. Run: pip install requests")
    sys.exit(1)

# ログ設定
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@dataclass
class RecoveryAttempt:
    """復旧試行記録"""
    session_id: int
    attempt_number: int
    timestamp: str
    success: bool
    error_message: Optional[str] = None
    recovery_duration: Optional[float] = None

class RecoveryStrategy:
    """
    復旧戦略実装（指数バックオフ）
    
    将来の拡張：
    - 線形バックオフ
    - ランダムジッター追加
    - カスタム戦略パターン
    """
    
    # 設定定数
    MAX_RETRY_ATTEMPTS = 3
    BASE_BACKOFF_SECONDS = 1
    MAX_BACKOFF_SECONDS = 60
    
    @classmethod
    def get_backoff_time(cls, attempt: int) -> float:
        """
        指数バックオフ時間の計算
        
        Args:
            attempt: 試行回数（1から開始）
            
        Returns:
            float: 待機時間（秒）
        """
        backoff = cls.BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
        return min(backoff, cls.MAX_BACKOFF_SECONDS)

class AutoRecoverySystem:
    """
    セッション自動復旧システム
    
    アーキテクチャ特徴：
    - 非同期監視による低負荷動作
    - 指数バックオフによる効率的リトライ
    - 復旧履歴の永続化
    - Discord通知統合
    - グレースフルシャットダウン
    
    拡張可能要素：
    - 予防的復旧（異常予測）
    - 複数復旧戦略の切り替え
    - 依存関係考慮した復旧順序
    - 部分的復旧（軽量再起動）
    """
    
    # 監視設定
    HEALTH_CHECK_INTERVAL = 30  # 30秒間隔
    RECOVERY_LOG_FILE = "logs/recovery_history.json"
    RECOVERY_LOG_MAX_ENTRIES = 1000
    
    def __init__(self):
        """
        AutoRecoverySystemの初期化
        """
        self.session_manager = SessionManager()
        self.tmux_manager = TmuxManager()
        self.settings = SettingsManager()
        self.recovery_strategy = RecoveryStrategy()
        
        # 復旧記録管理
        self.recovery_history: List[RecoveryAttempt] = []
        self.recovery_counts: Dict[int, int] = {}  # {session_id: attempt_count}
        
        # 監視制御
        self.monitoring = False
        self.stop_event = Event()
        self.monitor_thread: Optional[Thread] = None
        
        # 復旧履歴ロード
        self._load_recovery_history()
    
    def _load_recovery_history(self):
        """復旧履歴の読み込み"""
        try:
            log_path = Path(self.RECOVERY_LOG_FILE)
            if log_path.exists():
                with open(log_path, 'r') as f:
                    data = json.load(f)
                    self.recovery_history = [
                        RecoveryAttempt(**item) for item in data[-self.RECOVERY_LOG_MAX_ENTRIES:]
                    ]
                logger.info(f"Loaded {len(self.recovery_history)} recovery history entries")
        except Exception as e:
            logger.error(f"Failed to load recovery history: {e}")
            self.recovery_history = []
    
    def _save_recovery_history(self):
        """復旧履歴の保存"""
        try:
            log_path = Path(self.RECOVERY_LOG_FILE)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 最新エントリのみ保持
            recent_history = self.recovery_history[-self.RECOVERY_LOG_MAX_ENTRIES:]
            
            with open(log_path, 'w') as f:
                json.dump(
                    [asdict(attempt) for attempt in recent_history],
                    f,
                    indent=2
                )
        except Exception as e:
            logger.error(f"Failed to save recovery history: {e}")
    
    def check_session_health(self, session_id: int) -> bool:
        """
        セッション健康状態チェック
        
        Args:
            session_id: セッション番号
            
        Returns:
            bool: 健康フラグ（True: 正常、False: 異常）
        """
        try:
            # tmuxセッション存在確認
            if not self.tmux_manager.is_claude_session_exists(session_id):
                logger.warning(f"Session {session_id} tmux not found")
                return False
            
            # セッション設定確認
            if not self.session_manager.is_session_active(session_id):
                logger.warning(f"Session {session_id} not active in configuration")
                return False
            
            # プロセス応答性確認（拡張ポイント）
            # TODO: Claude CLIの応答確認機能追加
            
            return True
            
        except Exception as e:
            logger.error(f"Health check failed for session {session_id}: {e}")
            return False
    
    async def recover_session(self, session_id: int) -> bool:
        """
        セッション復旧実行（非同期）
        
        Args:
            session_id: セッション番号
            
        Returns:
            bool: 復旧成功フラグ
        """
        start_time = time.time()
        attempt_count = self.recovery_counts.get(session_id, 0) + 1
        
        if attempt_count > self.recovery_strategy.MAX_RETRY_ATTEMPTS:
            logger.error(f"Session {session_id} exceeded max recovery attempts")
            await self._notify_recovery_failure(session_id, "Max attempts exceeded")
            return False
        
        logger.info(f"Recovering session {session_id} (attempt {attempt_count}/{self.recovery_strategy.MAX_RETRY_ATTEMPTS})")
        
        # 指数バックオフ待機
        if attempt_count > 1:
            backoff_time = self.recovery_strategy.get_backoff_time(attempt_count)
            logger.info(f"Waiting {backoff_time}s before recovery attempt")
            await asyncio.sleep(backoff_time)
        
        # 復旧実行
        success = False
        error_message = None
        
        try:
            # 既存セッション終了
            if self.tmux_manager.is_claude_session_exists(session_id):
                self.tmux_manager.kill_claude_session(session_id)
                await asyncio.sleep(1)
            
            # 新規セッション作成
            work_dir = self.settings.get_claude_work_dir()
            claude_options = self.settings.get_claude_options()
            
            if self.tmux_manager.create_claude_session(session_id, work_dir, claude_options):
                await asyncio.sleep(2)  # 起動待機
                
                # 健康状態再確認
                if self.check_session_health(session_id):
                    success = True
                    self.recovery_counts[session_id] = 0  # カウンターリセット
                    logger.info(f"Successfully recovered session {session_id}")
                else:
                    error_message = "Health check failed after recovery"
            else:
                error_message = "Failed to create new tmux session"
                
        except Exception as e:
            error_message = str(e)
            logger.error(f"Recovery failed for session {session_id}: {e}")
        
        # 復旧記録追加
        duration = time.time() - start_time
        recovery_attempt = RecoveryAttempt(
            session_id=session_id,
            attempt_number=attempt_count,
            timestamp=datetime.now().isoformat(),
            success=success,
            error_message=error_message,
            recovery_duration=duration
        )
        
        self.recovery_history.append(recovery_attempt)
        self._save_recovery_history()
        
        if success:
            await self._notify_recovery_success(session_id, duration)
        else:
            self.recovery_counts[session_id] = attempt_count
            if attempt_count >= self.recovery_strategy.MAX_RETRY_ATTEMPTS:
                await self._notify_recovery_failure(session_id, error_message)
        
        return success
    
    async def _notify_recovery_success(self, session_id: int, duration: float):
        """復旧成功通知（Discord）"""
        try:
            message = f"✅ Session {session_id} recovered successfully (took {duration:.1f}s)"
            await self._send_discord_notification(message, session_id)
        except Exception as e:
            logger.error(f"Failed to send success notification: {e}")
    
    async def _notify_recovery_failure(self, session_id: int, error: Optional[str]):
        """復旧失敗通知（Discord）"""
        try:
            message = f"❌ Session {session_id} recovery failed: {error or 'Unknown error'}"
            await self._send_discord_notification(message, session_id)
        except Exception as e:
            logger.error(f"Failed to send failure notification: {e}")
    
    async def _send_discord_notification(self, message: str, session_id: int):
        """Discord通知送信"""
        try:
            # dpコマンド経由での通知
            channel_id = self.session_manager.get_channel_by_session(session_id)
            if channel_id:
                # TODO: Discord API直接呼び出しまたはdpコマンド統合
                logger.info(f"Discord notification: {message}")
        except Exception as e:
            logger.error(f"Discord notification failed: {e}")
    
    def _monitor_sessions(self):
        """セッション監視ループ（スレッド実行）"""
        logger.info("Starting session monitoring")
        
        while not self.stop_event.is_set():
            try:
                # 全アクティブセッション確認
                sessions = self.session_manager.list_sessions()
                
                for session_info in sessions:
                    if session_info.status != 'active':
                        continue
                    
                    session_id = session_info.session_id
                    
                    # 健康状態チェック
                    if not self.check_session_health(session_id):
                        logger.warning(f"Session {session_id} is unhealthy, initiating recovery")
                        
                        # 非同期復旧実行
                        asyncio.run(self.recover_session(session_id))
                
                # 次回チェックまで待機
                self.stop_event.wait(self.HEALTH_CHECK_INTERVAL)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(5)  # エラー時短縮待機
        
        logger.info("Session monitoring stopped")
    
    def start_monitoring(self):
        """監視開始"""
        if self.monitoring:
            logger.warning("Monitoring is already running")
            return
        
        self.monitoring = True
        self.stop_event.clear()
        
        # 監視スレッド起動
        self.monitor_thread = Thread(target=self._monitor_sessions, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Auto recovery system started")
    
    def stop_monitoring(self):
        """監視停止"""
        if not self.monitoring:
            return
        
        logger.info("Stopping auto recovery system...")
        self.monitoring = False
        self.stop_event.set()
        
        # スレッド終了待機
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("Auto recovery system stopped")
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """
        復旧統計情報取得
        
        Returns:
            Dict[str, Any]: 統計情報
        """
        total_attempts = len(self.recovery_history)
        successful_attempts = sum(1 for a in self.recovery_history if a.success)
        
        # 直近24時間の統計
        cutoff_time = datetime.now() - timedelta(hours=24)
        recent_attempts = [
            a for a in self.recovery_history
            if datetime.fromisoformat(a.timestamp) > cutoff_time
        ]
        
        return {
            'total_recovery_attempts': total_attempts,
            'successful_recoveries': successful_attempts,
            'success_rate': (successful_attempts / total_attempts * 100) if total_attempts > 0 else 0,
            'recent_24h_attempts': len(recent_attempts),
            'active_monitoring': self.monitoring,
            'sessions_with_issues': list(self.recovery_counts.keys())
        }

# テスト・デバッグ用関数
def test_auto_recovery():
    """AutoRecoverySystemのテスト"""
    recovery_system = AutoRecoverySystem()
    
    print("=== Auto Recovery System Test ===")
    
    # 統計表示
    stats = recovery_system.get_recovery_stats()
    print(f"Recovery stats: {json.dumps(stats, indent=2)}")
    
    # 監視開始
    recovery_system.start_monitoring()
    print("Monitoring started. Press Ctrl+C to stop...")
    
    try:
        time.sleep(60)  # 1分間テスト実行
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        recovery_system.stop_monitoring()
        print("Test completed")

if __name__ == "__main__":
    test_auto_recovery()