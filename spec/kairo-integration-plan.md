# Kairo統合開発プラン（保留中）

## A案：Kairoを通常モード内のサブプロセスとして統合

### 運用フロー
```
REQUIREMENTS モード
├── spec/requirements.md作成
└── 機能ごとにKairo実行
    ├── /kairo-requirements
    ├── /kairo-design  
    ├── /kairo-tasks
    └── /kairo-implement

DESIGN モード
├── spec/01-09設計書作成
└── Kairo成果物を統合

IMPLEMENTATION モード
└── Kairo成果物に基づいて実装
```

### メリット
- 一貫した品質管理
- 全体設計との整合性保持
- 統合時の手戻り防止

### デメリット
- 小さな機能でも重いプロセス
- 開発速度の低下
- Tsumiki本来の「小さく素早く」の価値を損なう

## 検討状況
- **現在**: Tsumiki稼働確認のため保留
- **次ステップ**: Tsumiki稼働確認後に本格検討
- **暫定運用**: C案（実験開発=Kairo、本格開発=通常モード）で実施

## 判断タイミング
- [ ] Tsumiki稼働確認完了
- [ ] Kairo開発の実際の効果測定
- [ ] 通常開発モードとの比較検討