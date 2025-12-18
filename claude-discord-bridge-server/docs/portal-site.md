# ポータルサイト仕様書

## 概要
gpd-ubuntu (staging) サーバーで稼働するサービス群の管理・監視を行うポータルサイト。

## インフラ構成

### サーバー情報
- **ホスト**: gpd-ubuntu (Tailscale: 100.93.241.39)
- **接続方法**: SSH (`$STAGING_ID@$STAGING_IP`)
- **認証情報**: `/home/rema/project/002--claude-test/.env` に記載

### ストレージ構成
| デバイス | UUID | マウント先 | 用途 |
|---------|------|-----------|------|
| sdb1 | 6624-BD05 | /media/rema/CIRAGO | バックアップ先 |
| sdc1 | CAF2-5176 | /media/rema/CIRAGO2 | メインデータ (SMB共有) |

※ 両方exFATフォーマット、fstabで自動マウント設定済み

### SMB共有
- **共有名**: share
- **パス**: /media/rema/CIRAGO2/share
- **設定**: /etc/samba/smb.conf
- **フォルダ構成**:
  - `project/` - プロジェクト関連
  - `job/` - 仕事関連
  - `private/` - プライベート

## バックアップシステム

### 実行スケジュール
- **時刻**: 毎日 0:00 (cron)
- **スクリプト**: `/usr/local/bin/daily-backup.sh`

### バックアップ対象
| 項目 | ソース | バックアップ先 |
|------|--------|---------------|
| 共有フォルダ | /media/rema/CIRAGO2/share | /media/rema/CIRAGO/share |
| Gitea | /var/lib/gitea | /media/rema/CIRAGO/gitea-backup |
| PostgreSQL | giteadb (pg_dump) | /media/rema/CIRAGO/postgresql-backup/giteadb_YYYYMMDD.sql |

※ PostgreSQLダンプは7日以上前のファイルを自動削除

### ログ出力
- **ログファイル**: `/media/rema/CIRAGO2/backup-log/YYYYMMDD_backup.log`
- **ステータスファイル**: `/media/rema/CIRAGO2/backup-status.json`

### ステータスファイル形式
```json
{
  "last_run": "2025-12-18T09:39:11+09:00",
  "status": "OK",
  "results": {
    "share": "OK",
    "gitea": "OK",
    "postgresql": "OK"
  },
  "errors": []
}
```

### エラー検知条件
1. **rsync失敗**: 終了コード != 0
2. **pg_dump失敗**: 終了コード != 0
3. **HDD未マウント**: マウントポイント存在チェック
4. **サーバー停止**: `last_run` が24時間以上前

## ポータルサイト実装予定

### バックアップ監視機能
1. SMB経由で `backup-status.json` を読み込み
2. 以下の条件でアラート表示:
   - `status` が "ERROR"
   - `last_run` が24時間以上前
3. 各項目(share/gitea/postgresql)の個別ステータス表示

### APIエンドポイント案
```
GET /api/backup/status
```
レスポンス: backup-status.json の内容 + 24h超過チェック結果

## 稼働サービス一覧

### Gitea
- **用途**: Git リポジトリホスティング
- **データ**: /var/lib/gitea
- **DB**: PostgreSQL (giteadb)

### PostgreSQL
- **バージョン**: 16
- **データベース**: giteadb (Gitea用)
- **データ**: /var/lib/postgresql/16

## 関連ファイル

| ファイル | 場所 | 説明 |
|---------|------|------|
| .env | /home/rema/project/002--claude-test/.env | 接続情報 |
| smb.conf | /etc/samba/smb.conf | SMB設定 |
| daily-backup.sh | /usr/local/bin/daily-backup.sh | バックアップスクリプト |
| fstab | /etc/fstab | HDD自動マウント設定 |
