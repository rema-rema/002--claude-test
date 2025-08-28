#!/usr/bin/env python3
"""
Session Manager - マルチセッション管理システム

このモジュールは以下の責任を持つ：
1. セッションのライフサイクル管理
2. チャンネル→セッション番号マッピング
3. 動的セッション追加・削除
4. セッション状態監視
5. sessions.json設定管理
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# パッケージルートの追加（相対インポート対応）
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import SettingsManager

# ログ設定
logger = logging.getLogger(__name__)

@dataclass
class SessionInfo:
    """
    セッション情報管理用データクラス
    
    将来の拡張ポイント：
    - セッション別権限設定
    - セッション作成者情報
    - セッション用途・目的
    - 最終アクセス時刻
    """
    session_id: int
    channel_id: str
    created_at: str
    status: str = "active"  # active, inactive, error
    last_health_check: Optional[str] = None

class SessionManagerError(Exception):
    """SessionManager固有エラー"""
    pass

class SessionManager:
    """
    マルチセッション管理の統合クラス
    
    アーキテクチャ特徴：
    - 設定駆動によるセッション管理
    - 例外安全性を保証するトランザクション処理
    - 拡張性を考慮した動的セッション管理
    - 堅牢なエラーハンドリング
    """
    
    def __init__(self):
        """
        セッションマネージャーの初期化
        """
        try:
            self.settings = SettingsManager()
            self.sessions_cache = {}  # {session_id: SessionInfo}
            self.channel_map = {}     # {channel_id: session_id}
            self._load_sessions()
            logger.info("SessionManager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SessionManager: {e}")
            raise SessionManagerError(f"Initialization failed: {e}")
    
    def _load_sessions(self):
        """
        sessions.jsonからセッション情報を読み込み、内部キャッシュを構築
        
        拡張ポイント：
        - 暗号化されたsessions.jsonの復号化
        - セッション情報の検証・修復
        - 不正セッションの自動除去
        """
        try:
            sessions_data = self.settings.load_sessions()
            self.sessions_cache.clear()
            self.channel_map.clear()
            
            for session_str, channel_id in sessions_data.items():
                if not session_str.isdigit():
                    logger.warning(f"Invalid session ID format: {session_str}")
                    continue
                    
                session_id = int(session_str)
                session_info = SessionInfo(
                    session_id=session_id,
                    channel_id=channel_id,
                    created_at=datetime.now().isoformat(),
                    status="active"
                )
                
                self.sessions_cache[session_id] = session_info
                self.channel_map[channel_id] = session_id
                
            logger.info(f"Loaded {len(self.sessions_cache)} sessions from config")
            
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
            # 空の状態で初期化（エラー時の安全な状態）
            self.sessions_cache = {}
            self.channel_map = {}
    
    def _save_sessions(self):
        """
        内部キャッシュをsessions.jsonに永続化
        
        拡張ポイント：
        - 暗号化保存機能
        - バックアップ作成
        - 原子的書き込み保証
        """
        try:
            sessions_dict = {
                str(info.session_id): info.channel_id 
                for info in self.sessions_cache.values()
                if info.status == "active"
            }
            
            self.settings.save_sessions(sessions_dict)
            logger.info(f"Saved {len(sessions_dict)} active sessions to config")
            
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")
            raise SessionManagerError(f"Session save failed: {e}")
    
    def get_session_by_channel(self, channel_id: str) -> Optional[int]:
        """
        チャンネルIDからセッション番号を取得
        
        Args:
            channel_id: DiscordチャンネルID
            
        Returns:
            Optional[int]: セッション番号（見つからない場合はNone）
        """
        session_id = self.channel_map.get(channel_id)
        if session_id and session_id in self.sessions_cache:
            session_info = self.sessions_cache[session_id]
            if session_info.status == "active":
                return session_id
        
        logger.debug(f"No active session found for channel: {channel_id}")
        return None
    
    def get_channel_by_session(self, session_id: int) -> Optional[str]:
        """
        セッション番号からチャンネルIDを取得
        
        Args:
            session_id: セッション番号
            
        Returns:
            Optional[str]: チャンネルID（見つからない場合はNone）
        """
        if session_id in self.sessions_cache:
            session_info = self.sessions_cache[session_id]
            if session_info.status == "active":
                return session_info.channel_id
        
        logger.debug(f"No active channel found for session: {session_id}")
        return None
    
    def add_session(self, channel_id: str) -> int:
        """
        新規セッションの動的追加
        
        拡張ポイント：
        - セッション作成権限チェック
        - チャンネル存在確認
        - セッション設定のカスタマイズ
        
        Args:
            channel_id: DiscordチャンネルID
            
        Returns:
            int: 新規作成されたセッション番号
            
        Raises:
            SessionManagerError: セッション作成失敗時
        """
        try:
            # 既存チャンネルIDのチェック
            if channel_id in self.channel_map:
                existing_session = self.channel_map[channel_id]
                raise SessionManagerError(
                    f"Channel {channel_id} is already mapped to session {existing_session}"
                )
            
            # バックアップ作成（例外安全性）
            backup_sessions = dict(self.sessions_cache)
            backup_channel_map = dict(self.channel_map)
            
            # 次のセッション番号を決定
            existing_session_ids = list(self.sessions_cache.keys())
            new_session_id = 1 if not existing_session_ids else max(existing_session_ids) + 1
            
            # セッション情報作成
            session_info = SessionInfo(
                session_id=new_session_id,
                channel_id=channel_id,
                created_at=datetime.now().isoformat(),
                status="active"
            )
            
            # アトミック更新
            self.sessions_cache[new_session_id] = session_info
            self.channel_map[channel_id] = new_session_id
            
            # 永続化
            self._save_sessions()
            
            logger.info(f"Successfully added session {new_session_id} for channel {channel_id}")
            return new_session_id
            
        except SessionManagerError:
            raise
        except Exception as e:
            # ロールバック
            self.sessions_cache = backup_sessions
            self.channel_map = backup_channel_map
            logger.error(f"Failed to add session for channel {channel_id}: {e}")
            raise SessionManagerError(f"Session creation failed: {e}")
    
    def remove_session(self, session_id: int) -> bool:
        """
        セッションの削除（将来拡張機能）
        
        Args:
            session_id: 削除するセッション番号
            
        Returns:
            bool: 削除成功フラグ
        """
        try:
            if session_id not in self.sessions_cache:
                logger.warning(f"Session {session_id} not found for removal")
                return False
            
            # バックアップ作成
            backup_sessions = dict(self.sessions_cache)
            backup_channel_map = dict(self.channel_map)
            
            # セッション情報を取得
            session_info = self.sessions_cache[session_id]
            
            # マッピングから削除
            if session_info.channel_id in self.channel_map:
                del self.channel_map[session_info.channel_id]
            
            # セッションキャッシュから削除
            del self.sessions_cache[session_id]
            
            # 永続化
            self._save_sessions()
            
            logger.info(f"Successfully removed session {session_id}")
            return True
            
        except Exception as e:
            # ロールバック
            self.sessions_cache = backup_sessions
            self.channel_map = backup_channel_map
            logger.error(f"Failed to remove session {session_id}: {e}")
            return False
    
    def list_sessions(self) -> List[SessionInfo]:
        """
        全セッション情報のリスト取得
        
        Returns:
            List[SessionInfo]: セッション情報のリスト（セッション番号順）
        """
        return sorted(
            self.sessions_cache.values(),
            key=lambda x: x.session_id
        )
    
    def get_default_session(self) -> int:
        """
        デフォルトセッション番号を取得
        
        Returns:
            int: デフォルトセッション番号（通常は1）
        """
        return self.settings.get_default_session()
    
    def update_session_health(self, session_id: int, is_healthy: bool):
        """
        セッションの健康状態を更新
        
        Args:
            session_id: セッション番号
            is_healthy: 健康状態
        """
        if session_id in self.sessions_cache:
            session_info = self.sessions_cache[session_id]
            session_info.last_health_check = datetime.now().isoformat()
            session_info.status = "active" if is_healthy else "error"
            
            logger.debug(f"Updated health for session {session_id}: {'healthy' if is_healthy else 'error'}")
    
    def get_session_count(self) -> int:
        """
        アクティブセッション数を取得
        
        Returns:
            int: アクティブセッション数
        """
        return len([s for s in self.sessions_cache.values() if s.status == "active"])
    
    def is_session_active(self, session_id: int) -> bool:
        """
        セッションがアクティブかチェック
        
        Args:
            session_id: セッション番号
            
        Returns:
            bool: アクティブフラグ
        """
        if session_id in self.sessions_cache:
            return self.sessions_cache[session_id].status == "active"
        return False
    
    def get_stats(self) -> Dict:
        """
        セッション統計情報を取得
        
        Returns:
            Dict: 統計情報
        """
        active_count = len([s for s in self.sessions_cache.values() if s.status == "active"])
        error_count = len([s for s in self.sessions_cache.values() if s.status == "error"])
        
        return {
            "total_sessions": len(self.sessions_cache),
            "active_sessions": active_count,
            "error_sessions": error_count,
            "channels_mapped": len(self.channel_map),
            "last_updated": datetime.now().isoformat()
        }

# テスト・デバッグ用関数
def test_session_manager():
    """
    SessionManagerの動作テスト
    """
    try:
        # インスタンス作成
        manager = SessionManager()
        
        print(f"Default session: {manager.get_default_session()}")
        print(f"Session count: {manager.get_session_count()}")
        
        # セッション一覧表示
        sessions = manager.list_sessions()
        print(f"Current sessions:")
        for session in sessions:
            print(f"  Session {session.session_id}: {session.channel_id} ({session.status})")
        
        # 統計情報表示
        stats = manager.get_stats()
        print(f"Stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    test_session_manager()