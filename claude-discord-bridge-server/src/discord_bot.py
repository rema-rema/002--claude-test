#!/usr/bin/env python3
"""
Discord Bot実装 - Claude-Discord Bridgeのコア機能

このモジュールは以下の責任を持つ：
1. Discordメッセージの受信・処理
2. 画像添付ファイルの管理
3. Claude Codeへのメッセージ転送
4. ユーザーフィードバックの管理
5. 定期的なメンテナンス処理

拡張性のポイント：
- メッセージフォーマット戦略の追加
- 新しい添付ファイル形式のサポート
- カスタムコマンドの追加
- 通知方法の拡張
- セッション管理の強化
"""

import os
import sys
import json
import asyncio
import logging
import requests
from pathlib import Path
from typing import Optional, List, Dict, Any

# パッケージルートの追加（相対インポート対応）
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import discord
    from discord.ext import commands, tasks
except ImportError:
    print("Error: discord.py is not installed. Run: pip install discord.py")
    sys.exit(1)

from config.settings import SettingsManager
from src.attachment_manager import AttachmentManager
from src.session_manager import SessionManager

# ログ設定（本番環境では外部設定ファイルから読み込み可能）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MessageProcessor:
    """
    メッセージ処理の戦略パターン実装
    
    将来の拡張：
    - 異なるメッセージ形式への対応
    - コンテンツフィルタリング
    - メッセージ変換処理
    """
    
    @staticmethod
    def format_message_with_attachments(content: str, attachment_paths: List[str], session_num: int) -> str:
        """
        メッセージと添付ファイルパスを適切にフォーマット
        
        拡張ポイント：
        - 添付ファイル形式の多様化（動画、音声、ドキュメント等）
        - メッセージテンプレートのカスタマイズ
        - 多言語対応
        
        Args:
            content: 元のメッセージ内容
            attachment_paths: 添付ファイルのパスリスト
            session_num: セッション番号
        
        Returns:
            str: フォーマットされたメッセージ
        """
        # 添付ファイルパス文字列の生成
        attachment_str = ""
        if attachment_paths:
            attachment_parts = [f"[添付画像のファイルパス: {path}]" for path in attachment_paths]
            attachment_str = " " + " ".join(attachment_parts)
        
        # メッセージタイプによる分岐処理
        if content.startswith('/'):
            # スラッシュコマンド形式（直接Claude Codeコマンド実行）
            return f"{content}{attachment_str} session={session_num}"
        else:
            # 通常メッセージ形式（Claude Codeへの通知）
            return f"Discordからの通知: {content}{attachment_str} session={session_num}"

class ClaudeCLIBot(commands.Bot):
    """
    Claude CLI統合Discord Bot
    
    アーキテクチャ特徴：
    - 非同期処理による高いレスポンス性
    - モジュラー設計による拡張性
    - 堅牢なエラーハンドリング
    - 自動リソース管理
    
    拡張可能要素：
    - カスタムコマンドの追加
    - 権限管理システム
    - ユーザーセッション管理
    - 統計・分析機能
    - Webhook統合
    """
    
    # 設定可能な定数（将来は設定ファイル化）
    CLEANUP_INTERVAL_HOURS = 6
    REQUEST_TIMEOUT_SECONDS = 5
    LOADING_MESSAGE = "`...`"
    SUCCESS_MESSAGE = "> メッセージを送信完了しました"
    
    def __init__(self, settings_manager: SettingsManager):
        """
        Botインスタンスの初期化（マルチセッション対応）
        
        Args:
            settings_manager: 設定管理インスタンス
        """
        self.settings = settings_manager
        self.session_manager = SessionManager()
        self.message_processor = MessageProcessor()
        
        # セッション別AttachmentManagerのキャッシュ
        self.attachment_managers = {}  # {session_id: AttachmentManager}
        
        # Discord Bot設定
        intents = discord.Intents.default()
        intents.message_content = True  # メッセージ内容へのアクセス権限
        
        super().__init__(command_prefix='!', intents=intents)
        
    async def on_ready(self):
        """
        Bot準備完了時の初期化処理
        
        拡張ポイント：
        - データベース接続初期化
        - 外部API接続確認
        - 統計情報の初期化
        - 定期処理タスクの開始
        """
        logger.info(f'{self.user} has connected to Discord!')
        print(f'✅ Discord bot is ready as {self.user}')
        
        # 初回システムクリーンアップ
        await self._perform_initial_cleanup()
        
        # 定期メンテナンス処理の開始
        await self._start_maintenance_tasks()
        
    async def _perform_initial_cleanup(self):
        """
        Bot起動時の初回クリーンアップ処理（マルチセッション対応）
        
        拡張ポイント：
        - 古いセッションデータの削除
        - ログファイルのローテーション
        - キャッシュの初期化
        """
        # 全セッションのクリーンアップ実行
        total_cleanup_count = 0
        
        # 現在設定されている全セッション取得
        sessions = self.settings.list_sessions()
        session_ids = [session_num for session_num, _ in sessions]
        
        # デフォルトセッション追加（存在しない場合）
        default_session = self.session_manager.get_default_session()
        if default_session not in session_ids:
            session_ids.append(default_session)
        
        # 各セッションでクリーンアップ実行
        for session_id in session_ids:
            attachment_manager = self._get_attachment_manager(session_id)
            cleanup_count = attachment_manager.cleanup_old_files()
            total_cleanup_count += cleanup_count
            
            if cleanup_count > 0:
                logger.info(f'Session {session_id}: Cleaned up {cleanup_count} old files')
        
        if total_cleanup_count > 0:
            print(f'🧹 Cleaned up {total_cleanup_count} old attachment files across all sessions')
            
    async def _start_maintenance_tasks(self):
        """
        定期メンテナンスタスクの開始
        
        拡張ポイント：
        - データベースメンテナンス
        - 統計情報の集計
        - 外部API状態確認
        """
        if not self.cleanup_task.is_running():
            self.cleanup_task.start()
            print(f'⏰ Attachment cleanup task started (runs every {self.CLEANUP_INTERVAL_HOURS} hours)')
        
    async def on_message(self, message):
        """
        メッセージ受信時のメイン処理ハンドラー
        
        処理フロー：
        1. メッセージの事前検証
        2. セッション確認
        3. 即座のユーザーフィードバック
        4. 添付ファイル処理
        5. メッセージフォーマット
        6. Claude Codeへの転送
        7. 結果フィードバック
        
        拡張ポイント：
        - メッセージ前処理フィルター
        - 権限チェック
        - レート制限
        - ログ記録
        - 統計収集
        """
        # 基本的な検証
        if not await self._validate_message(message):
            return
        
        # セッション確認（SessionManagerを使用）
        session_id = self.session_manager.get_session_by_channel(str(message.channel.id))
        if session_id is None:
            # デフォルトセッション使用
            session_id = self.session_manager.get_default_session()
            logger.debug(f"Using default session {session_id} for channel {message.channel.id}")
        
        # ユーザーフィードバック（即座のローディング表示）
        loading_msg = await self._send_loading_feedback(message.channel)
        if not loading_msg:
            return
        
        try:
            # メッセージ処理パイプライン
            result_text = await self._process_message_pipeline(message, session_id)
            
        except Exception as e:
            result_text = f"❌ 処理エラー: {str(e)[:100]}"
            logger.error(f"Message processing error: {e}", exc_info=True)
        
        # 最終結果の表示
        await self._update_feedback(loading_msg, result_text)
        
    def _get_attachment_manager(self, session_id: int) -> AttachmentManager:
        """
        セッション別AttachmentManager取得（キャッシュ付き）
        
        Args:
            session_id: セッション番号
            
        Returns:
            AttachmentManager: セッション専用のAttachmentManagerインスタンス
        """
        if session_id not in self.attachment_managers:
            self.attachment_managers[session_id] = AttachmentManager(session_id=session_id)
            logger.debug(f"Created AttachmentManager for session {session_id}")
        
        return self.attachment_managers[session_id]
        
    async def _validate_message(self, message) -> bool:
        """
        メッセージの基本検証
        
        拡張ポイント：
        - スパム検出
        - 権限確認
        - ブラックリストチェック
        """
        # Bot自身のメッセージは無視
        # 🎤プレフィックスもFlask直接転送に変更したため、discord-bridge経由は不要
        if message.author == self.user:
            if message.content.startswith('🎤'):
                logger.info(f'音声入力メッセージ（ログのみ、処理スキップ）: {message.content[:50]}...')
            return False
        
        # Discord標準コマンドの処理
        await self.process_commands(message)
        
        return True
        
    async def _send_loading_feedback(self, channel) -> Optional[discord.Message]:
        """
        ローディングフィードバックの送信
        
        拡張ポイント：
        - カスタムローディングメッセージ
        - アニメーション表示
        - プログレスバー
        """
        try:
            return await channel.send(self.LOADING_MESSAGE)
        except Exception as e:
            logger.error(f'フィードバック送信エラー: {e}')
            return None
            
    async def _process_message_pipeline(self, message, session_id: int) -> str:
        """
        メッセージ処理パイプライン（マルチセッション対応）
        
        拡張ポイント：
        - 処理ステップの追加
        - 非同期処理の並列化
        - キャッシュ機能
        """
        # ステップ1: セッション別AttachmentManager取得
        attachment_manager = self._get_attachment_manager(session_id)
        
        # ステップ2: 添付ファイル処理
        attachment_paths = await self._process_attachments(message, session_id, attachment_manager)
        
        # ステップ3: メッセージフォーマット
        formatted_message = self.message_processor.format_message_with_attachments(
            message.content, attachment_paths, session_id
        )
        
        # ステップ4: Claude Codeへの転送
        return await self._forward_to_claude(formatted_message, message, session_id)
        
    async def _process_attachments(self, message, session_id: int, attachment_manager: AttachmentManager) -> List[str]:
        """
        添付ファイル処理（マルチセッション対応）
        
        拡張ポイント：
        - 新しいファイル形式のサポート
        - ファイル変換処理
        - ウイルススキャン
        
        Args:
            message: Discordメッセージオブジェクト
            session_id: セッション番号
            attachment_manager: セッション専用AttachmentManager
            
        Returns:
            List[str]: 処理済み添付ファイルパスのリスト
        """
        attachment_paths = []
        if message.attachments:
            try:
                attachment_paths = await attachment_manager.process_attachments(message.attachments)
                if attachment_paths:
                    logger.info(f"Processed {len(attachment_paths)} attachment(s) for session_{session_id}")
            except Exception as e:
                logger.error(f"Attachment processing error for session {session_id}: {e}")
        
        return attachment_paths
        
    async def _forward_to_claude(self, formatted_message: str, original_message, session_id: int) -> str:
        """
        Claude Codeへのメッセージ転送（マルチセッション対応）
        
        拡張ポイント：
        - 複数転送先のサポート
        - 転送失敗時のリトライ
        - 負荷分散
        - セッション別ルーティング
        
        Args:
            formatted_message: フォーマット済みメッセージ
            original_message: 元のDiscordメッセージ
            session_id: セッション番号
            
        Returns:
            str: 転送結果メッセージ
        """
        try:
            payload = {
                'message': formatted_message,
                'channel_id': str(original_message.channel.id),
                'session': session_id,
                'user_id': str(original_message.author.id),
                'username': str(original_message.author)
            }
            
            flask_port = self.settings.get_port('flask')
            response = requests.post(
                f'http://localhost:{flask_port}/discord-message',
                json=payload,
                timeout=self.REQUEST_TIMEOUT_SECONDS
            )
            
            logger.debug(f"Forwarded message to Claude session {session_id} with status {response.status_code}")
            return self._format_response_status(response.status_code)
            
        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to Flask app. Is it running?")
            return "❌ エラー: Flask appに接続できません"
        except Exception as e:
            logger.error(f"Error forwarding message to session {session_id}: {e}")
            return f"❌ エラー: {str(e)[:100]}"
            
    def _format_response_status(self, status_code: int) -> str:
        """
        レスポンスステータスのフォーマット
        
        拡張ポイント：
        - 詳細ステータスメッセージ
        - 多言語対応
        - カスタムメッセージ
        """
        if status_code == 200:
            return self.SUCCESS_MESSAGE
        else:
            return f"⚠️ ステータス: {status_code}"
            
    async def _update_feedback(self, loading_msg: discord.Message, result_text: str):
        """
        フィードバックメッセージの更新
        
        拡張ポイント：
        - リッチメッセージ表示
        - 進捗状況の表示
        - インタラクティブ要素
        """
        try:
            await loading_msg.edit(content=result_text)
        except Exception as e:
            logger.error(f'メッセージ更新失敗: {e}')
    
    @tasks.loop(hours=CLEANUP_INTERVAL_HOURS)
    async def cleanup_task(self):
        """
        定期クリーンアップタスク（マルチセッション対応）
        
        拡張ポイント：
        - データベースクリーンアップ
        - ログファイル管理
        - 統計情報の集計
        - システムヘルスチェック
        """
        try:
            total_cleanup_count = 0
            
            # 現在設定されている全セッション取得
            sessions = self.settings.list_sessions()
            session_ids = [session_num for session_num, _ in sessions]
            
            # デフォルトセッション追加（存在しない場合）
            default_session = self.session_manager.get_default_session()
            if default_session not in session_ids:
                session_ids.append(default_session)
            
            # 各セッションでクリーンアップ実行
            for session_id in session_ids:
                try:
                    attachment_manager = self._get_attachment_manager(session_id)
                    cleanup_count = attachment_manager.cleanup_old_files()
                    total_cleanup_count += cleanup_count
                    
                    if cleanup_count > 0:
                        logger.info(f'Session {session_id} automatic cleanup: {cleanup_count} files deleted')
                        
                except Exception as e:
                    logger.error(f'Error in cleanup task for session {session_id}: {e}')
                    continue
            
            if total_cleanup_count > 0:
                logger.info(f'Total automatic cleanup: {total_cleanup_count} files deleted across all sessions')
                
        except Exception as e:
            logger.error(f'Error in cleanup task: {e}')
    
    @cleanup_task.before_loop
    async def before_cleanup_task(self):
        """クリーンアップタスク開始前の準備処理"""
        await self.wait_until_ready()

def create_bot_commands(bot: ClaudeCLIBot, settings: SettingsManager):
    """
    Botコマンドの登録（マルチセッション対応）
    
    拡張ポイント：
    - 新しいコマンドの追加
    - 権限ベースのコマンド
    - 動的コマンド登録
    """
    
    @bot.command(name='status')
    async def status_command(ctx):
        """Bot状態確認コマンド（マルチセッション対応）"""
        sessions = settings.list_sessions()
        embed = discord.Embed(
            title="Claude CLI Bot Status - Multi-Session",
            description="✅ Bot is running",
            color=discord.Color.green()
        )
        
        session_list = "\n".join([f"Session {num}: <#{ch_id}>" for num, ch_id in sessions])
        embed.add_field(name="Active Sessions", value=session_list or "No sessions configured", inline=False)
        
        # セッション別添付ファイル統計
        if sessions:
            attachment_stats = []
            for session_num, _ in sessions:
                attachment_manager = bot._get_attachment_manager(session_num)
                info = attachment_manager.get_session_attachments_info()
                attachment_stats.append(f"Session {session_num}: {info['total_files']} files ({info['total_size_mb']}MB)")
            
            embed.add_field(name="Attachment Storage", value="\n".join(attachment_stats), inline=False)
        
        await ctx.send(embed=embed)
    
    @bot.command(name='sessions')
    async def sessions_command(ctx):
        """設定済みセッション一覧表示コマンド"""
        sessions = settings.list_sessions()
        if not sessions:
            await ctx.send("No sessions configured.")
            return
        
        embed = discord.Embed(
            title="Configured Sessions",
            color=discord.Color.blue()
        )
        
        # セッション詳細情報
        for session_num, channel_id in sessions:
            attachment_manager = bot._get_attachment_manager(session_num)
            info = attachment_manager.get_session_attachments_info()
            
            embed.add_field(
                name=f"Session {session_num}",
                value=f"Channel: <#{channel_id}>\nFiles: {info['total_files']} ({info['total_size_mb']}MB)\nStatus: {info['storage_status']}",
                inline=True
            )
        
        await ctx.send(embed=embed)
    
    @bot.command(name='session-info')
    async def session_info_command(ctx, session_id: int = None):
        """セッション詳細情報表示コマンド"""
        if session_id is None:
            # 現在のチャンネルのセッション情報取得
            session_id = bot.session_manager.get_session_by_channel(str(ctx.channel.id))
            if session_id is None:
                session_id = bot.session_manager.get_default_session()
        
        # セッション存在確認
        sessions = settings.list_sessions()
        session_exists = any(num == session_id for num, _ in sessions)
        
        if not session_exists and session_id != bot.session_manager.get_default_session():
            await ctx.send(f"❌ Session {session_id} not found.")
            return
        
        # 添付ファイル情報取得
        attachment_manager = bot._get_attachment_manager(session_id)
        info = attachment_manager.get_session_attachments_info()
        
        embed = discord.Embed(
            title=f"Session {session_id} Details",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Session ID", value=str(session_id), inline=True)
        embed.add_field(name="Storage Directory", value=info['directory'], inline=False)
        embed.add_field(name="Total Files", value=str(info['total_files']), inline=True)
        embed.add_field(name="Total Size", value=f"{info['total_size_mb']}MB", inline=True)
        embed.add_field(name="Status", value=info['storage_status'], inline=True)
        
        if info.get('last_updated'):
            embed.add_field(name="Last Updated", value=info['last_updated'], inline=False)
        
        await ctx.send(embed=embed)
    
    @bot.command(name='cleanup')
    async def cleanup_command(ctx, session_id: int = None):
        """手動クリーンアップコマンド"""
        if session_id is None:
            # 全セッションクリーンアップ
            sessions = settings.list_sessions()
            session_ids = [session_num for session_num, _ in sessions]
            
            # デフォルトセッション追加
            default_session = bot.session_manager.get_default_session()
            if default_session not in session_ids:
                session_ids.append(default_session)
            
            total_cleanup_count = 0
            for sid in session_ids:
                attachment_manager = bot._get_attachment_manager(sid)
                cleanup_count = attachment_manager.cleanup_old_files()
                total_cleanup_count += cleanup_count
            
            await ctx.send(f"🧹 Manual cleanup completed: {total_cleanup_count} files deleted across all sessions")
            
        else:
            # 特定セッションクリーンアップ
            attachment_manager = bot._get_attachment_manager(session_id)
            cleanup_count = attachment_manager.cleanup_old_files()
            await ctx.send(f"🧹 Session {session_id} cleanup completed: {cleanup_count} files deleted")

def run_bot():
    """
    Discord Botのメイン実行関数
    
    拡張ポイント：
    - 複数Bot管理
    - シャーディング対応
    - 高可用性設定
    """
    settings = SettingsManager()
    
    # トークン確認
    token = settings.get_token()
    if not token or token == 'your_token_here':
        print("❌ Discord bot token not configured!")
        print("Run './install.sh' to set up the token.")
        sys.exit(1)
    
    # Botインスタンス作成
    bot = ClaudeCLIBot(settings)
    
    # コマンド登録
    create_bot_commands(bot, settings)
    
    # Bot実行
    try:
        bot.run(token)
    except discord.LoginFailure:
        print("❌ Failed to login. Check your Discord bot token.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running bot: {e}")
        logger.error(f"Bot execution error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    run_bot()