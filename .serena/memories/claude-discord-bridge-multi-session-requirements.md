# Claude-Discord-Bridge マルチセッション対応要件

## 背景
yamkz/claude-discord-bridge導入後、複数Discordチャンネルでの並行開発を実現するため、attachments管理の競合問題解決が必要。

## 現在の問題
### ファイル管理競合
- 全セッションが単一`attachments/`ディレクトリを共有
- ファイル名競合：同時刻投稿で`IMG_YYYYMMDD_HHMMSS_random`が重複リスク
- ファイル識別不可：どのセッション/チャンネルの画像か判別困難
- クリーンアップ競合：他セッションの使用中ファイル誤削除リスク

## 採用要件：A案 - セッション別ディレクトリ分割

### ディレクトリ構造
```
attachments/
├── session_1/    # セッション1専用
├── session_2/    # セッション2専用
└── session_N/    # セッションN専用
```

### 技術要件
- `FileNamingStrategy`修正：セッション番号をパス生成に組み込み
- `StorageManager`修正：セッション別ディレクトリ管理
- `AttachmentManager`修正：セッション識別機能追加
- クリーンアップ機能：セッション別個別実行

### 実装ファイル
- `src/attachment_manager.py` - コア機能修正
- `config/settings.py` - セッション設定管理
- 既存API互換性維持

### 優先度
- **高** - マルチセッション本格運用前に実装必須
- 現在の単一セッション動作には影響しない設計とする

## 決定日時
2025-08-27 - ユーザー要件として確定