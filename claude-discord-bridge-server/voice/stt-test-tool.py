#!/usr/bin/env python3
"""
STT自動テストツール - VOICEVOX合成音声でSTT認識精度を検証
"""

import asyncio
import json
import requests
import websockets
import numpy as np
from datetime import datetime

# 設定
VOICEVOX_URL = "http://localhost:50021"
STT_WS_URL = "ws://127.0.0.1:8765"
SPEAKER_ID = 3  # ずんだもん（ノーマル）

# テストパターン（100パターン: 短文30、中文40、長文30）
TEST_PATTERNS = {
    "short": [
        # 挨拶・基本フレーズ (10)
        "今日は天気がいいですね",
        "お疲れ様です",
        "ありがとうございます",
        "了解しました",
        "よろしくお願いします",
        "おはようございます",
        "こんにちは",
        "こんばんは",
        "お世話になっております",
        "失礼します",
        # ビジネス短文 (10)
        "確認しました",
        "承知しました",
        "問題ありません",
        "少々お待ちください",
        "申し訳ございません",
        "かしこまりました",
        "お先に失礼します",
        "いってきます",
        "ただいま戻りました",
        "お待たせしました",
        # 技術用語短文 (10)
        "テストが通りました",
        "ビルドが完了しました",
        "デプロイしました",
        "マージしてください",
        "レビューお願いします",
        "バグを見つけました",
        "修正しました",
        "プッシュしました",
        "プルリクエスト作成しました",
        "コンフリクトがあります",
    ],
    "medium": [
        # 日常会話 (10)
        "今日は天気が良いので午後から散歩に行こうと思っています",
        "週末は友達と映画を見に行く予定です",
        "昨日買った本がとても面白かったです",
        "来月の旅行の計画を立てています",
        "最近運動不足なのでジムに通い始めました",
        "新しいレストランを見つけたので今度行ってみましょう",
        "電車が遅延しているので少し遅れます",
        "今日の夕飯は何にしようか考えています",
        "週末に部屋の掃除をしなければなりません",
        "最近忙しくてあまり眠れていません",
        # ビジネス会話 (15)
        "このプロジェクトの進捗状況を教えていただけますか",
        "明日の会議は午前10時から開始予定です",
        "システムの動作確認が完了しましたので報告します",
        "新しい機能の実装について相談させてください",
        "テスト結果を確認したところ問題は見つかりませんでした",
        "次のステップとして何をすべきか教えてください",
        "データベースの接続設定を変更する必要があります",
        "ドキュメントの更新が完了しましたのでご確認ください",
        "来週のスケジュールについて調整をお願いします",
        "本日中に対応しますのでお待ちください",
        "クライアントからの要望を整理しました",
        "見積もりの作成をお願いできますか",
        "納期について確認させてください",
        "契約書の内容を確認してください",
        "予算内で対応可能かどうか検討します",
        # 技術的な会話 (15)
        "このコードのリファクタリングが必要です",
        "パフォーマンスの改善案を検討しています",
        "セキュリティの脆弱性が見つかりました",
        "ログを確認したところエラーが発生していました",
        "本番環境へのデプロイ準備が整いました",
        "ステージング環境でテストを実施します",
        "APIのレスポンスが遅いので調査します",
        "メモリリークの可能性があります",
        "キャッシュを有効にすると改善するかもしれません",
        "バックアップの確認をお願いします",
        "負荷テストの結果を共有します",
        "インフラの設定を見直す必要があります",
        "監視アラートが発生しました",
        "障害の原因を調査中です",
        "復旧作業が完了しました",
    ],
    "long": [
        # 複合的な説明 (15)
        "今日は天気が良いので午後から公園に散歩に行って、そのあとカフェでコーヒーを飲もうと思っています",
        "このシステムは音声認識と音声合成を組み合わせて、自然な対話を実現することを目的としています",
        "プロジェクトの進捗状況ですが、現在は基本機能の実装が完了し、テストフェーズに入っています",
        "会議の議題として、予算の見直しと来期の計画について話し合いたいと思いますので、資料の準備をお願いします",
        "音声認識の精度を向上させるために、ノイズ除去とVADのパラメータ調整を行う必要があります",
        "この機能は複数のマイクロサービスと連携しており、全体のアーキテクチャを理解する必要があります",
        "ユーザーからのフィードバックを反映して、インターフェースを改善しました",
        "テスト自動化により、品質を担保しながら開発速度を向上させることができます",
        "クラウド環境へのマイグレーションを計画しており、コスト削減と可用性向上を目指しています",
        "機械学習モデルのトレーニングには大量のデータと計算リソースが必要です",
        "セキュリティ監査の結果、いくつかの改善点が指摘されましたので対応します",
        "ドキュメントを最新の状態に保つことで、チームメンバーの理解を助けます",
        "コードレビューを通じて、バグの早期発見と知識共有を促進しています",
        "継続的インテグレーションにより、変更が自動的にテストされます",
        "アジャイル開発手法を採用することで、柔軟に要件変更に対応できます",
        # 技術的な長文 (15)
        "データベースのインデックスを最適化することで、クエリのパフォーマンスが大幅に改善されました",
        "マイクロサービスアーキテクチャでは、各サービスが独立してデプロイできるため、開発効率が向上します",
        "コンテナ技術を活用することで、開発環境と本番環境の差異を最小限に抑えることができます",
        "ロードバランサーを導入することで、トラフィックを複数のサーバーに分散させることができます",
        "リアルタイムでデータを処理するために、ストリーミング処理の仕組みを実装しました",
        "分散システムでは、ネットワークの遅延や障害を考慮した設計が重要になります",
        "暗号化を適切に実装することで、データの機密性と完全性を保護することができます",
        "キューを使用した非同期処理により、システムの応答性を向上させることができます",
        "モニタリングとアラートを設定することで、問題を早期に検知して対応できます",
        "バージョン管理を適切に行うことで、変更履歴の追跡とロールバックが容易になります",
        "テスト駆動開発では、まずテストを書いてから実装を行うことで品質を確保します",
        "リファクタリングは、機能を変えずにコードの構造を改善する作業です",
        "アクセシビリティを考慮した設計により、より多くのユーザーが利用できるようになります",
        "パフォーマンス測定を定期的に実施し、ボトルネックを特定して改善します",
        "災害対策として、複数のリージョンにバックアップを配置しています",
    ],
}


def generate_audio(text: str) -> bytes:
    """VOICEVOXでテキストから音声を生成"""
    # 音声クエリを作成
    query_res = requests.post(
        f"{VOICEVOX_URL}/audio_query",
        params={"text": text, "speaker": SPEAKER_ID}
    )
    query_res.raise_for_status()
    query = query_res.json()

    # 音声合成
    synth_res = requests.post(
        f"{VOICEVOX_URL}/synthesis",
        params={"speaker": SPEAKER_ID},
        json=query
    )
    synth_res.raise_for_status()

    return synth_res.content


def wav_to_pcm16(wav_data: bytes) -> bytes:
    """WAVデータをPCM16に変換（ヘッダー除去）"""
    # WAVヘッダーをスキップ（44バイト）
    return wav_data[44:]


async def test_stt(audio_pcm: bytes, timeout: float = 15.0) -> str:
    """STTサーバーに音声を送信して認識結果を取得（タイムアウト付き）"""
    recognized_text = ""

    async def _test():
        nonlocal recognized_text
        async with websockets.connect(STT_WS_URL) as ws:
            # 音声データを送信（チャンク分割）
            chunk_size = 3200  # 0.1秒分 (16000Hz * 2bytes * 0.1s)
            for i in range(0, len(audio_pcm), chunk_size):
                chunk = audio_pcm[i:i+chunk_size]
                await ws.send(chunk)
                await asyncio.sleep(0.05)  # 送信間隔

            # 発話終了を通知
            await ws.send(json.dumps({"type": "end"}))

            # 結果を待機
            try:
                async for message in ws:
                    data = json.loads(message)
                    if data.get("type") == "final":
                        recognized_text = data.get("text", "")
                        break
                    elif data.get("type") == "partial":
                        recognized_text = data.get("text", "")
                        # 繰り返し検出: 同じパターンが3回以上繰り返されたら終了
                        if len(recognized_text) > 100 and has_repetition(recognized_text):
                            print("    [警告] 繰り返し検出 - 強制終了")
                            await ws.send(json.dumps({"type": "reset"}))
                            break
            except websockets.exceptions.ConnectionClosed:
                pass

    try:
        await asyncio.wait_for(_test(), timeout=timeout)
    except asyncio.TimeoutError:
        print(f"    [警告] タイムアウト ({timeout}秒)")

    return recognized_text


def has_repetition(text: str, min_pattern_len: int = 5, min_repeats: int = 3) -> bool:
    """テキスト内の繰り返しパターンを検出"""
    if len(text) < min_pattern_len * min_repeats:
        return False

    # 末尾からパターンを探す
    for pattern_len in range(min_pattern_len, min(30, len(text) // min_repeats)):
        pattern = text[-pattern_len:]
        count = text.count(pattern)
        if count >= min_repeats:
            return True

    return False


def calculate_accuracy(original: str, recognized: str) -> float:
    """文字単位の認識精度を計算"""
    if not original:
        return 0.0

    # 簡易的な文字一致率
    original_chars = set(original.replace(" ", ""))
    recognized_chars = set(recognized.replace(" ", ""))

    if not original_chars:
        return 0.0

    matching = len(original_chars & recognized_chars)
    return matching / len(original_chars) * 100


async def run_tests():
    """全テストパターンを実行"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "summary": {"total": 0, "passed": 0, "failed": 0},
        "by_category": {},
        "details": []
    }

    print("=" * 60)
    print("STT自動テスト開始")
    print("=" * 60)

    for category, patterns in TEST_PATTERNS.items():
        print(f"\n【{category}】({len(patterns)}パターン)")
        print("-" * 40)

        category_results = {"total": len(patterns), "passed": 0, "avg_accuracy": 0}
        accuracies = []

        for i, text in enumerate(patterns, 1):
            print(f"\n[{i}/{len(patterns)}] テスト: {text[:30]}...")

            try:
                # 音声生成
                wav_data = generate_audio(text)
                pcm_data = wav_to_pcm16(wav_data)

                # STT認識
                recognized = await test_stt(pcm_data)

                # 精度計算
                accuracy = calculate_accuracy(text, recognized)
                accuracies.append(accuracy)

                passed = accuracy >= 70  # 70%以上で合格
                status = "✅" if passed else "❌"

                if passed:
                    category_results["passed"] += 1
                    results["summary"]["passed"] += 1
                else:
                    results["summary"]["failed"] += 1

                print(f"  原文: {text}")
                print(f"  認識: {recognized}")
                print(f"  精度: {accuracy:.1f}% {status}")

                results["details"].append({
                    "category": category,
                    "original": text,
                    "recognized": recognized,
                    "accuracy": accuracy,
                    "passed": passed
                })

            except Exception as e:
                print(f"  エラー: {e}")
                results["summary"]["failed"] += 1
                results["details"].append({
                    "category": category,
                    "original": text,
                    "error": str(e),
                    "passed": False
                })

            results["summary"]["total"] += 1

        category_results["avg_accuracy"] = sum(accuracies) / len(accuracies) if accuracies else 0
        results["by_category"][category] = category_results

        print(f"\n{category}合計: {category_results['passed']}/{category_results['total']} 通過, 平均精度: {category_results['avg_accuracy']:.1f}%")

    # 最終サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    print(f"合計: {results['summary']['total']}パターン")
    print(f"合格: {results['summary']['passed']}")
    print(f"不合格: {results['summary']['failed']}")

    for cat, cat_result in results["by_category"].items():
        print(f"  {cat}: {cat_result['passed']}/{cat_result['total']} (平均精度: {cat_result['avg_accuracy']:.1f}%)")

    # 結果をJSONで保存
    with open("/tmp/stt-test-results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n詳細結果: /tmp/stt-test-results.json")

    return results


if __name__ == "__main__":
    asyncio.run(run_tests())
