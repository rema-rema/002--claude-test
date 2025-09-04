"""
QueueManager - 依頼書管理システム
Queue/Active/Completed方式による依頼書のライフサイクル管理
"""

import json
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import threading

class RequestStatus(Enum):
    """依頼書ステータス"""
    QUEUED = "queued"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Priority(Enum):
    """優先度"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

@dataclass
class WorkRequest:
    """作業依頼書データクラス"""
    request_id: str
    session_id: str
    target_session: str
    priority: Priority
    task_description: str
    requirements: List[str]
    deadline: Optional[datetime]
    dependencies: List[str]
    created_at: datetime
    status: RequestStatus
    metadata: Dict[str, Any]

@dataclass
class WorkResult:
    """作業結果データクラス"""
    request_id: str
    session_id: str
    status: str  # success, failure, partial
    summary: str
    details: Dict[str, Any]
    completed_at: datetime
    artifacts: List[str]  # 生成されたファイルやリソース

@dataclass
class ConflictInfo:
    """衝突情報データクラス"""
    request_id: str
    conflict_type: str  # resource, dependency, session
    description: str
    resolution_suggestion: str

class QueueManager:
    """依頼書管理クラス"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        self.base_dir = base_dir or Path(__file__).parent.parent
        
        # ディレクトリ設定
        self.queue_dir = self.base_dir / 'queue'
        self.active_dir = self.base_dir / 'active'
        self.completed_dir = self.base_dir / 'completed'
        
        # ディレクトリ作成
        for dir_path in [self.queue_dir, self.active_dir, self.completed_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # セッション別アクティブリクエスト追跡
        self.active_requests: Dict[str, str] = {}  # session_id -> request_id
        self.lock = threading.Lock()  # スレッドセーフティ
    
    def generate_request_id(self, session_id: str, task: str) -> str:
        """一意のリクエストIDを生成"""
        timestamp = datetime.now().isoformat()
        content = f"{session_id}_{task}_{timestamp}"
        hash_obj = hashlib.md5(content.encode())
        return f"REQ_{hash_obj.hexdigest()[:8]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def enqueue_request(self, request: WorkRequest) -> str:
        """依頼書をキューに追加"""
        with self.lock:
            # 衝突チェック
            conflicts = self.check_conflicts(request.target_session)
            if conflicts:
                self.logger.warning(f"Conflicts detected for request {request.request_id}: {conflicts}")
            
            # 依頼書をJSON形式で保存
            request_file = self.queue_dir / f"{request.request_id}.json"
            request_data = asdict(request)
            
            # datetime オブジェクトを文字列に変換
            if request.deadline:
                request_data['deadline'] = request.deadline.isoformat()
            request_data['created_at'] = request.created_at.isoformat()
            request_data['priority'] = request.priority.value
            request_data['status'] = request.status.value
            
            with open(request_file, 'w') as f:
                json.dump(request_data, f, indent=2)
            
            self.logger.info(f"Enqueued request {request.request_id} for session {request.target_session}")
            return request.request_id
    
    def dequeue_request(self, session_id: str) -> Optional[WorkRequest]:
        """セッション用の次の依頼書を取得"""
        with self.lock:
            # 既にアクティブなリクエストがある場合はNone
            if session_id in self.active_requests:
                self.logger.info(f"Session {session_id} already has active request")
                return None
            
            # 優先度順にキュー内の依頼書を検索
            queue_files = sorted(self.queue_dir.glob("*.json"))
            
            for request_file in queue_files:
                with open(request_file, 'r') as f:
                    request_data = json.load(f)
                
                # 対象セッションの依頼書を探す
                if request_data['target_session'] == session_id:
                    # WorkRequestオブジェクトを再構築
                    request = self._reconstruct_request(request_data)
                    
                    # アクティブに移動
                    if self.move_to_active(request.request_id, session_id):
                        return request
            
            return None
    
    def move_to_active(self, request_id: str, session_id: str) -> bool:
        """依頼書をアクティブディレクトリに移動"""
        with self.lock:
            try:
                source = self.queue_dir / f"{request_id}.json"
                destination = self.active_dir / f"{request_id}.json"
                
                if not source.exists():
                    self.logger.error(f"Request {request_id} not found in queue")
                    return False
                
                # ファイルを移動
                shutil.move(str(source), str(destination))
                
                # アクティブリクエストを記録
                self.active_requests[session_id] = request_id
                
                # ステータスを更新
                self._update_request_status(destination, RequestStatus.ACTIVE)
                
                self.logger.info(f"Moved request {request_id} to active for session {session_id}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to move request {request_id} to active: {e}")
                return False
    
    def complete_request(self, request_id: str, result: WorkResult) -> bool:
        """依頼書を完了としてマーク"""
        with self.lock:
            try:
                source = self.active_dir / f"{request_id}.json"
                destination = self.completed_dir / f"{request_id}.json"
                
                if not source.exists():
                    self.logger.error(f"Request {request_id} not found in active")
                    return False
                
                # 結果を依頼書に追加
                with open(source, 'r') as f:
                    request_data = json.load(f)
                
                request_data['result'] = asdict(result)
                request_data['result']['completed_at'] = result.completed_at.isoformat()
                request_data['status'] = RequestStatus.COMPLETED.value
                
                # 完了ディレクトリに保存
                with open(destination, 'w') as f:
                    json.dump(request_data, f, indent=2)
                
                # 元のファイルを削除
                source.unlink()
                
                # アクティブリクエストから削除
                session_id = request_data.get('session_id')
                if session_id in self.active_requests:
                    del self.active_requests[session_id]
                
                self.logger.info(f"Completed request {request_id}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to complete request {request_id}: {e}")
                return False
    
    def check_conflicts(self, session_id: str) -> List[ConflictInfo]:
        """セッションの衝突をチェック"""
        conflicts = []
        
        # アクティブリクエストの衝突チェック
        if session_id in self.active_requests:
            conflicts.append(ConflictInfo(
                request_id=self.active_requests[session_id],
                conflict_type="session",
                description=f"Session {session_id} already has an active request",
                resolution_suggestion="Wait for current request to complete or cancel it"
            ))
        
        # キュー内の同一セッション向け依頼書をチェック
        queue_count = 0
        for request_file in self.queue_dir.glob("*.json"):
            with open(request_file, 'r') as f:
                request_data = json.load(f)
                if request_data.get('target_session') == session_id:
                    queue_count += 1
        
        if queue_count > 3:  # 閾値
            conflicts.append(ConflictInfo(
                request_id="N/A",
                conflict_type="resource",
                description=f"Session {session_id} has {queue_count} pending requests",
                resolution_suggestion="Consider distributing load to other sessions"
            ))
        
        return conflicts
    
    def get_queue_status(self) -> Dict[str, Any]:
        """キューの状態を取得"""
        with self.lock:
            queue_count = len(list(self.queue_dir.glob("*.json")))
            active_count = len(list(self.active_dir.glob("*.json")))
            completed_count = len(list(self.completed_dir.glob("*.json")))
            
            return {
                "queue": queue_count,
                "active": active_count,
                "completed": completed_count,
                "active_sessions": list(self.active_requests.keys()),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_request_history(self, session_id: Optional[str] = None, 
                           limit: int = 10) -> List[Dict[str, Any]]:
        """依頼書履歴を取得"""
        history = []
        
        # 完了済み依頼書を取得
        completed_files = sorted(
            self.completed_dir.glob("*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )[:limit]
        
        for request_file in completed_files:
            with open(request_file, 'r') as f:
                request_data = json.load(f)
                
                if session_id is None or request_data.get('session_id') == session_id:
                    history.append(request_data)
        
        return history
    
    def cancel_request(self, request_id: str) -> bool:
        """依頼書をキャンセル"""
        with self.lock:
            # キューから削除
            queue_file = self.queue_dir / f"{request_id}.json"
            if queue_file.exists():
                queue_file.unlink()
                self.logger.info(f"Cancelled queued request {request_id}")
                return True
            
            # アクティブから削除（完了扱い）
            active_file = self.active_dir / f"{request_id}.json"
            if active_file.exists():
                # キャンセル結果を作成
                result = WorkResult(
                    request_id=request_id,
                    session_id="system",
                    status="cancelled",
                    summary="Request was cancelled",
                    details={"reason": "Manual cancellation"},
                    completed_at=datetime.now(),
                    artifacts=[]
                )
                return self.complete_request(request_id, result)
            
            return False
    
    def _reconstruct_request(self, data: Dict[str, Any]) -> WorkRequest:
        """JSONデータからWorkRequestを再構築"""
        # datetime文字列を変換
        if data.get('deadline'):
            data['deadline'] = datetime.fromisoformat(data['deadline'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['priority'] = Priority(data['priority'])
        data['status'] = RequestStatus(data['status'])
        
        return WorkRequest(**data)
    
    def _update_request_status(self, request_file: Path, status: RequestStatus):
        """依頼書のステータスを更新"""
        with open(request_file, 'r') as f:
            request_data = json.load(f)
        
        request_data['status'] = status.value
        
        with open(request_file, 'w') as f:
            json.dump(request_data, f, indent=2)