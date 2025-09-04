"""
SessionManager - セッション生命周期管理・階層制御
複数Claude Codeセッションの統括管理と階層的制御
"""

import json
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

class SessionStatus(Enum):
    """セッションステータス"""
    IDLE = "idle"
    BUSY = "busy"
    WAITING = "waiting"
    ERROR = "error"
    TERMINATED = "terminated"

class SessionRole(Enum):
    """セッション役割"""
    SUPREME = "supreme"  # 最高責任者
    COORDINATOR = "coordinator"  # 統括
    MANAGER = "manager"  # 管理署
    WORKER = "worker"  # 実装セッション

@dataclass
class SessionCapabilities:
    """セッション能力情報"""
    can_implement: bool = True
    can_review: bool = True
    can_test: bool = True
    can_deploy: bool = False
    can_manage: bool = False
    specializations: List[str] = None
    
    def __post_init__(self):
        if self.specializations is None:
            self.specializations = []

@dataclass
class SessionInfo:
    """セッション情報"""
    session_id: str
    role: SessionRole
    status: SessionStatus
    parent_id: Optional[str]
    children_ids: List[str]
    capabilities: SessionCapabilities
    created_at: datetime
    last_active: datetime
    current_task: Optional[str]
    metadata: Dict[str, Any]

@dataclass
class Task:
    """タスク情報"""
    task_id: str
    description: str
    priority: int
    assigned_to: Optional[str]
    created_by: str
    created_at: datetime
    deadline: Optional[datetime]
    dependencies: List[str]
    status: str

class SessionManager:
    """セッション管理クラス"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path or Path(__file__).parent.parent / 'config' / 'sessions.json'
        
        # セッション情報
        self.sessions: Dict[str, SessionInfo] = {}
        self.hierarchy: Dict[str, List[str]] = {}  # parent_id -> [child_ids]
        
        # タスク管理
        self.tasks: Dict[str, Task] = {}
        self.task_queue: List[str] = []
        
        # スレッドセーフティ
        self.lock = threading.Lock()
        
        # 設定読み込み
        self._load_config()
        
        # セッション監視スレッド
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_sessions, daemon=True)
        self.monitor_thread.start()
    
    def _load_config(self):
        """設定ファイルを読み込む"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                # 既存セッションの復元
                for session_data in config.get('sessions', []):
                    self._restore_session(session_data)
    
    def _restore_session(self, data: Dict[str, Any]):
        """セッション情報を復元"""
        # datetime文字列を変換
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_active'] = datetime.fromisoformat(data['last_active'])
        data['role'] = SessionRole(data['role'])
        data['status'] = SessionStatus(data['status'])
        data['capabilities'] = SessionCapabilities(**data['capabilities'])
        
        session = SessionInfo(**data)
        self.sessions[session.session_id] = session
        
        # 階層情報を更新
        if session.parent_id:
            if session.parent_id not in self.hierarchy:
                self.hierarchy[session.parent_id] = []
            self.hierarchy[session.parent_id].append(session.session_id)
    
    def create_session(self, session_id: str, role: SessionRole, 
                      parent_id: Optional[str] = None,
                      capabilities: Optional[SessionCapabilities] = None) -> SessionInfo:
        """新しいセッションを作成"""
        with self.lock:
            if session_id in self.sessions:
                raise ValueError(f"Session {session_id} already exists")
            
            # デフォルト能力設定
            if capabilities is None:
                capabilities = self._get_default_capabilities(role)
            
            # セッション情報作成
            session = SessionInfo(
                session_id=session_id,
                role=role,
                status=SessionStatus.IDLE,
                parent_id=parent_id,
                children_ids=[],
                capabilities=capabilities,
                created_at=datetime.now(),
                last_active=datetime.now(),
                current_task=None,
                metadata={}
            )
            
            # 登録
            self.sessions[session_id] = session
            
            # 階層情報更新
            if parent_id:
                if parent_id not in self.hierarchy:
                    self.hierarchy[parent_id] = []
                self.hierarchy[parent_id].append(session_id)
                
                # 親セッションの子リストを更新
                if parent_id in self.sessions:
                    self.sessions[parent_id].children_ids.append(session_id)
            
            self.logger.info(f"Created session {session_id} with role {role.value}")
            self._save_config()
            
            return session
    
    def destroy_session(self, session_id: str) -> bool:
        """セッションを破棄"""
        with self.lock:
            if session_id not in self.sessions:
                return False
            
            session = self.sessions[session_id]
            
            # 子セッションがある場合は警告
            if session.children_ids:
                self.logger.warning(f"Destroying session {session_id} with active children: {session.children_ids}")
            
            # 階層情報から削除
            if session.parent_id and session.parent_id in self.hierarchy:
                self.hierarchy[session.parent_id].remove(session_id)
            
            # 親セッションの子リストから削除
            if session.parent_id and session.parent_id in self.sessions:
                self.sessions[session.parent_id].children_ids.remove(session_id)
            
            # セッション削除
            del self.sessions[session_id]
            
            self.logger.info(f"Destroyed session {session_id}")
            self._save_config()
            
            return True
    
    def get_session_status(self, session_id: str) -> Optional[SessionStatus]:
        """セッションステータスを取得"""
        with self.lock:
            if session_id in self.sessions:
                return self.sessions[session_id].status
            return None
    
    def update_session_status(self, session_id: str, status: SessionStatus):
        """セッションステータスを更新"""
        with self.lock:
            if session_id in self.sessions:
                self.sessions[session_id].status = status
                self.sessions[session_id].last_active = datetime.now()
                self._save_config()
    
    def assign_task(self, task: Task, target_session: str) -> bool:
        """タスクをセッションに割り当て"""
        with self.lock:
            if target_session not in self.sessions:
                return False
            
            session = self.sessions[target_session]
            
            # セッションが利用可能か確認
            if session.status != SessionStatus.IDLE:
                self.logger.warning(f"Session {target_session} is not idle (status: {session.status.value})")
                return False
            
            # タスクを割り当て
            task.assigned_to = target_session
            self.tasks[task.task_id] = task
            
            # セッション状態を更新
            session.current_task = task.task_id
            session.status = SessionStatus.BUSY
            session.last_active = datetime.now()
            
            self.logger.info(f"Assigned task {task.task_id} to session {target_session}")
            self._save_config()
            
            return True
    
    def escalate_to_parent(self, session_id: str, task: Task) -> bool:
        """タスクを親セッションにエスカレート"""
        with self.lock:
            if session_id not in self.sessions:
                return False
            
            session = self.sessions[session_id]
            
            if not session.parent_id:
                self.logger.warning(f"Session {session_id} has no parent to escalate to")
                return False
            
            # 親セッションに割り当て
            return self.assign_task(task, session.parent_id)
    
    def get_available_sessions(self, role: Optional[SessionRole] = None) -> List[str]:
        """利用可能なセッションを取得"""
        with self.lock:
            available = []
            for session_id, session in self.sessions.items():
                if session.status == SessionStatus.IDLE:
                    if role is None or session.role == role:
                        available.append(session_id)
            return available
    
    def get_session_hierarchy(self) -> Dict[str, Any]:
        """セッション階層を取得"""
        with self.lock:
            # 最上位セッションを探す
            root_sessions = []
            for session_id, session in self.sessions.items():
                if session.parent_id is None:
                    root_sessions.append(session_id)
            
            # 階層構造を構築
            def build_tree(session_id: str) -> Dict[str, Any]:
                session = self.sessions[session_id]
                return {
                    "id": session_id,
                    "role": session.role.value,
                    "status": session.status.value,
                    "children": [build_tree(child_id) for child_id in session.children_ids]
                }
            
            return {
                "hierarchy": [build_tree(root_id) for root_id in root_sessions],
                "total_sessions": len(self.sessions),
                "active_sessions": sum(1 for s in self.sessions.values() if s.status == SessionStatus.BUSY)
            }
    
    def find_best_session_for_task(self, task: Task) -> Optional[str]:
        """タスクに最適なセッションを見つける"""
        with self.lock:
            candidates = []
            
            for session_id, session in self.sessions.items():
                if session.status != SessionStatus.IDLE:
                    continue
                
                # 能力マッチングスコアを計算
                score = 0
                
                # タスク要件と能力のマッチング
                if "implementation" in task.description.lower() and session.capabilities.can_implement:
                    score += 10
                if "review" in task.description.lower() and session.capabilities.can_review:
                    score += 10
                if "test" in task.description.lower() and session.capabilities.can_test:
                    score += 10
                
                # 役割による優先度
                if session.role == SessionRole.WORKER:
                    score += 5  # 実装タスクは通常ワーカーに
                
                if score > 0:
                    candidates.append((session_id, score))
            
            if candidates:
                # スコアが最も高いセッションを選択
                candidates.sort(key=lambda x: x[1], reverse=True)
                return candidates[0][0]
            
            return None
    
    def _get_default_capabilities(self, role: SessionRole) -> SessionCapabilities:
        """役割に基づくデフォルト能力を取得"""
        if role == SessionRole.SUPREME:
            return SessionCapabilities(
                can_implement=False,
                can_review=True,
                can_test=False,
                can_deploy=True,
                can_manage=True,
                specializations=["decision_making", "strategy"]
            )
        elif role == SessionRole.COORDINATOR:
            return SessionCapabilities(
                can_implement=True,
                can_review=True,
                can_test=True,
                can_deploy=False,
                can_manage=True,
                specializations=["coordination", "planning"]
            )
        elif role == SessionRole.MANAGER:
            return SessionCapabilities(
                can_implement=True,
                can_review=True,
                can_test=True,
                can_deploy=False,
                can_manage=True,
                specializations=["task_management", "quality_control"]
            )
        else:  # WORKER
            return SessionCapabilities(
                can_implement=True,
                can_review=True,
                can_test=True,
                can_deploy=False,
                can_manage=False,
                specializations=["coding", "testing"]
            )
    
    def _monitor_sessions(self):
        """セッションを監視（バックグラウンドスレッド）"""
        while self.monitoring:
            try:
                with self.lock:
                    now = datetime.now()
                    for session_id, session in self.sessions.items():
                        # タイムアウトチェック（30分）
                        if session.status == SessionStatus.BUSY:
                            if now - session.last_active > timedelta(minutes=30):
                                self.logger.warning(f"Session {session_id} appears to be stuck")
                                session.status = SessionStatus.ERROR
                
                # 30秒ごとに監視
                threading.Event().wait(30)
                
            except Exception as e:
                self.logger.error(f"Monitor thread error: {e}")
    
    def _save_config(self):
        """設定をファイルに保存"""
        config = {
            "sessions": [],
            "updated_at": datetime.now().isoformat()
        }
        
        for session in self.sessions.values():
            session_data = asdict(session)
            # datetime オブジェクトを文字列に変換
            session_data['created_at'] = session.created_at.isoformat()
            session_data['last_active'] = session.last_active.isoformat()
            session_data['role'] = session.role.value
            session_data['status'] = session.status.value
            session_data['capabilities'] = asdict(session.capabilities)
            
            config['sessions'].append(session_data)
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def shutdown(self):
        """マネージャーをシャットダウン"""
        self.monitoring = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        self._save_config()
        self.logger.info("SessionManager shutdown complete")