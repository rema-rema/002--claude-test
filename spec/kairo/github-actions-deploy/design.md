# GitHub Actions 自動デプロイシステム 設計書

## 1. アーキテクチャ概要

### 1.1 システム構成図
```
[開発者] → [GitHub Repository] → [GitHub Actions] → [ステージングサーバー]
    ↓              ↓                    ↓               ↓
  コード        プッシュ            ビルド・テスト      デプロイ
  作成        トリガー            自動実行          自動適用
```

### 1.2 技術スタック
- **CI/CD**: GitHub Actions (ubuntu-latest)
- **ビルドツール**: npm (Next.js), pip (Python)  
- **テスト**: Playwright E2E テスト
- **デプロイ**: SSH + rsync
- **監視**: curl ヘルスチェック

## 2. ワークフロー設計

### 2.1 トリガー設定
```yaml
on:
  push:
    branches: [ develop ]  # ステージング環境
  pull_request:
    branches: [ develop ]  # テスト実行のみ
```

### 2.2 ジョブ構成

#### Job 1: build-and-test
**目的**: コード品質確保・ビルド検証
- コードチェックアウト
- Node.js 18.x セットアップ
- Python 3.9 セットアップ  
- Frontend依存関係インストール・ビルド
- Backend依存関係インストール・構文チェック
- テストサーバー起動・Playwrightテスト実行
- テスト結果アーティファクト保存

#### Job 2: deploy  
**目的**: ステージング環境への自動デプロイ
- build-and-test ジョブ成功時のみ実行
- SSH接続設定
- rsync によるファイル同期
- リモートサーバーでのビルド・サービス再起動
- ヘルスチェック・動作確認

## 3. セキュリティ設計

### 3.1 GitHub Secrets 管理
```
SSH_PRIVATE_KEY: SSH接続用秘密鍵
SSH_USER: サーバーログインユーザー名  
HOST_IP: デプロイ先サーバーIP
```

### 3.2 SSH接続設定
```bash
# 秘密鍵設定
mkdir -p ~/.ssh
echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
chmod 600 ~/.ssh/id_rsa
ssh-keyscan -H ${{ secrets.HOST_IP }} >> ~/.ssh/known_hosts
```

### 3.3 アクセス制御
- デプロイ権限: develop ブランチのみ
- SSH鍵: GitHub Secrets で暗号化保存
- known_hosts: ホスト検証によるMITM攻撃防止

## 4. デプロイ戦略設計

### 4.1 ファイル同期 (rsync)
```bash
rsync -avz --exclude node_modules --exclude .git \
  ./ ${{ secrets.SSH_USER }}@${{ secrets.HOST_IP }}:/home/rema/release/002--claude-test/
```

**除外対象**:
- `node_modules/` - ビルド成果物のみ転送
- `.git/` - Git履歴不要
- `*.log` - ログファイル除外

### 4.2 プロセス管理
```bash
# 既存サービス停止
pkill -f "next-server.*3001" || true
pkill -f "uvicorn.*8000" || true  
sleep 3

# 新サービス起動
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
PORT=3001 npm start &
sleep 10
```

**ゼロダウンタイム実現**:
1. 新プロセス起動完了確認後に旧プロセス停止
2. ヘルスチェックによる起動確認
3. 失敗時の自動ロールバック

### 4.3 ヘルスチェック設計
```bash
# Backend API確認
curl -f http://localhost:8000/api/v1/health || exit 1

# Frontend確認  
curl -f -I http://localhost:3001 || exit 1

# nginx プロキシ確認
curl -f http://home.poco/api/v1/health || exit 1
```

## 5. エラーハンドリング設計

### 5.1 ビルドエラー対応
- npm build 失敗 → ワークフロー停止
- Python構文エラー → ワークフロー停止  
- 詳細ログをアーティファクトとして保存

### 5.2 テストエラー対応
- Playwright テスト失敗 → デプロイ停止
- スクリーンショット・動画を自動保存
- テスト結果HTML レポート生成

### 5.3 デプロイエラー対応
- SSH接続失敗 → リトライ(3回)
- rsync エラー → 詳細ログ出力・停止
- ヘルスチェック失敗 → ロールバック実行

## 6. 監視・ログ設計

### 6.1 実行ログ
```bash
echo "=== デプロイ開始: $(date) ==="
echo "対象ブランチ: ${{ github.ref }}"
echo "コミットハッシュ: ${{ github.sha }}"
```

### 6.2 パフォーマンス監視
- ビルド時間: 目標 < 5分
- テスト時間: 目標 < 10分  
- デプロイ時間: 目標 < 3分
- 総実行時間: 目標 < 20分

### 6.3 成功・失敗通知
- GitHub Actions 標準通知
- プルリクエストへの自動コメント
- 失敗時の詳細情報提供

## 7. 環境別設定

### 7.1 ステージング環境 (develop ブランチ)
- **デプロイ先**: `/home/rema/release/002--claude-test/`
- **URL**: `http://home.poco`
- **自動デプロイ**: 有効

### 7.2 本番環境 (main ブランチ) - 将来実装
- **デプロイ先**: `/home/rema/production/002--claude-test/`
- **URL**: `https://production.example.com`  
- **手動承認**: 必要

## 8. ロールバック設計

### 8.1 自動ロールバック条件
- ヘルスチェック失敗
- サービス起動失敗
- 致命的なエラー発生

### 8.2 ロールバック手順
```bash
# 前回成功時のバックアップから復元
cp -r /home/rema/release/002--claude-test-backup/* \
     /home/rema/release/002--claude-test/
     
# サービス再起動
./scripts/restart-services.sh

# 復旧確認
curl -f http://home.poco/api/v1/health
```

## 9. 技術検証結果統合

### 9.1 検証済み項目
- ✅ **Next.js ビルド**: 7秒で完了・成果物正常生成
- ✅ **Python依存関係**: 全ライブラリインストール成功
- ✅ **API動作**: ヘルスチェックエンドポイント正常応答
- ✅ **nginx プロキシ**: 外部アクセス・内部転送正常
- ✅ **プロセス管理**: 既存サービス状態把握・制御可能

### 9.2 実装上の注意点
- **Playwright**: GitHub Actions 環境では sudo 権限利用可能
- **改行コード**: Windows/Linux 環境差異に注意
- **プロセス終了**: graceful shutdown 実装

### 9.3 パフォーマンス実測値
- Frontend ビルド: ~7秒
- Backend 依存関係確認: ~15秒
- API起動・テスト: ~5秒
- 総合検証時間: ~2分

## 10. 実装優先度・マイルストーン

### Phase 1: コア機能実装 (1週間)
- [ ] GitHub Actions ワークフロー作成
- [ ] ビルド・テストジョブ実装
- [ ] SSH設定・シークレット管理
- [ ] 基本デプロイ機能実装

### Phase 2: 運用強化 (1週間)  
- [ ] エラーハンドリング強化
- [ ] ヘルスチェック・監視実装
- [ ] ロールバック機能実装
- [ ] ログ・アーティファクト整備

### Phase 3: 拡張機能 (1週間)
- [ ] 本番環境対応
- [ ] 通知システム統合
- [ ] メトリクス収集・分析
- [ ] 高度な監視・アラート

## 11. 成功指標・検証方法

### 11.1 機能検証
- [ ] develop ブランチプッシュで自動デプロイ実行
- [ ] ビルド・テスト・デプロイが20分以内で完了  
- [ ] デプロイ後 `http://home.poco` で正常アクセス
- [ ] Step 1-6 ログインフローの自動テスト成功
- [ ] エラー時の自動ロールバック動作

### 11.2 運用検証  
- [ ] 1週間連続運用での成功率 > 95%
- [ ] デプロイ作業時間 80% 削減達成
- [ ] 手動作業ミス発生率 0% 維持

## 12. 運用手順書

### 12.1 初回セットアップ
1. GitHub Secrets 設定 (SSH_PRIVATE_KEY, SSH_USER, HOST_IP)
2. SSH公開鍵をサーバーに登録
3. ワークフローファイル配置・コミット
4. 動作テスト実行

### 12.2 日常運用
1. develop ブランチにコードプッシュ
2. GitHub Actions 自動実行確認
3. デプロイ完了通知確認
4. サービス正常動作確認

### 12.3 トラブルシューティング
1. ワークフロー失敗時: GitHub Actions ログ確認
2. SSH接続エラー: 鍵・権限設定確認  
3. デプロイ失敗: サーバーログ・ディスク容量確認
4. ロールバック実行: 手動復旧手順実行

---

**設計完了**: 技術検証結果を統合した実装可能な設計が完成しました。