"""
HooksManager - Claude Code Hooks統合管理
PostToolUse, PreToolUse, Notification, Stop hookの処理と完了検知
"""

import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass

@dataclass
class CompletionSignal:
    """完了信号データクラス"""
    type: str  # todo_completion, serena_completion, etc.
    timestamp: datetime
    session_id: str
    context: Dict[str, Any]
    raw_output: str

@dataclass
class HookContext:
    """Hookコンテキストデータクラス"""
    hook_type: str  # PostToolUse, PreToolUse, etc.
    session_id: str
    tool_name: Optional[str]
    tool_output: Optional[str]
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class HookResult:
    """Hook処理結果データクラス"""
    success: bool
    should_block: bool  # PreToolUse用
    message: Optional[str]
    actions: List[Dict[str, Any]]  # 実行すべきアクション

@dataclass
class Report:
    """完了報告書データクラス"""
    session_id: str
    completion_type: str
    timestamp: datetime
    summary: str
    details: Dict[str, Any]
    next_actions: List[str]

class HooksManager:
    """Claude Code Hooks統合管理クラス"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path or Path(__file__).parent.parent / 'config' / 'hooks.json'
        self.config = self._load_config()
        self.patterns = self._compile_patterns()
        self.handlers: Dict[str, List[Callable]] = {
            'PostToolUse': [],
            'PreToolUse': [],
            'Notification': [],
            'Stop': []
        }
        self._register_default_handlers()
    
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込む"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {
            "hooks": {
                "PostToolUse": [],
                "PreToolUse": [],
                "Notification": [],
                "Stop": []
            },
            "patterns": {
                "todo_completion": r'"status":\s*"completed"',
                "serena_completion": r'mcp__serena__think_about_whether_you_are_done',
                "implementation_done": r'実装完了|implementation\s+completed',
                "test_success": r'All\s+tests\s+passed|テスト成功',
                "build_success": r'Build\s+successful|ビルド成功'
            }
        }
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """正規表現パターンをコンパイル"""
        patterns = {}
        for name, pattern in self.config.get('patterns', {}).items():
            try:
                patterns[name] = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            except re.error as e:
                self.logger.error(f"Failed to compile pattern {name}: {e}")
        return patterns
    
    def _register_default_handlers(self):
        """デフォルトハンドラーを登録"""
        # PostToolUse完了検知ハンドラー
        self.register_handler('PostToolUse', self._detect_completion_handler)
        # PreToolUseリソースチェックハンドラー
        self.register_handler('PreToolUse', self._resource_check_handler)
    
    def register_handler(self, hook_type: str, handler: Callable):
        """Hookハンドラーを登録"""
        if hook_type in self.handlers:
            self.handlers[hook_type].append(handler)
            self.logger.info(f"Registered handler for {hook_type}")
    
    def process_hook(self, context: HookContext) -> HookResult:
        """Hookを処理"""
        hook_type = context.hook_type
        results = []
        
        if hook_type not in self.handlers:
            return HookResult(success=False, should_block=False, 
                            message=f"Unknown hook type: {hook_type}", actions=[])
        
        for handler in self.handlers[hook_type]:
            try:
                result = handler(context)
                results.append(result)
                
                # PreToolUseでブロックが必要な場合は即座に返す
                if hook_type == 'PreToolUse' and result.should_block:
                    return result
                    
            except Exception as e:
                self.logger.error(f"Handler error for {hook_type}: {e}")
                results.append(HookResult(success=False, should_block=False,
                                        message=str(e), actions=[]))
        
        # 全ハンドラーの結果を統合
        return self._merge_results(results)
    
    def _merge_results(self, results: List[HookResult]) -> HookResult:
        """複数のHook結果を統合"""
        success = all(r.success for r in results)
        should_block = any(r.should_block for r in results)
        messages = [r.message for r in results if r.message]
        actions = []
        for r in results:
            actions.extend(r.actions)
        
        return HookResult(
            success=success,
            should_block=should_block,
            message='\n'.join(messages) if messages else None,
            actions=actions
        )
    
    def _detect_completion_handler(self, context: HookContext) -> HookResult:
        """完了パターンを検知するハンドラー"""
        if context.hook_type != 'PostToolUse' or not context.tool_output:
            return HookResult(success=True, should_block=False, message=None, actions=[])
        
        signals = self.detect_completion_patterns(context.tool_output, context.session_id)
        
        if signals:
            actions = []
            for signal in signals:
                report = self.generate_completion_report(signal)
                actions.append({
                    'type': 'send_report',
                    'report': report.__dict__
                })
            
            return HookResult(
                success=True,
                should_block=False,
                message=f"Detected {len(signals)} completion signals",
                actions=actions
            )
        
        return HookResult(success=True, should_block=False, message=None, actions=[])
    
    def _resource_check_handler(self, context: HookContext) -> HookResult:
        """リソースをチェックするハンドラー"""
        if context.hook_type != 'PreToolUse':
            return HookResult(success=True, should_block=False, message=None, actions=[])
        
        # リソースチェックロジック（簡易版）
        # 実際の実装では、メモリ、CPU、ディスク使用量などをチェック
        should_block = False
        message = None
        
        # 例: 危険なツールの実行をブロック
        dangerous_tools = ['system_shutdown', 'delete_all_files']
        if context.tool_name in dangerous_tools:
            should_block = True
            message = f"Dangerous tool {context.tool_name} blocked"
        
        return HookResult(
            success=True,
            should_block=should_block,
            message=message,
            actions=[]
        )
    
    def detect_completion_patterns(self, output: str, session_id: str) -> List[CompletionSignal]:
        """出力から完了パターンを検知"""
        signals = []
        
        for pattern_name, pattern in self.patterns.items():
            if pattern.search(output):
                signal = CompletionSignal(
                    type=pattern_name,
                    timestamp=datetime.now(),
                    session_id=session_id,
                    context={'pattern': pattern.pattern},
                    raw_output=output[:500]  # 最初の500文字を保存
                )
                signals.append(signal)
                self.logger.info(f"Detected completion pattern: {pattern_name} for session {session_id}")
        
        return signals
    
    def generate_completion_report(self, signal: CompletionSignal) -> Report:
        """完了信号から報告書を生成"""
        report = Report(
            session_id=signal.session_id,
            completion_type=signal.type,
            timestamp=signal.timestamp,
            summary=self._generate_summary(signal),
            details={
                'signal_type': signal.type,
                'detection_time': signal.timestamp.isoformat(),
                'context': signal.context
            },
            next_actions=self._suggest_next_actions(signal)
        )
        
        self.logger.info(f"Generated completion report for session {signal.session_id}")
        return report
    
    def _generate_summary(self, signal: CompletionSignal) -> str:
        """完了信号からサマリーを生成"""
        summaries = {
            'todo_completion': 'タスクが完了しました',
            'serena_completion': 'Serenaによる完了確認が行われました',
            'implementation_done': '実装が完了しました',
            'test_success': 'テストが成功しました',
            'build_success': 'ビルドが成功しました'
        }
        return summaries.get(signal.type, f'{signal.type}が検知されました')
    
    def _suggest_next_actions(self, signal: CompletionSignal) -> List[str]:
        """次のアクションを提案"""
        suggestions = {
            'todo_completion': ['次のタスクを確認', '進捗を報告'],
            'serena_completion': ['コードレビューを実施', 'テストを実行'],
            'implementation_done': ['テストを作成', 'コードレビューを依頼'],
            'test_success': ['本番環境へのデプロイを検討', 'ドキュメントを更新'],
            'build_success': ['デプロイを実行', 'リリースノートを作成']
        }
        return suggestions.get(signal.type, ['次のステップを検討'])
    
    def save_config(self):
        """設定をファイルに保存"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        self.logger.info("Hooks configuration saved")