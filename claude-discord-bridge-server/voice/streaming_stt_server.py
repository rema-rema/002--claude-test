#!/usr/bin/env python3
"""
Streaming STT Server - whisper_streaming を使ったリアルタイム音声認識サーバー

WebSocket経由で音声チャンクを受信し、リアルタイムで認識結果を返す
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# whisper_streaming_lib をパスに追加
sys.path.insert(0, str(Path(__file__).parent / "whisper_streaming_lib"))

# whisper_streaming をインポート
try:
    from whisper_online import FasterWhisperASR, OnlineASRProcessor
except ImportError as e:
    print(f"Error importing whisper_online: {e}")
    print("Make sure whisper_streaming_lib is cloned:")
    print("  git clone https://github.com/ufal/whisper_streaming.git whisper_streaming_lib")
    sys.exit(1)

import websockets
import numpy as np

# ログ設定
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# 設定
HOST = "127.0.0.1"
PORT = 8765
MODEL_SIZE = "large-v3-turbo"  # Kotoba-Whisperはwhisper_streamingと非互換のため戻す
LANGUAGE = "ja"
SAMPLE_RATE = 16000
DEVICE = "cuda"  # cpu or cuda
COMPUTE_TYPE = "float16"  # int8 for CPU, float16 for GPU

# バッファリング設定（チャンクが小さすぎると認識精度が下がる）
MIN_CHUNK_SAMPLES = SAMPLE_RATE // 2  # 0.5秒分 = 8000サンプル


class ConfigurableFasterWhisperASR(FasterWhisperASR):
    """設定可能なFasterWhisperASR - device/compute_typeを外部から指定"""

    def load_model(self, modelsize=None, cache_dir=None, model_dir=None):
        from faster_whisper import WhisperModel
        if model_dir is not None:
            model_size_or_path = model_dir
        elif modelsize is not None:
            model_size_or_path = modelsize
        else:
            raise ValueError("modelsize or model_dir parameter must be set")

        # 設定に基づいてデバイス・計算タイプを選択
        model = WhisperModel(model_size_or_path, device=DEVICE, compute_type=COMPUTE_TYPE, download_root=cache_dir)
        return model


# グローバル変数
asr = None
online_processor = None


def init_asr():
    """ASRモデルを初期化"""
    global asr, online_processor

    logger.info(f"Loading Whisper model: {MODEL_SIZE} (device={DEVICE}, compute={COMPUTE_TYPE})")
    asr = ConfigurableFasterWhisperASR(LANGUAGE, MODEL_SIZE)

    # Silero VADを有効化（幻聴防止）
    logger.info("Enabling Silero VAD for hallucination prevention...")
    asr.use_vad()

    logger.info("Model loaded successfully with VAD enabled")


async def handle_client(websocket):
    """クライアント接続を処理"""
    client_id = id(websocket)
    logger.info(f"Client connected: {client_id}")

    # セッションごとにOnlineASRProcessorを作成
    processor = OnlineASRProcessor(asr)

    # 確定テキストの累積（COMPLETE NOWの部分を全て保持）
    accumulated_text = ""
    # 最後に送信したテキスト（重複送信防止）
    last_sent_text = ""

    # 音声バッファ（小さなチャンクを溜めてから処理）
    audio_buffer = np.array([], dtype=np.float32)

    try:
        async for message in websocket:
            logger.debug(f"Received message type: {type(message)}, len: {len(message) if hasattr(message, '__len__') else 'N/A'}")
            if isinstance(message, bytes):
                # 音声データを受信
                # 16bit PCM mono 16kHz を想定
                audio_chunk = np.frombuffer(message, dtype=np.int16).astype(np.float32) / 32768.0

                # バッファに追加
                audio_buffer = np.concatenate([audio_buffer, audio_chunk])

                # バッファが十分に溜まったら処理
                if len(audio_buffer) < MIN_CHUNK_SAMPLES:
                    continue  # まだ溜まっていない

                # バッファを処理用に取り出し
                chunk_to_process = audio_buffer
                audio_buffer = np.array([], dtype=np.float32)

                # 音声チャンクを処理（別スレッドで実行してブロックを回避）
                def process_audio():
                    processor.insert_audio_chunk(chunk_to_process)
                    return processor.process_iter()

                output = await asyncio.to_thread(process_audio)

                if output and output[2]:  # output = (beg, end, text)
                    # whisper_streamingのprocess_iter()は確定テキスト（COMPLETE NOW）を返す
                    # これを累積していく
                    current_text = output[2]
                    if current_text != last_sent_text:
                        # 確定テキストを累積に追加
                        accumulated_text += current_text
                        result = {
                            "type": "partial",
                            "text": accumulated_text,  # 累積テキストを送信
                            "start": output[0],
                            "end": output[1]
                        }
                        await websocket.send(json.dumps(result))
                        logger.info(f"Partial: {accumulated_text}")
                        last_sent_text = current_text

            elif isinstance(message, str):
                data = json.loads(message)
                logger.info(f"Received JSON message: {data}")

                if data.get("type") == "end":
                    # 発話終了 - 残りのバッファを処理してから最終結果を取得
                    logger.info("Processing end request...")

                    # バッファに残っている音声も処理
                    if len(audio_buffer) > 0:
                        remaining_chunk = audio_buffer
                        audio_buffer = np.array([], dtype=np.float32)

                        def process_remaining():
                            processor.insert_audio_chunk(remaining_chunk)
                            return processor.process_iter()

                        remaining_output = await asyncio.to_thread(process_remaining)
                        # 残りの処理結果も累積に追加
                        if remaining_output and remaining_output[2]:
                            accumulated_text += remaining_output[2]

                    final_output = await asyncio.to_thread(processor.finish)

                    # 最終テキストを構築（累積テキスト + finish()の未確定部分）
                    final_text = accumulated_text
                    if final_output and final_output[2]:
                        final_text += final_output[2]

                    if final_text:
                        result = {
                            "type": "final",
                            "text": final_text,
                            "start": final_output[0] if final_output else 0,
                            "end": final_output[1] if final_output else 0
                        }
                        await websocket.send(json.dumps(result))
                        logger.info(f"Final: {final_text}")

                    # プロセッサをリセット
                    processor = OnlineASRProcessor(asr)
                    accumulated_text = ""
                    last_sent_text = ""
                    audio_buffer = np.array([], dtype=np.float32)
                    logger.info("Processor reset for new utterance")

                elif data.get("type") == "reset":
                    # 強制リセット
                    processor = OnlineASRProcessor(asr)
                    accumulated_text = ""
                    last_sent_text = ""
                    audio_buffer = np.array([], dtype=np.float32)
                    logger.info("Processor force reset")

    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
    finally:
        logger.info(f"Client session ended: {client_id}")


async def main():
    """メインサーバー起動"""
    init_asr()

    logger.info(f"Starting Streaming STT Server on ws://{HOST}:{PORT}")

    async with websockets.serve(handle_client, HOST, PORT):
        logger.info("Server ready. Waiting for connections...")
        await asyncio.Future()  # 永久に待機


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown")
