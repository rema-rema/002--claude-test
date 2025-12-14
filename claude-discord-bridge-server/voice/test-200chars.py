#!/usr/bin/env python3
"""
200文字テストスクリプト - 長文チャンク分割のテスト
"""

import asyncio
import json
import requests
import websockets
import sys

# 設定
VOICEVOX_URL = "http://localhost:50021"
STT_WS_URL = "ws://127.0.0.1:8765"
SPEAKER_ID = 3  # ずんだもん（ノーマル）

# 200文字テスト用テキスト（約200文字）
TEST_TEXT_200 = """来週の月曜日に開催される全体会議では新しいプロジェクトについて説明が行われる予定です。参加者は事前に資料を確認しておいてください。質問がある場合は会議前にメールで送ってください。会議の後にはチームごとの打ち合わせも予定されています。"""

# 150文字バージョン
TEST_TEXT_150 = """今日は天気が良いので午後から公園に散歩に行って、そのあとカフェでコーヒーを飲もうと思っています。最近忙しくてリフレッシュが必要だと感じていたので、ちょうど良い機会です。"""

# 100文字バージョン
TEST_TEXT_100 = """このシステムは音声認識と音声合成を組み合わせて、自然な対話を実現することを目的としています。"""


def generate_audio(text: str) -> bytes:
    """VOICEVOXでテキストから音声を生成"""
    print(f"[TTS] 音声合成中...")

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


async def test_stt(audio_pcm: bytes, timeout: float = 60.0) -> str:
    """STTサーバーに音声を送信して認識結果を取得（複数finalを蓄積）"""
    final_texts = []  # 複数のfinalを蓄積
    partials = []

    print(f"[STT] WebSocket接続中... ({STT_WS_URL})")

    try:
        async with websockets.connect(STT_WS_URL) as ws:
            print(f"[STT] 接続成功")
            print(f"[STT] 音声データ送信中... ({len(audio_pcm)} bytes)")

            # 音声データを送信（チャンク分割）
            chunk_size = 3200  # 0.1秒分 (16000Hz * 2bytes * 0.1s)
            total_chunks = len(audio_pcm) // chunk_size + 1

            for i in range(0, len(audio_pcm), chunk_size):
                chunk = audio_pcm[i:i+chunk_size]
                await ws.send(chunk)
                if (i // chunk_size) % 20 == 0:
                    print(f"[STT] 送信中: {i // chunk_size + 1}/{total_chunks}")
                await asyncio.sleep(0.05)  # 送信間隔

            print(f"[STT] 音声送信完了、終了通知送信...")
            # 発話終了を通知
            await ws.send(json.dumps({"type": "end"}))

            print(f"[STT] 結果待機中... (タイムアウト: {timeout}秒)")

            # 結果を待機（複数finalを蓄積）
            # 音声データ送信完了後、少し待ってから結果収集を終了
            last_activity = asyncio.get_event_loop().time()

            try:
                while True:
                    try:
                        # 3秒間新しいメッセージがなければ終了
                        message = await asyncio.wait_for(ws.recv(), timeout=3.0)
                        last_activity = asyncio.get_event_loop().time()

                        data = json.loads(message)
                        msg_type = data.get("type", "")

                        if msg_type == "speech_start":
                            print(f"[STT] 発話開始検出")
                        elif msg_type == "partial":
                            partial_text = data.get("text", "")
                            partials.append(partial_text)
                            print(f"[STT] Partial ({len(partial_text)}文字): {partial_text[:50]}...")
                        elif msg_type == "final":
                            final_text = data.get("text", "")
                            final_texts.append(final_text)
                            print(f"[STT] Final #{len(final_texts)}: {final_text}")

                    except asyncio.TimeoutError:
                        # 3秒間メッセージなし = 全ての発話処理完了
                        print(f"[STT] 3秒間メッセージなし、収集完了")
                        break

            except websockets.exceptions.ConnectionClosed as e:
                print(f"[STT] WebSocket切断: {e}")

    except Exception as e:
        print(f"[STT] エラー: {e}")
        import traceback
        traceback.print_exc()

    # 複数のfinalを結合
    combined_text = "".join(final_texts)
    print(f"[STT] 結合結果 ({len(final_texts)}個のfinal): {combined_text}")
    return combined_text


def calculate_accuracy(original: str, recognized: str) -> float:
    """文字単位の認識精度を計算（編集距離ベース）"""
    if not original:
        return 0.0
    if not recognized:
        return 0.0

    # 正規化
    original = original.replace(" ", "").replace("　", "")
    recognized = recognized.replace(" ", "").replace("　", "")

    # 一致する文字数をカウント（順序を考慮しない）
    orig_chars = list(original)
    recog_chars = list(recognized)

    matches = 0
    for c in orig_chars:
        if c in recog_chars:
            matches += 1
            recog_chars.remove(c)

    return matches / len(original) * 100


async def run_test(test_name: str, text: str):
    """テストを実行"""
    print(f"\n{'='*60}")
    print(f"テスト: {test_name} ({len(text)}文字)")
    print(f"{'='*60}")
    print(f"原文: {text}")
    print(f"-"*60)

    try:
        # 音声生成
        wav_data = generate_audio(text)
        pcm_data = wav_to_pcm16(wav_data)
        duration = len(pcm_data) / (16000 * 2)  # 16kHz, 16bit mono
        print(f"[TTS] 音声生成完了: {len(pcm_data)} bytes ({duration:.1f}秒)")

        # STT認識
        recognized = await asyncio.wait_for(test_stt(pcm_data), timeout=120.0)

        # 結果表示
        print(f"\n{'='*60}")
        print(f"結果")
        print(f"{'='*60}")
        print(f"原文 ({len(text)}文字):")
        print(f"  {text}")
        print(f"\n認識 ({len(recognized)}文字):")
        print(f"  {recognized}")

        accuracy = calculate_accuracy(text, recognized)
        status = "✅ 成功" if accuracy >= 70 else "❌ 失敗"
        print(f"\n精度: {accuracy:.1f}% {status}")

        return accuracy >= 70

    except asyncio.TimeoutError:
        print(f"❌ タイムアウト (120秒)")
        return False
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """メイン処理"""
    print("="*60)
    print("200文字チャンク分割テスト")
    print("="*60)

    # コマンドライン引数でテストを選択
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "100":
            await run_test("100文字テスト", TEST_TEXT_100)
        elif arg == "150":
            await run_test("150文字テスト", TEST_TEXT_150)
        elif arg == "200":
            await run_test("200文字テスト", TEST_TEXT_200)
        elif arg == "all":
            await run_test("100文字テスト", TEST_TEXT_100)
            await run_test("150文字テスト", TEST_TEXT_150)
            await run_test("200文字テスト", TEST_TEXT_200)
        else:
            # カスタムテキスト
            await run_test(f"カスタム ({len(arg)}文字)", arg)
    else:
        # デフォルトは200文字テスト
        await run_test("200文字テスト", TEST_TEXT_200)


if __name__ == "__main__":
    asyncio.run(main())
