#!/usr/bin/env python3
"""
Resource Monitor - リソース使用量監視システム

このモジュールは以下の責任を持つ：
1. CPU/メモリ/ディスク使用量の定期監視
2. セッション別リソース使用量追跡
3. メトリクスの永続化と履歴管理
4. 閾値超過時のアラート発行
5. リソース使用傾向の分析

拡張性のポイント：
- カスタムメトリクス追加
- 外部監視システム連携（Prometheus等）
- 予測分析機能
- 自動スケーリング連携
"""

import os
import sys
import json
import psutil
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from threading import Thread, Event
import subprocess

# パッケージルートの追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.session_manager import SessionManager
from src.tmux_manager import TmuxManager
from config.settings import SettingsManager

# ログ設定
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@dataclass
class ResourceMetrics:
    """リソース使用量メトリクス"""
    timestamp: str
    session_id: Optional[int]
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_used_gb: float
    disk_percent: float
    process_count: int
    network_sent_mb: float
    network_recv_mb: float

@dataclass 
class AlertThreshold:
    """アラート閾値設定"""
    cpu_percent: float = 80.0
    memory_percent: float = 85.0
    disk_percent: float = 90.0
    
    def check_threshold(self, metrics: ResourceMetrics) -> List[str]:
        """
        閾値チェック
        
        Returns:
            List[str]: 超過した項目のリスト
        """
        violations = []
        
        if metrics.cpu_percent > self.cpu_percent:
            violations.append(f"CPU: {metrics.cpu_percent:.1f}% > {self.cpu_percent}%")
        
        if metrics.memory_percent > self.memory_percent:
            violations.append(f"Memory: {metrics.memory_percent:.1f}% > {self.memory_percent}%")
        
        if metrics.disk_percent > self.disk_percent:
            violations.append(f"Disk: {metrics.disk_percent:.1f}% > {self.disk_percent}%")
        
        return violations

class ResourceMonitor:
    """
    リソース監視システム
    
    アーキテクチャ特徴：
    - 低オーバーヘッド監視
    - 時系列データ管理
    - セッション別リソース追跡
    - 自動アラート機能
    - メトリクス永続化
    
    拡張可能要素：
    - GPU使用量監視
    - ネットワーク帯域詳細分析
    - コンテナ別リソース監視
    - クラウドリソース統合
    """
    
    # 監視設定
    MONITOR_INTERVAL = 300  # 5分間隔
    METRICS_FILE = "metrics.json"
    METRICS_RETENTION_DAYS = 7
    MAX_METRICS_ENTRIES = 10000
    
    def __init__(self):
        """
        ResourceMonitorの初期化
        """
        self.session_manager = SessionManager()
        self.tmux_manager = TmuxManager()
        self.settings = SettingsManager()
        
        # メトリクス管理
        self.metrics_history: List[ResourceMetrics] = []
        self.alert_threshold = AlertThreshold()
        
        # 監視制御
        self.monitoring = False
        self.stop_event = Event()
        self.monitor_thread: Optional[Thread] = None
        
        # ネットワーク使用量ベースライン
        self.network_baseline = self._get_network_stats()
        
        # メトリクス履歴ロード
        self._load_metrics()
    
    def _load_metrics(self):
        """メトリクス履歴の読み込み"""
        try:
            metrics_path = Path(self.METRICS_FILE)
            if metrics_path.exists():
                with open(metrics_path, 'r') as f:
                    data = json.load(f)
                    
                    # 保持期間内のデータのみ読み込み
                    cutoff = datetime.now() - timedelta(days=self.METRICS_RETENTION_DAYS)
                    
                    self.metrics_history = [
                        ResourceMetrics(**item) for item in data
                        if datetime.fromisoformat(item['timestamp']) > cutoff
                    ][-self.MAX_METRICS_ENTRIES:]
                    
                logger.info(f"Loaded {len(self.metrics_history)} metrics entries")
        except Exception as e:
            logger.error(f"Failed to load metrics: {e}")
            self.metrics_history = []
    
    def _save_metrics(self):
        """メトリクスの永続化"""
        try:
            metrics_path = Path(self.METRICS_FILE)
            
            # 保持期間とエントリ数制限
            cutoff = datetime.now() - timedelta(days=self.METRICS_RETENTION_DAYS)
            recent_metrics = [
                m for m in self.metrics_history
                if datetime.fromisoformat(m.timestamp) > cutoff
            ][-self.MAX_METRICS_ENTRIES:]
            
            with open(metrics_path, 'w') as f:
                json.dump(
                    [asdict(m) for m in recent_metrics],
                    f,
                    indent=2
                )
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    def _get_network_stats(self) -> Dict[str, float]:
        """ネットワーク統計取得"""
        try:
            stats = psutil.net_io_counters()
            return {
                'sent_mb': stats.bytes_sent / (1024 * 1024),
                'recv_mb': stats.bytes_recv / (1024 * 1024)
            }
        except Exception as e:
            logger.error(f"Failed to get network stats: {e}")
            return {'sent_mb': 0, 'recv_mb': 0}
    
    def get_system_metrics(self) -> ResourceMetrics:
        """
        システム全体のメトリクス取得
        
        Returns:
            ResourceMetrics: システムメトリクス
        """
        try:
            # CPU使用率（1秒間隔で測定）
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # メモリ使用量
            memory = psutil.virtual_memory()
            memory_mb = memory.used / (1024 * 1024)
            memory_percent = memory.percent
            
            # ディスク使用量
            disk = psutil.disk_usage('/')
            disk_used_gb = disk.used / (1024 * 1024 * 1024)
            disk_percent = disk.percent
            
            # プロセス数
            process_count = len(psutil.pids())
            
            # ネットワーク使用量（差分）
            current_network = self._get_network_stats()
            network_sent = current_network['sent_mb'] - self.network_baseline['sent_mb']
            network_recv = current_network['recv_mb'] - self.network_baseline['recv_mb']
            
            return ResourceMetrics(
                timestamp=datetime.now().isoformat(),
                session_id=None,  # システム全体
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                memory_percent=memory_percent,
                disk_used_gb=disk_used_gb,
                disk_percent=disk_percent,
                process_count=process_count,
                network_sent_mb=network_sent,
                network_recv_mb=network_recv
            )
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return ResourceMetrics(
                timestamp=datetime.now().isoformat(),
                session_id=None,
                cpu_percent=0, memory_mb=0, memory_percent=0,
                disk_used_gb=0, disk_percent=0, process_count=0,
                network_sent_mb=0, network_recv_mb=0
            )
    
    def get_session_metrics(self, session_id: int) -> Optional[ResourceMetrics]:
        """
        セッション別メトリクス取得
        
        Args:
            session_id: セッション番号
            
        Returns:
            Optional[ResourceMetrics]: セッションメトリクス
        """
        try:
            # tmuxセッション名取得
            session_name = f"claude-session-{session_id}"
            
            # tmux pane のPID取得
            result = subprocess.run(
                ["tmux", "list-panes", "-t", session_name, "-F", "#{pane_pid}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return None
            
            pids = [int(pid) for pid in result.stdout.strip().split('\n') if pid]
            
            # プロセスメトリクス集計
            total_cpu = 0
            total_memory_mb = 0
            process_count = 0
            
            for pid in pids:
                try:
                    process = psutil.Process(pid)
                    
                    # CPU使用率
                    total_cpu += process.cpu_percent(interval=0.1)
                    
                    # メモリ使用量
                    memory_info = process.memory_info()
                    total_memory_mb += memory_info.rss / (1024 * 1024)
                    
                    # 子プロセス含む
                    for child in process.children(recursive=True):
                        total_cpu += child.cpu_percent(interval=0.1)
                        child_memory = child.memory_info()
                        total_memory_mb += child_memory.rss / (1024 * 1024)
                        process_count += 1
                    
                    process_count += 1
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # システムメトリクスと組み合わせ
            system_memory = psutil.virtual_memory()
            memory_percent = (total_memory_mb * 1024 * 1024) / system_memory.total * 100
            
            return ResourceMetrics(
                timestamp=datetime.now().isoformat(),
                session_id=session_id,
                cpu_percent=total_cpu,
                memory_mb=total_memory_mb,
                memory_percent=memory_percent,
                disk_used_gb=0,  # セッション固有ディスクは未実装
                disk_percent=0,
                process_count=process_count,
                network_sent_mb=0,  # セッション固有ネットワークは未実装
                network_recv_mb=0
            )
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id} metrics: {e}")
            return None
    
    async def check_and_alert(self, metrics: ResourceMetrics):
        """
        閾値チェックとアラート送信
        
        Args:
            metrics: チェック対象メトリクス
        """
        violations = self.alert_threshold.check_threshold(metrics)
        
        if violations:
            session_info = f"Session {metrics.session_id}" if metrics.session_id else "System"
            alert_message = f"⚠️ Resource Alert for {session_info}:\n" + "\n".join(violations)
            
            logger.warning(alert_message)
            
            # Discord通知
            await self._send_discord_alert(alert_message, metrics.session_id)
    
    async def _send_discord_alert(self, message: str, session_id: Optional[int]):
        """Discord アラート送信"""
        try:
            # TODO: Discord APIまたはdpコマンド統合
            logger.info(f"Discord alert: {message}")
        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
    
    def _monitor_loop(self):
        """監視ループ（スレッド実行）"""
        logger.info("Starting resource monitoring")
        
        while not self.stop_event.is_set():
            try:
                # システム全体メトリクス
                system_metrics = self.get_system_metrics()
                self.metrics_history.append(system_metrics)
                
                # 閾値チェック
                asyncio.run(self.check_and_alert(system_metrics))
                
                # セッション別メトリクス
                sessions = self.session_manager.list_sessions()
                for session_info in sessions:
                    if session_info.status != 'active':
                        continue
                    
                    session_metrics = self.get_session_metrics(session_info.session_id)
                    if session_metrics:
                        self.metrics_history.append(session_metrics)
                        asyncio.run(self.check_and_alert(session_metrics))
                
                # メトリクス保存
                self._save_metrics()
                
                # 次回監視まで待機
                self.stop_event.wait(self.MONITOR_INTERVAL)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(30)
        
        logger.info("Resource monitoring stopped")
    
    def start_monitoring(self):
        """監視開始"""
        if self.monitoring:
            logger.warning("Monitoring is already running")
            return
        
        self.monitoring = True
        self.stop_event.clear()
        
        # 監視スレッド起動
        self.monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Resource monitor started")
    
    def stop_monitoring(self):
        """監視停止"""
        if not self.monitoring:
            return
        
        logger.info("Stopping resource monitor...")
        self.monitoring = False
        self.stop_event.set()
        
        # スレッド終了待機
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("Resource monitor stopped")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        統計情報取得
        
        Returns:
            Dict[str, Any]: リソース使用統計
        """
        if not self.metrics_history:
            return {
                'total_metrics': 0,
                'monitoring_active': self.monitoring
            }
        
        # 直近24時間の統計
        cutoff = datetime.now() - timedelta(hours=24)
        recent_metrics = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m.timestamp) > cutoff
        ]
        
        if recent_metrics:
            avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
            max_cpu = max(m.cpu_percent for m in recent_metrics)
            max_memory = max(m.memory_percent for m in recent_metrics)
        else:
            avg_cpu = avg_memory = max_cpu = max_memory = 0
        
        return {
            'total_metrics': len(self.metrics_history),
            'recent_24h_metrics': len(recent_metrics),
            'avg_cpu_percent': avg_cpu,
            'avg_memory_percent': avg_memory,
            'max_cpu_percent': max_cpu,
            'max_memory_percent': max_memory,
            'monitoring_active': self.monitoring,
            'alert_threshold': asdict(self.alert_threshold)
        }

# テスト・デバッグ用
import time

def test_resource_monitor():
    """ResourceMonitorのテスト"""
    monitor = ResourceMonitor()
    
    print("=== Resource Monitor Test ===")
    
    # システムメトリクス取得
    metrics = monitor.get_system_metrics()
    print(f"System metrics:")
    print(f"  CPU: {metrics.cpu_percent:.1f}%")
    print(f"  Memory: {metrics.memory_mb:.1f}MB ({metrics.memory_percent:.1f}%)")
    print(f"  Disk: {metrics.disk_used_gb:.1f}GB ({metrics.disk_percent:.1f}%)")
    print(f"  Processes: {metrics.process_count}")
    
    # 統計表示
    stats = monitor.get_statistics()
    print(f"\nStatistics: {json.dumps(stats, indent=2)}")
    
    # 監視テスト
    print("\nStarting monitoring...")
    monitor.start_monitoring()
    
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        monitor.stop_monitoring()
        print("Test completed")

if __name__ == "__main__":
    test_resource_monitor()