#!/usr/bin/env python3
"""
Attachment Migration Script - 既存attachmentsのsession_1/移行

このスクリプトは以下の機能を提供する：
1. 既存attachmentsディレクトリのバックアップ作成
2. IMG_*ファイルのsession_1/への安全な移行
3. 移行失敗時の自動ロールバック
4. 移行プロセスの詳細ログ記録
"""

import os
import sys
import shutil
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# パッケージルートの追加
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir.parent))

from config.settings import SettingsManager

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AttachmentMigration:
    """
    添付ファイル移行管理クラス
    
    機能：
    - バックアップ作成・管理
    - 段階的ファイル移行
    - エラー時自動ロールバック
    - 移行進捗追跡
    """
    
    def __init__(self):
        """移行管理の初期化"""
        self.settings = SettingsManager()
        self.base_dir = Path.cwd()
        self.attachments_dir = self.base_dir / 'attachments'
        self.session1_dir = self.attachments_dir / 'session_1'
        self.backup_dir = self.base_dir / 'migration' / 'backup'
        
        # 移行状態管理
        self.migration_log = []
        self.migrated_files = []
        self.failed_files = []
        
    def create_backup(self) -> bool:
        """
        既存attachmentsのバックアップ作成
        
        Returns:
            bool: バックアップ成功フラグ
        """
        try:
            if not self.attachments_dir.exists():
                logger.info("No attachments directory found - nothing to migrate")
                return True
            
            # バックアップディレクトリ作成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"attachments_backup_{timestamp}"
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # 既存ファイルリスト取得
            existing_files = list(self.attachments_dir.glob("IMG_*"))
            
            if not existing_files:
                logger.info("No IMG_* files found to migrate")
                return True
            
            logger.info(f"Creating backup of {len(existing_files)} files...")
            
            # ファイル別バックアップ
            backup_successful = 0
            for file_path in existing_files:
                try:
                    backup_file = backup_path / file_path.name
                    shutil.copy2(file_path, backup_file)
                    backup_successful += 1
                    
                    self.migration_log.append({
                        'action': 'backup',
                        'source': str(file_path),
                        'target': str(backup_file),
                        'timestamp': datetime.now().isoformat(),
                        'status': 'success'
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to backup {file_path.name}: {e}")
                    self.migration_log.append({
                        'action': 'backup',
                        'source': str(file_path),
                        'target': str(backup_path / file_path.name),
                        'timestamp': datetime.now().isoformat(),
                        'status': 'failed',
                        'error': str(e)
                    })
                    return False
            
            logger.info(f"✅ Backup completed: {backup_successful} files -> {backup_path}")
            self.backup_path = backup_path
            return True
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return False
    
    def migrate_files(self) -> bool:
        """
        ファイル移行実行
        
        Returns:
            bool: 移行成功フラグ
        """
        try:
            if not self.attachments_dir.exists():
                logger.info("No source directory found")
                return True
            
            # session_1ディレクトリ確保
            self.session1_dir.mkdir(parents=True, exist_ok=True)
            os.chmod(self.session1_dir, 0o700)
            
            # 移行対象ファイル取得
            source_files = list(self.attachments_dir.glob("IMG_*"))
            
            if not source_files:
                logger.info("No files to migrate")
                return True
            
            logger.info(f"Starting migration of {len(source_files)} files...")
            
            # ファイル別移行処理
            for file_path in source_files:
                if self._migrate_single_file(file_path):
                    self.migrated_files.append(file_path)
                else:
                    self.failed_files.append(file_path)
                    # 失敗時は即座にロールバック
                    self._rollback_migration()
                    return False
            
            logger.info(f"✅ Migration completed: {len(self.migrated_files)} files moved to session_1/")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self._rollback_migration()
            return False
    
    def _migrate_single_file(self, source_file: Path) -> bool:
        """
        単一ファイルの移行
        
        Args:
            source_file: 移行元ファイルパス
            
        Returns:
            bool: 移行成功フラグ
        """
        try:
            target_file = self.session1_dir / source_file.name
            
            # 既存ファイルチェック
            if target_file.exists():
                logger.warning(f"Target file exists: {target_file.name}")
                # タイムスタンプ付きでリネーム
                timestamp = datetime.now().strftime("_%Y%m%d_%H%M%S")
                stem = target_file.stem
                suffix = target_file.suffix
                target_file = self.session1_dir / f"{stem}{timestamp}{suffix}"
            
            # ファイル移動
            shutil.move(str(source_file), str(target_file))
            
            # 権限設定
            os.chmod(target_file, 0o644)
            
            logger.debug(f"Migrated: {source_file.name} -> {target_file}")
            
            self.migration_log.append({
                'action': 'migrate',
                'source': str(source_file),
                'target': str(target_file),
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate {source_file.name}: {e}")
            
            self.migration_log.append({
                'action': 'migrate',
                'source': str(source_file),
                'target': str(target_file) if 'target_file' in locals() else 'unknown',
                'timestamp': datetime.now().isoformat(),
                'status': 'failed',
                'error': str(e)
            })
            
            return False
    
    def _rollback_migration(self) -> bool:
        """
        移行のロールバック実行
        
        Returns:
            bool: ロールバック成功フラグ
        """
        try:
            logger.warning("Starting migration rollback...")
            
            if not hasattr(self, 'backup_path') or not self.backup_path.exists():
                logger.error("No backup found for rollback")
                return False
            
            # 移行済みファイルを削除
            for file_path in self.migrated_files:
                try:
                    session1_file = self.session1_dir / file_path.name
                    if session1_file.exists():
                        session1_file.unlink()
                        logger.debug(f"Removed: {session1_file}")
                except Exception as e:
                    logger.error(f"Failed to remove {session1_file}: {e}")
            
            # バックアップからリストア
            backup_files = list(self.backup_path.glob("IMG_*"))
            restored_count = 0
            
            for backup_file in backup_files:
                try:
                    original_file = self.attachments_dir / backup_file.name
                    shutil.copy2(backup_file, original_file)
                    restored_count += 1
                except Exception as e:
                    logger.error(f"Failed to restore {backup_file.name}: {e}")
            
            logger.info(f"✅ Rollback completed: {restored_count} files restored")
            return restored_count == len(backup_files)
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def save_migration_log(self) -> bool:
        """
        移行ログの保存
        
        Returns:
            bool: 保存成功フラグ
        """
        try:
            log_file = self.base_dir / 'migration' / 'migration_log.json'
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            log_data = {
                'migration_date': datetime.now().isoformat(),
                'total_files_processed': len(self.migration_log),
                'successful_migrations': len(self.migrated_files),
                'failed_migrations': len(self.failed_files),
                'migration_details': self.migration_log
            }
            
            with open(log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            logger.info(f"Migration log saved: {log_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save migration log: {e}")
            return False
    
    def verify_migration(self) -> Tuple[bool, Dict]:
        """
        移行結果の検証
        
        Returns:
            Tuple[bool, Dict]: (検証成功フラグ, 検証結果詳細)
        """
        try:
            # session_1ディレクトリ確認
            if not self.session1_dir.exists():
                return False, {'error': 'session_1 directory not found'}
            
            # 移行されたファイル確認
            session1_files = list(self.session1_dir.glob("IMG_*"))
            original_dir_files = list(self.attachments_dir.glob("IMG_*"))
            
            # バックアップとの比較
            if hasattr(self, 'backup_path') and self.backup_path.exists():
                backup_files = list(self.backup_path.glob("IMG_*"))
                expected_count = len(backup_files)
            else:
                expected_count = len(self.migrated_files)
            
            verification = {
                'session1_files_count': len(session1_files),
                'original_files_remaining': len(original_dir_files),
                'expected_files_count': expected_count,
                'migration_successful': len(session1_files) == expected_count and len(original_dir_files) == 0,
                'session1_files': [f.name for f in session1_files],
                'directory_permissions': oct(os.stat(self.session1_dir).st_mode)[-3:]
            }
            
            if verification['migration_successful']:
                logger.info("✅ Migration verification: SUCCESS")
            else:
                logger.error("❌ Migration verification: FAILED")
            
            return verification['migration_successful'], verification
            
        except Exception as e:
            logger.error(f"Migration verification failed: {e}")
            return False, {'error': str(e)}

def run_migration():
    """メイン移行処理実行"""
    logger.info("=== Attachment Migration Starting ===")
    
    migration = AttachmentMigration()
    
    try:
        # Step 1: バックアップ作成
        if not migration.create_backup():
            logger.error("❌ Migration aborted: Backup creation failed")
            return False
        
        # Step 2: ファイル移行
        if not migration.migrate_files():
            logger.error("❌ Migration failed: File migration error")
            return False
        
        # Step 3: 移行検証
        success, verification = migration.verify_migration()
        if not success:
            logger.error(f"❌ Migration verification failed: {verification}")
            return False
        
        # Step 4: ログ保存
        migration.save_migration_log()
        
        logger.info("✅ Migration completed successfully!")
        logger.info(f"   Files migrated: {verification['session1_files_count']}")
        logger.info(f"   Target directory: {migration.session1_dir}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)